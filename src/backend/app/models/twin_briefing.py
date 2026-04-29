"""
TwinBriefing model - time-scoped prompt context for Phase 9.
"""

from sqlalchemy import Column, String, Text, ForeignKey, Boolean, DateTime, Integer
from app.models.base import BaseModel


class TwinBriefing(BaseModel):
    """Stores temporary briefing facts/instructions injected into twin prompts."""

    __tablename__ = "twin_briefings"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    briefing_type = Column(String(50), nullable=False)
    topic = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(Integer, nullable=False, default=5)
    is_active = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime, nullable=True)
    max_uses = Column(Integer, nullable=True)
    use_count = Column(Integer, nullable=False, default=0)
    cleared_at = Column(DateTime, nullable=True)
