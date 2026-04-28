"""
Channel integration endpoints
/v1/channels/*
"""

from fastapi import APIRouter, HTTPException, status, Header

router = APIRouter()


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


@router.get("/instagram/connect")
async def instagram_oauth():
    """
    Initiate Instagram OAuth flow
    """
    # TODO: Phase 5 — redirect to Meta OAuth consent screen
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Instagram OAuth endpoint coming in Phase 5"
    )


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

@router.get("/gmail/connect")
async def gmail_oauth():
    """
    Initiate Gmail OAuth flow
    """
    # TODO: Phase 5 — redirect to Google OAuth consent screen
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Gmail OAuth endpoint coming in Phase 5"
    )


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

@router.get("/connected")
async def list_connected_channels():
    """
    List all connected channels for current user
    """
    # TODO: Phase 5 — fetch connected channels from DB
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="List channels endpoint coming in Phase 5"
    )


@router.post("/{channel}/disconnect")
async def disconnect_channel(channel: str):
    """
    Disconnect a channel (revoke tokens, delete credentials)
    """
    # TODO: Phase 5 — delete channel tokens, revoke OAuth grants
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Disconnect channel endpoint coming in Phase 5"
    )
