"""
ChannelCredential model — OAuth tokens and API credentials
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator
from app.crypto import decrypt_secret, encrypt_secret
from app.models.base import BaseModel


class EncryptedString(TypeDecorator):
    """String column encrypted at rest (Fernet). Legacy plaintext values are read transparently."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return encrypt_secret(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return decrypt_secret(value) if value is not None else None


class ChannelCredential(BaseModel):
    """OAuth tokens and API credentials for channels"""
    __tablename__ = "channel_credentials"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    channel = Column(String, nullable=False)  # instagram, gmail, twitter, whatsapp, slack
    credential_type = Column(String, default="oauth_token", nullable=False)  # oauth_token, api_key, etc.
    
    # OAuth token / JSON token blob, encrypted at rest (see app/crypto.py)
    credential_value = Column(EncryptedString, nullable=False)
    
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
