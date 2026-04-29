"""Crisis and surge activation events."""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from app.models.base import BaseModel


class SurgeEvent(BaseModel):
    __tablename__ = "surge_events"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    trigger_type = Column(String(50), nullable=False)
    trigger_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    baseline_rate = Column(Float, nullable=True)
    peak_rate = Column(Float, nullable=True)
    mode_activated = Column(String(50), nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolution_type = Column(String(50), nullable=True)

    __table_args__ = (
        Index("ix_surge_events_user_resolved", "user_id", "resolved_at"),
    )
