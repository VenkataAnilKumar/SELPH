"""
Sender tier model for VIP Override / Relationship Tiers.
"""

from sqlalchemy import Column, String, Text, ForeignKey, Integer, DateTime, Index, UniqueConstraint
from app.models.base import BaseModel


class SenderTier(BaseModel):
    """Per-sender routing tier override for a user and platform."""

    __tablename__ = "sender_tiers"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    sender_id = Column(String(200), nullable=False)
    platform = Column(String(50), nullable=False)
    tier = Column(Integer, nullable=False, default=2)  # 0=VIP, 1=Priority, 2=Standard, 3=Cold
    tier_label = Column(String(100), nullable=True)
    set_by = Column(String(20), nullable=False, default="user")
    notes = Column(Text, nullable=True)
    last_interaction_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "sender_id", "platform", name="uq_sender_tiers_user_sender_platform"),
        Index("ix_sender_tiers_user_platform_tier", "user_id", "platform", "tier"),
    )
