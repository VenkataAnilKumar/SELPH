"""
Pydantic schemas for channel credential endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ChannelConnectRequest(BaseModel):
    """Connect request payload for a channel."""
    credential_value: Optional[str] = None
    scope: Optional[str] = None


class ChannelConnectResponse(BaseModel):
    """Connection result payload."""
    channel: str
    connected: bool


class ConnectedChannelResponse(BaseModel):
    """Channel connection state for dashboard rendering."""
    channel: str
    connected: bool
    scope: Optional[str] = None
    updated_at: datetime


class OAuthUrlResponse(BaseModel):
    """OAuth authorization URL returned to the client for redirect."""
    channel: str
    authorization_url: str


class OAuthCallbackResponse(BaseModel):
    """Result of OAuth code exchange."""
    channel: str
    connected: bool
    email: Optional[str] = None     # Gmail: authenticated Google account email
    page_count: Optional[int] = None  # Instagram: number of pages connected


class WebhookAckResponse(BaseModel):
    """Standard acknowledgment for webhook receipt."""
    received: bool
    queued: int = 0   # number of messages enqueued for processing


class SendReplyRequest(BaseModel):
    """Request body for manually triggering a reply send."""
    draft_id: str


class SendReplyResponse(BaseModel):
    """Result of a channel reply send operation."""
    draft_id: str
    sent: bool
    channel: Optional[str] = None
