"""
Pydantic schemas for referral endpoints
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime


class ReferralInviteRequest(BaseModel):
    """Request payload to send a referral invite."""

    invitee_email: EmailStr


class ReferralInviteResponse(BaseModel):
    """Referral invite details."""

    id: str
    referral_code: str
    invitee_email: str
    status: str
    reward_status: str
    created_at: datetime


class ReferralAcceptRequest(BaseModel):
    """Request payload to accept a referral invite."""

    referral_code: str


class ReferralSummaryResponse(BaseModel):
    """Current user's referral performance summary."""

    total_invites: int
    pending_invites: int
    accepted_invites: int
    reward_months_earned: int
