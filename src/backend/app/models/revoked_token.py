"""
Revoked token model — server-side logout / token revocation
"""

from sqlalchemy import Column, String, DateTime, Index
from app.models.base import BaseModel


class RevokedToken(BaseModel):
    """A token that must no longer be accepted, kept until it would have expired anyway."""
    __tablename__ = "revoked_tokens"

    token_key = Column(String, nullable=False, unique=True, index=True)  # jti or sha256 of token
    user_id = Column(String, nullable=False, index=True)
    token_type = Column(String, nullable=False, default="access")  # access | refresh
    expires_at = Column(DateTime, nullable=False)

    __table_args__ = (Index("ix_revoked_tokens_expires_at", "expires_at"),)
