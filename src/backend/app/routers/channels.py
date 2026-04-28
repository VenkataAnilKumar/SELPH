"""
Channel integration endpoints — Phase 5 implementation
/v1/channels/*

Provides:
  - OAuth authorization URL generation (Instagram + Gmail)
  - OAuth callback handlers (code exchange + credential storage)
  - Meta webhook verification (GET) and DM ingestion (POST)
  - Gmail Pub/Sub webhook ingestion
  - Channel connect/disconnect management
  - Manual draft reply send endpoint
"""

import json
import hmac
import logging
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Request, status, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import User, ChannelCredential
from app.channels.instagram import InstagramAdapter
from app.channels.gmail import GmailAdapter
from app.config import get_settings
from app.security import create_access_token, verify_token
from app.services.channel import ChannelService
from app.schemas.channels import (
    ChannelConnectRequest,
    ChannelConnectResponse,
    ConnectedChannelResponse,
    OAuthUrlResponse,
    OAuthCallbackResponse,
    WebhookAckResponse,
    SendReplyRequest,
    SendReplyResponse,
)

router = APIRouter(tags=["Channels"])
logger = logging.getLogger(__name__)

SUPPORTED_CHANNELS = {"instagram", "gmail"}


def _validate_channel(channel: str) -> str:
    normalized = channel.strip().lower()
    if normalized not in SUPPORTED_CHANNELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported channel '{channel}'. Supported: {', '.join(SUPPORTED_CHANNELS)}",
        )
    return normalized


def _build_oauth_state(user_id: str) -> str:
    """Create a short-lived signed OAuth state token bound to a user."""
    token, _ = create_access_token(
        data={"sub": user_id, "purpose": "channel_oauth_state"},
        expires_delta=timedelta(minutes=10),
    )
    return token


def _resolve_oauth_state(state: str) -> str:
    """Resolve and validate OAuth state, returning user_id if valid."""
    payload = verify_token(state)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state",
        )

    if payload.get("purpose") != "channel_oauth_state":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state purpose",
        )

    user_id = payload.get("sub", "")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state user",
        )
    return user_id


# ============================================================================
# INSTAGRAM — OAuth
# ============================================================================

@router.get("/instagram/oauth", response_model=OAuthUrlResponse)
async def instagram_oauth_url(
    current_user: User = Depends(get_current_user),
):
    """
    Generate the Meta OAuth authorization URL.
    The client redirects the user's browser to this URL to begin Instagram connection.
    """
    settings = get_settings()
    if not settings.meta_app_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Instagram integration is not configured on this server",
        )
    adapter = InstagramAdapter()
    state_token = _build_oauth_state(current_user.id)
    url = adapter.build_authorization_url(user_id=state_token)
    return OAuthUrlResponse(channel="instagram", authorization_url=url)


@router.get("/instagram/callback", response_model=OAuthCallbackResponse)
async def instagram_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    Instagram OAuth callback.
    Meta redirects here with ?code=...&state=<user_id> after the user grants access.
    Exchanges the code for tokens and stores credentials.
    """
    user_id = _resolve_oauth_state(state)

    adapter = InstagramAdapter()
    try:
        token_data = adapter.exchange_code_for_token(code)
    except Exception as exc:
        logger.error("Instagram token exchange failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to exchange Instagram authorization code. Please try again.",
        )

    pages = token_data.get("pages", [])
    if not pages:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "No Instagram Business Pages found. "
                "Please connect a Business Account and try again."
            ),
        )

    first_page = pages[0]
    page_access_token = first_page.get("access_token", token_data["access_token"])
    scope_data = json.dumps({"page_id": first_page.get("id"), "page_name": first_page.get("name")})

    ChannelService.upsert_credential(
        db=db,
        user_id=user_id,
        channel="instagram_dm",
        credential_value=page_access_token,
        scope=scope_data,
    )

    logger.info("Instagram connected for user=%s pages=%d", user_id, len(pages))
    return OAuthCallbackResponse(
        channel="instagram",
        connected=True,
        page_count=len(pages),
    )


# ============================================================================
# INSTAGRAM — Webhook (Meta Graph API)
# ============================================================================

@router.get("/instagram/webhook")
async def instagram_webhook_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    Meta webhook verification challenge.
    Meta sends a GET request with hub.mode=subscribe when the webhook is first configured.
    We must echo back hub.challenge if hub.verify_token matches META_VERIFY_TOKEN.
    """
    if not hub_mode or not hub_verify_token or not hub_challenge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required hub.mode, hub.verify_token, or hub.challenge parameters",
        )

    adapter = InstagramAdapter()
    try:
        challenge = adapter.verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    except ValueError as exc:
        logger.warning("Instagram webhook verification failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(challenge)


@router.post("/instagram/webhook", response_model=WebhookAckResponse)
async def instagram_webhook_receive(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Instagram DM webhook receiver.
    Meta posts DM events here; we verify the signature, parse the payload,
    find the destination user, create Message records, and enqueue draft generation.
    """
    settings = get_settings()

    body_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if settings.meta_app_secret:
        adapter = InstagramAdapter()
        if not adapter.verify_signature(body_bytes, signature):
            logger.warning("Instagram webhook signature verification failed")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Webhook signature verification failed",
            )

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in webhook body",
        )

    adapter = InstagramAdapter()
    normalized_messages = adapter.parse_webhook_event(payload)

    if not normalized_messages:
        return WebhookAckResponse(received=True, queued=0)

    queued = 0
    page_user_cache: dict[str, str | None] = {}
    for nm in normalized_messages:
        page_id = nm.channel_metadata.get("page_id")
        if not page_id:
            user_id = None
        elif page_id in page_user_cache:
            user_id = page_user_cache[page_id]
        else:
            user_id = ChannelService.find_user_by_instagram_page(db, page_id)
            page_user_cache[page_id] = user_id

        if not user_id:
            logger.warning(
                "Instagram webhook: no user found for page_id=%s — skipping message",
                page_id,
            )
            continue

        _enqueue_message_ingestion(
            user_id=user_id,
            channel="instagram_dm",
            sender_id=nm.sender_id,
            sender_name=nm.sender_name,
            content=nm.content,
            channel_metadata=nm.channel_metadata,
        )
        queued += 1

    return WebhookAckResponse(received=True, queued=queued)


# ============================================================================
# GMAIL — OAuth
# ============================================================================

@router.get("/gmail/oauth", response_model=OAuthUrlResponse)
async def gmail_oauth_url(
    current_user: User = Depends(get_current_user),
):
    """
    Generate the Google OAuth authorization URL.
    The client redirects the user's browser here to begin Gmail connection.
    """
    settings = get_settings()
    if not settings.google_oauth_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gmail integration is not configured on this server",
        )
    adapter = GmailAdapter()
    state_token = _build_oauth_state(current_user.id)
    url = adapter.build_authorization_url(user_id=state_token)
    return OAuthUrlResponse(channel="gmail", authorization_url=url)


@router.get("/gmail/callback", response_model=OAuthCallbackResponse)
async def gmail_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    Gmail OAuth callback.
    Google redirects here with ?code=...&state=<user_id> after consent.
    Exchanges the code for tokens, sets up Pub/Sub watch, and stores credentials.
    """
    user_id = _resolve_oauth_state(state)

    adapter = GmailAdapter()
    try:
        token_data = adapter.exchange_code_for_token(code)
    except Exception as exc:
        logger.error("Gmail token exchange failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to exchange Gmail authorization code. Please try again.",
        )

    email = token_data.get("email", "")

    settings = get_settings()
    if settings.google_pubsub_topic:
        try:
            adapter.setup_push_notifications(token_data["access_token"])
        except Exception as exc:
            logger.warning("Gmail watch() setup failed (non-fatal): %s", exc)

    credential_value = json.dumps({
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token", ""),
        "email": email,
    })
    scope_data = json.dumps({"email": email, "scope": token_data.get("scope", "")})

    ChannelService.upsert_credential(
        db=db,
        user_id=user_id,
        channel="gmail",
        credential_value=credential_value,
        scope=scope_data,
    )

    logger.info("Gmail connected for user=%s email=%s", user_id, email)
    return OAuthCallbackResponse(
        channel="gmail",
        connected=True,
        email=email,
    )


# ============================================================================
# GMAIL — Webhook (Google Cloud Pub/Sub push)
# ============================================================================

@router.post("/gmail/webhook", response_model=WebhookAckResponse)
async def gmail_webhook_receive(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Gmail Pub/Sub push notification receiver.
    Google sends a POST with a base64-encoded notification when new emails arrive.
    We decode it, fetch the new message via Gmail History API, and enqueue processing.
    """
    settings = get_settings()
    if settings.google_webhook_secret:
        received_secret = request.headers.get("X-Webhook-Token", "")
        if not hmac.compare_digest(received_secret, settings.google_webhook_secret):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Gmail webhook token",
            )

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in Pub/Sub notification body",
        )

    adapter = GmailAdapter()
    notification = adapter.parse_pubsub_notification(payload)

    if not notification:
        return WebhookAckResponse(received=True, queued=0)

    email_address = notification.get("emailAddress")
    history_id = str(notification.get("historyId", ""))

    if not email_address or not history_id:
        logger.warning("Gmail Pub/Sub: missing emailAddress or historyId in notification")
        return WebhookAckResponse(received=True, queued=0)

    user_id = ChannelService.find_user_by_gmail_address(db, email_address)
    if not user_id:
        logger.warning("Gmail webhook: no user found for email=%s", email_address)
        return WebhookAckResponse(received=True, queued=0)

    cred = ChannelService.get_credential(db, user_id, "gmail")
    if not cred:
        logger.warning("Gmail webhook: no active credential for user=%s", user_id)
        return WebhookAckResponse(received=True, queued=0)

    try:
        cred_data = json.loads(cred.credential_value)
        access_token = cred_data.get("access_token", cred.credential_value)
    except (json.JSONDecodeError, TypeError):
        access_token = cred.credential_value

    normalized_messages = adapter.fetch_new_messages(
        access_token=access_token,
        history_id=history_id,
    )

    queued = 0
    for nm in normalized_messages:
        _enqueue_message_ingestion(
            user_id=user_id,
            channel="gmail",
            sender_id=nm.sender_id,
            sender_name=nm.sender_name,
            content=nm.content,
            channel_metadata=nm.channel_metadata,
        )
        queued += 1

    return WebhookAckResponse(received=True, queued=queued)


# ============================================================================
# CHANNEL MANAGEMENT
# ============================================================================

@router.get("/connected", response_model=list[ConnectedChannelResponse])
async def list_connected_channels(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all connected channels for the current user."""
    credentials = (
        db.query(ChannelCredential)
        .filter(ChannelCredential.user_id == current_user.id)
        .all()
    )
    return [
        ConnectedChannelResponse(
            channel=cred.channel,
            connected=cred.is_active,
            scope=cred.scope,
            updated_at=cred.updated_at,
        )
        for cred in credentials
    ]


@router.post("/{channel}/disconnect")
async def disconnect_channel(
    channel: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect a channel — marks credential inactive."""
    normalized = _validate_channel(channel)

    credential = (
        db.query(ChannelCredential)
        .filter(
            ChannelCredential.user_id == current_user.id,
            ChannelCredential.channel.in_([normalized, f"{normalized}_dm"]),
            ChannelCredential.is_active.is_(True),
        )
        .first()
    )

    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{normalized} channel is not connected",
        )

    credential.is_active = False
    db.commit()
    return {"channel": normalized, "connected": False}


@router.post("/send-reply", response_model=SendReplyResponse)
async def send_channel_reply(
    request: SendReplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send an approved draft reply through its originating channel.
    Available for manual triggering or retry after a send failure.
    """
    from app.models import Draft, Message

    draft = db.query(Draft).filter(
        Draft.id == request.draft_id,
        Draft.user_id == current_user.id,
    ).first()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Draft {request.draft_id} not found",
        )

    if draft.status not in ("approved", "edited", "send_failed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Draft status '{draft.status}' is not eligible for sending",
        )

    message = db.query(Message).filter(Message.id == draft.message_id).first()
    channel = message.channel if message else None

    sent = ChannelService.send_draft_reply(db, request.draft_id)
    return SendReplyResponse(draft_id=request.draft_id, sent=sent, channel=channel)


# ============================================================================
# Legacy connect endpoints (backward compatibility)
# ============================================================================

@router.post("/instagram/connect", response_model=ChannelConnectResponse)
async def connect_instagram_legacy(
    request: ChannelConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Legacy credential storage endpoint.
    Prefer /instagram/oauth + /instagram/callback for real OAuth flows.
    """
    token_value = request.credential_value or "instagram_connected"
    ChannelService.upsert_credential(
        db=db,
        user_id=current_user.id,
        channel="instagram_dm",
        credential_value=token_value,
        scope=request.scope,
    )
    return ChannelConnectResponse(channel="instagram", connected=True)


@router.post("/gmail/connect", response_model=ChannelConnectResponse)
async def connect_gmail_legacy(
    request: ChannelConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Legacy credential storage endpoint.
    Prefer /gmail/oauth + /gmail/callback for real OAuth flows.
    """
    token_value = request.credential_value or "gmail_connected"
    ChannelService.upsert_credential(
        db=db,
        user_id=current_user.id,
        channel="gmail",
        credential_value=token_value,
        scope=request.scope,
    )
    return ChannelConnectResponse(channel="gmail", connected=True)


# ============================================================================
# Helpers
# ============================================================================

def _enqueue_message_ingestion(
    user_id: str,
    channel: str,
    sender_id: str,
    sender_name: str,
    content: str,
    channel_metadata: dict,
) -> None:
    """
    Enqueue the process_incoming_message Celery task.
    Import is deferred to avoid circular imports at module load time.
    """
    from app.tasks.message_processing import process_incoming_message
    process_incoming_message.delay(
        user_id=user_id,
        channel=channel,
        sender_id=sender_id,
        sender_name=sender_name,
        content=content,
        channel_metadata=channel_metadata,
    )
