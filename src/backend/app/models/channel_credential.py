"""
ChannelCredential model — OAuth tokens and API credentials
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import BaseModel


class ChannelCredential(BaseModel):
    """OAuth tokens and API credentials for channels"""
    __tablename__ = "channel_credentials"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    channel = Column(String, nullable=False)  # instagram, gmail, twitter, whatsapp, slack
    credential_type = Column(String, default="oauth_token", nullable=False)  # oauth_token, api_key, etc.
    
    # Credential value (should be encrypted in production)
    # In production, use encrypted column or store in vault
    credential_value = Column(String, nullable=False)
    
    # Metadata
    scope = Column(String, nullable=True)  # Permissions: e.g., "messages.read messages.write"
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="channel_credentials")

    __table_args__ = (
        Index("ix_channel_credentials_user_channel", "user_id", "channel"),
    )
