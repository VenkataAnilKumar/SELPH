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
