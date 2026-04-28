"""
Channel integration endpoints
/v1/channels/*
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import User, ChannelCredential
from app.schemas.channels import (
    ChannelConnectRequest,
    ChannelConnectResponse,
    ConnectedChannelResponse,
)

router = APIRouter(tags=["Channels"])


SUPPORTED_CHANNELS = {"instagram", "gmail"}


def _validate_channel(channel: str) -> str:
    normalized = channel.strip().lower()
    if normalized not in SUPPORTED_CHANNELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported channel '{channel}'. Supported: instagram, gmail",
        )
    return normalized


# ============================================================================
# INSTAGRAM DMs
# ============================================================================

@router.get("/instagram/webhook")
async def instagram_webhook_verify(hub_challenge: str = None):
    """
    Instagram webhook verification (GET)
    """
    # TODO: Phase 5 — verify Meta webhook challenge
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Instagram verification endpoint coming in Phase 5"
    )


@router.post("/instagram/webhook")
async def instagram_webhook(body: dict):
    """
    Instagram webhook receiver (POST)
    Receives DM events from Meta Graph API
    """
    # TODO: Phase 5 — parse Meta webhook, enqueue draft generation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Instagram webhook endpoint coming in Phase 5"
    )


@router.post("/instagram/connect", response_model=ChannelConnectResponse)
async def connect_instagram(
    request: ChannelConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initiate Instagram OAuth flow
    """
    existing = db.query(ChannelCredential).filter(
        ChannelCredential.user_id == current_user.id,
        ChannelCredential.channel == "instagram",
    ).first()

    token_value = request.credential_value or "instagram_connected"

    if existing:
        existing.credential_value = token_value
        existing.scope = request.scope
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return ChannelConnectResponse(channel="instagram", connected=True)

    credential = ChannelCredential(
        user_id=current_user.id,
        channel="instagram",
        credential_type="oauth_token",
        credential_value=token_value,
        scope=request.scope,
        is_active=True,
    )
    db.add(credential)
    db.commit()

    return ChannelConnectResponse(channel="instagram", connected=True)


@router.get("/instagram/callback")
async def instagram_callback(code: str = None, state: str = None):
    """
    Instagram OAuth callback
    """
    # TODO: Phase 5 — exchange code for access token, store in DB
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Instagram callback endpoint coming in Phase 5"
    )


# ============================================================================
# GMAIL
# ============================================================================

@router.post("/gmail/connect", response_model=ChannelConnectResponse)
async def connect_gmail(
    request: ChannelConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initiate Gmail OAuth flow
    """
    existing = db.query(ChannelCredential).filter(
        ChannelCredential.user_id == current_user.id,
        ChannelCredential.channel == "gmail",
    ).first()

    token_value = request.credential_value or "gmail_connected"

    if existing:
        existing.credential_value = token_value
        existing.scope = request.scope
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return ChannelConnectResponse(channel="gmail", connected=True)

    credential = ChannelCredential(
        user_id=current_user.id,
        channel="gmail",
        credential_type="oauth_token",
        credential_value=token_value,
        scope=request.scope,
        is_active=True,
    )
    db.add(credential)
    db.commit()

    return ChannelConnectResponse(channel="gmail", connected=True)


@router.get("/gmail/callback")
async def gmail_callback(code: str = None, state: str = None):
    """
    Gmail OAuth callback
    """
    # TODO: Phase 5 — exchange code for access token, set up Pub/Sub watch
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Gmail callback endpoint coming in Phase 5"
    )


@router.post("/gmail/webhook")
async def gmail_webhook(body: dict):
    """
    Gmail Pub/Sub webhook receiver
    Receives email notifications from Google Cloud Pub/Sub
    """
    # TODO: Phase 5 — parse Pub/Sub message, fetch email, enqueue draft
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Gmail webhook endpoint coming in Phase 5"
    )


# ============================================================================
# CHANNEL MANAGEMENT
# ============================================================================

@router.get("/connected", response_model=list[ConnectedChannelResponse])
async def list_connected_channels(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all connected channels for current user
    """
    credentials = db.query(ChannelCredential).filter(
        ChannelCredential.user_id == current_user.id,
    ).all()

    return [
        ConnectedChannelResponse(
            channel=credential.channel,
            connected=credential.is_active,
            scope=credential.scope,
            updated_at=credential.updated_at,
        )
        for credential in credentials
    ]


@router.post("/{channel}/disconnect")
async def disconnect_channel(
    channel: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Disconnect a channel (revoke tokens, delete credentials)
    """
    normalized = _validate_channel(channel)

    credential = db.query(ChannelCredential).filter(
        ChannelCredential.user_id == current_user.id,
        ChannelCredential.channel == normalized,
        ChannelCredential.is_active.is_(True),
    ).first()

    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{normalized} channel is not connected",
        )

    credential.is_active = False
    db.commit()

    return {"channel": normalized, "connected": False}
