"""
Identity endpoints
/v1/identity/*
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import User
from app.services.identity import IdentityService
from app.services.twin import TwinService
from app.schemas.identity import (
    OnboardingRequest,
    OnboardingResponse,
    TopicRequest,
    TopicResponse,
    IdentityProfileResponse,
    UpdateIdentityRequest,
    IdentityConfidenceResponse,
    RESPONSE_LENGTH_MAP,
)
from typing import List

router = APIRouter(tags=["Identity"])


@router.post("/onboard", response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED)
async def complete_onboarding(
    request: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit the onboarding questionnaire.

    - Updates Twin: domain, tone, avg_response_length
    - Updates IdentityProfile: vocabulary_description, communication_style, topics_avoided
    - Returns the merged profile state

    Can be called multiple times — subsequent calls update the existing profile.
    """
    avg_length = RESPONSE_LENGTH_MAP[request.response_length]
    vocabulary_description = ", ".join(request.three_words)
    communication_style = f"{request.communication_style.value}; audience tone: {request.audience_tone}"

    # Update Twin profile
    twin = TwinService.update_twin_profile(
        db,
        current_user.id,
        domain=request.role,
        tone=request.communication_style.value,
        avg_response_length=avg_length,
    )

    if not twin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Twin not found. Ensure signup completed successfully.",
        )

    # Update IdentityProfile + topics_avoided
    IdentityService.create_identity_profile(
        db,
        user_id=current_user.id,
        vocabulary_description=vocabulary_description,
        communication_style=communication_style,
        topics_avoided=request.topics_avoided,
    )

    profile = IdentityService.get_identity_profile(db, current_user.id)
    topics_avoided = IdentityService.get_topics_avoided(db, current_user.id)

    return OnboardingResponse(
        twin_id=twin.id,
        domain=twin.domain,
        tone=twin.tone,
        avg_response_length=twin.avg_response_length,
        vocabulary_description=profile.vocabulary_description or "",
        communication_style=profile.communication_style or "",
        topics_avoided=topics_avoided,
        profile_version=1,
    )


@router.get("/profile", response_model=IdentityProfileResponse)
async def get_identity_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the current user's identity profile.

    Returns vocabulary, communication style, known and avoided topics.
    `profile_complete` is True once the onboarding questionnaire has been submitted.
    """
    summary = IdentityService.get_identity_summary(db, current_user.id)

    if summary is None:
        return IdentityProfileResponse(
            vocabulary_description=None,
            communication_style=None,
            topics_known=[],
            topics_avoided=[],
            profile_complete=False,
        )

    profile_complete = bool(
        summary["vocabulary_description"] and summary["communication_style"]
    )

    return IdentityProfileResponse(
        vocabulary_description=summary["vocabulary_description"],
        communication_style=summary["communication_style"],
        topics_known=summary["topics_known"],
        topics_avoided=summary["topics_avoided"],
        profile_complete=profile_complete,
    )


@router.patch("/profile", response_model=IdentityProfileResponse)
async def update_identity_profile(
    request: UpdateIdentityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Partially update the identity profile.

    Only supplied fields are updated; omitted fields are unchanged.
    """
    IdentityService.patch_identity_profile(
        db,
        user_id=current_user.id,
        vocabulary_description=request.vocabulary_description,
        communication_style=request.communication_style,
        topics_known=request.topics_known,
        topics_avoided=request.topics_avoided,
    )

    summary = IdentityService.get_identity_summary(db, current_user.id)
    profile_complete = bool(
        summary and summary["vocabulary_description"] and summary["communication_style"]
    )

    return IdentityProfileResponse(
        vocabulary_description=summary["vocabulary_description"] if summary else None,
        communication_style=summary["communication_style"] if summary else None,
        topics_known=summary["topics_known"] if summary else [],
        topics_avoided=summary["topics_avoided"] if summary else [],
        profile_complete=profile_complete,
    )


# ── Topics: Known ─────────────────────────────────────────────────────────────

@router.get("/topics/known", response_model=List[str])
async def list_known_topics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all topics the twin is comfortable discussing."""
    return IdentityService.get_topics_known(db, current_user.id)


@router.post("/topics/known", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def add_known_topic(
    request: TopicRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a topic the twin can discuss."""
    topic = IdentityService.add_known_topic(db, current_user.id, request.topic, request.context)
    return TopicResponse(
        id=topic.id,
        topic=topic.topic,
        topic_type=topic.topic_type,
        context=topic.context,
        frequency=topic.frequency,
    )


@router.delete("/topics/known/{topic}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_known_topic(
    topic: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a known topic."""
    deleted = IdentityService.delete_topic(db, current_user.id, topic, "known")
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Known topic '{topic}' not found",
        )


# ── Topics: Avoided ───────────────────────────────────────────────────────────

@router.get("/topics/avoided", response_model=List[str])
async def list_avoided_topics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all topics the twin should avoid."""
    return IdentityService.get_topics_avoided(db, current_user.id)


@router.post("/topics/avoided", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def add_avoided_topic(
    request: TopicRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a topic the twin should never discuss."""
    topic = IdentityService.add_avoided_topic(db, current_user.id, request.topic, request.context)
    return TopicResponse(
        id=topic.id,
        topic=topic.topic,
        topic_type=topic.topic_type,
        context=topic.context,
        frequency=topic.frequency,
    )


@router.delete("/topics/avoided/{topic}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_avoided_topic(
    topic: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove an avoided topic."""
    deleted = IdentityService.delete_topic(db, current_user.id, topic, "avoided")
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Avoided topic '{topic}' not found",
        )


# ── Confidence ────────────────────────────────────────────────────────────────

@router.get("/confidence", response_model=IdentityConfidenceResponse)
async def get_identity_confidence(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the twin's identity confidence score.

    Stub implementation: score is based on profile completeness (0–1).
    Phase 2 will replace this with an embedding-based similarity score
    derived from approved draft history.
    """
    result = IdentityService.get_confidence_score(db, current_user.id)
    return IdentityConfidenceResponse(**result)
