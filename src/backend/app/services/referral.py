"""
Referral service
"""

from datetime import datetime, UTC
import uuid

from sqlalchemy.orm import Session

from app.models import ReferralInvite


class ReferralService:
    """Business logic for creator referral invites."""

    @staticmethod
    def _generate_referral_code() -> str:
        return uuid.uuid4().hex[:12]

    @staticmethod
    def create_invite(db: Session, referrer_user_id: str, invitee_email: str) -> ReferralInvite:
        """Create a referral invite if no pending invite exists for this referrer/email pair."""
        existing = db.query(ReferralInvite).filter(
            ReferralInvite.referrer_user_id == referrer_user_id,
            ReferralInvite.invitee_email == invitee_email,
            ReferralInvite.status == "pending",
        ).first()
        if existing:
            return existing

        invite = ReferralInvite(
            referrer_user_id=referrer_user_id,
            invitee_email=invitee_email,
            referral_code=ReferralService._generate_referral_code(),
            status="pending",
            reward_status="unclaimed",
        )
        db.add(invite)
        db.commit()
        db.refresh(invite)
        return invite

    @staticmethod
    def accept_invite(db: Session, invitee_user_id: str, referral_code: str) -> ReferralInvite | None:
        """Accept a referral invite by code."""
        invite = db.query(ReferralInvite).filter(
            ReferralInvite.referral_code == referral_code,
        ).first()
        if not invite:
            return None

        if invite.referrer_user_id == invitee_user_id:
            raise ValueError("self_referral_not_allowed")

        if invite.status == "accepted":
            if invite.invitee_user_id == invitee_user_id:
                return invite
            raise ValueError("referral_code_already_claimed")

        invite.status = "accepted"
        invite.invitee_user_id = invitee_user_id
        invite.accepted_at = datetime.now(UTC).replace(tzinfo=None)

        db.add(invite)
        db.commit()
        db.refresh(invite)
        return invite

    @staticmethod
    def get_summary(db: Session, referrer_user_id: str) -> dict:
        """Get referral summary stats for a user."""
        invites = db.query(ReferralInvite).filter(
            ReferralInvite.referrer_user_id == referrer_user_id,
        )

        total_invites = invites.count()
        pending_invites = invites.filter(ReferralInvite.status == "pending").count()
        accepted_invites = invites.filter(ReferralInvite.status == "accepted").count()

        return {
            "total_invites": total_invites,
            "pending_invites": pending_invites,
            "accepted_invites": accepted_invites,
            "reward_months_earned": accepted_invites,
        }
