"""
Consent model — privacy and regulatory consents
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import BaseModel


class Consent(BaseModel):
    """User consents for privacy regulations"""
    __tablename__ = "consents"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    consent_type = Column(String, nullable=False)  # data_processing, marketing, analytics, etc.
    granted = Column(Boolean, default=False, nullable=False)
    
    # Dates
    granted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="consents")

    __table_args__ = (
        Index("ix_consents_user_id_type", "user_id", "consent_type"),
    )
