"""Proactive suggestions generated from inbox signals."""

from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Index
from app.models.base import BaseModel


class ProactiveSuggestion(BaseModel):
    __tablename__ = "proactive_suggestions"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    suggestion_type = Column(String(50), nullable=False)
    contact_id = Column(String(200), nullable=True)
    signal_summary = Column(Text, nullable=False)
    draft_message = Column(Text, nullable=False)
    urgency_score = Column(Float, nullable=False, default=0.5)
    value_score = Column(Float, nullable=False, default=0.5)
    status = Column(String(50), nullable=False, default="pending")
    snoozed_until = Column(DateTime, nullable=True)
    acted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_proactive_suggestions_user_status", "user_id", "status"),
    )
