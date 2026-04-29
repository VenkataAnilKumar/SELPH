"""Twin certificate metadata for verification."""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from app.models.base import BaseModel


class TwinCertificate(BaseModel):
    __tablename__ = "twin_certificates"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    twin_public_id = Column(String(50), nullable=False, unique=True, index=True)
    public_key = Column(Text, nullable=False)
    private_key_ref = Column(String(200), nullable=False)
    issued_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoke_reason = Column(String(200), nullable=True)
