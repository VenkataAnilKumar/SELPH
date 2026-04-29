"""Per-user proactive twin preferences."""

from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey
from app.models.base import BaseModel


class ProactivePreference(BaseModel):
    __tablename__ = "proactive_preferences"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    enabled = Column(Boolean, nullable=False, default=True)
    enabled_types = Column(JSON, nullable=False, default=lambda: ["cold_relationship", "open_thread", "deal_signal", "follow_up"])
    cold_threshold_days = Column(Integer, nullable=False, default=14)
    open_thread_hours = Column(Integer, nullable=False, default=48)
    max_suggestions_per_day = Column(Integer, nullable=False, default=5)
