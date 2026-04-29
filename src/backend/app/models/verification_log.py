"""Public verification attempts audit trail."""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Index
from app.models.base import BaseModel


class VerificationLog(BaseModel):
    __tablename__ = "verification_logs"

    certificate_id = Column(String, ForeignKey("twin_certificates.id"), nullable=True, index=True)
    twin_public_id = Column(String(50), nullable=False, index=True)
    message_hash = Column(String(200), nullable=False)
    valid = Column(Boolean, nullable=False, default=False)
    reason = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_verification_logs_twin_verified", "twin_public_id", "verified_at"),
    )
