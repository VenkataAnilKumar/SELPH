"""
Referral endpoints
/v1/referrals/*
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import User
from app.schemas.referral import (
    ReferralInviteRequest,
    ReferralInviteResponse,
    ReferralAcceptRequest,
    ReferralSummaryResponse,
)
from app.services.referral import ReferralService

router = APIRouter(tags=["Referrals"])


@router.post("/invite", response_model=ReferralInviteResponse, status_code=status.HTTP_201_CREATED)
async def send_referral_invite(
    request: ReferralInviteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a creator referral invite."""
    if request.invitee_email.lower() == current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot invite your own email",
        )

    invite = ReferralService.create_invite(db, current_user.id, request.invitee_email.lower())

    return ReferralInviteResponse(
        id=invite.id,
        referral_code=invite.referral_code,
        invitee_email=invite.invitee_email,
        status=invite.status,
        reward_status=invite.reward_status,
        created_at=invite.created_at,
    )


@router.post("/accept", response_model=ReferralInviteResponse)
async def accept_referral_invite(
    request: ReferralAcceptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept a referral invite using a referral code."""
    try:
        invite = ReferralService.accept_invite(db, current_user.id, request.referral_code)
    except ValueError as exc:
        detail_map = {
            "self_referral_not_allowed": "Cannot accept your own referral code",
            "referral_code_already_claimed": "Referral code already claimed by another user",
        }
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail_map.get(str(exc), "Referral acceptance conflict"),
        ) from exc

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral invite not found",
        )

    return ReferralInviteResponse(
        id=invite.id,
        referral_code=invite.referral_code,
        invitee_email=invite.invitee_email,
        status=invite.status,
        reward_status=invite.reward_status,
        created_at=invite.created_at,
    )


@router.get("/summary", response_model=ReferralSummaryResponse)
async def get_referral_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's referral summary and earned reward months."""
    summary = ReferralService.get_summary(db, current_user.id)
    return ReferralSummaryResponse(**summary)
