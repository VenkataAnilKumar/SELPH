"""
ReferralInvite model - tracks creator referral invites and rewards
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ReferralInvite(BaseModel):
    """Referral invite sent by a creator to another creator."""
    __tablename__ = "referral_invites"

    referrer_user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    invitee_user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    invitee_email = Column(String, nullable=False, index=True)
    referral_code = Column(String, nullable=False, unique=True, index=True)
    status = Column(String, nullable=False, default="pending")  # pending | accepted
    reward_status = Column(String, nullable=False, default="unclaimed")  # unclaimed | granted
    accepted_at = Column(DateTime, nullable=True)

    referrer = relationship("User", foreign_keys=[referrer_user_id])
    invitee = relationship("User", foreign_keys=[invitee_user_id])

    __table_args__ = (
        Index("ix_referral_invites_referrer_status", "referrer_user_id", "status"),
    )
