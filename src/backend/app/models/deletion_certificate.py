"""Deletion certificate: proof that a user's data was erased, without keeping that data."""

from sqlalchemy import Column, String, DateTime, JSON, Text
from app.models.base import BaseModel


class DeletionCertificate(BaseModel):
    __tablename__ = "deletion_certificates"

    # sha256("selph-erasure:" + user_id + ":" + certificate id): lets the former user prove the
    # certificate is theirs (they know their user id) while storing nothing that identifies them.
    subject_hash = Column(String(64), nullable=False, index=True)
    completed_at = Column(DateTime, nullable=False)
    summary = Column(JSON, nullable=False)  # {"tables": {name: rows}, "notes": [...]}
    signature = Column(Text, nullable=False)  # HMAC over the fields above
