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
    IdentityOnboardingStatusResponse,
    VoiceConsentRequest,
    VoiceConsentResponse,
    VoiceEnrollmentRequest,
    VoiceEnrollmentResponse,
    AvatarConsentRequest,
    AvatarConsentResponse,
    AvatarEnrollmentRequest,
    AvatarEnrollmentResponse,
    TwinBriefingCreateRequest,
    TwinBriefingResponse,
    TwinBriefingListResponse,
    SenderTierUpsertRequest,
    SenderTierResponse,
    SenderTierListResponse,
    RESPONSE_LENGTH_MAP,
)
from app.schemas.identity_profiles import (
    IdentityVariantCreateRequest,
    IdentityVariantUpdateRequest,
    IdentityVariantResponse,
    IdentityVariantListResponse,
    ChannelProfileMappingUpsertRequest,
    ChannelProfileMappingResponse,
    ChannelProfileMappingListResponse,
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


@router.get("/onboarding/status", response_model=IdentityOnboardingStatusResponse)
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return onboarding completion, blockers, and next-step guidance."""
    status_payload = IdentityService.get_onboarding_status(db, current_user.id)
    return IdentityOnboardingStatusResponse(**status_payload)


# ── Twin Briefings (Phase 9 PR A) ───────────────────────────────────────────

@router.post("/briefings", response_model=TwinBriefingResponse, status_code=status.HTTP_201_CREATED)
async def create_twin_briefing(
    request: TwinBriefingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a briefing that is injected into future twin prompts."""
    try:
        briefing = IdentityService.create_twin_briefing(
            db,
            user_id=current_user.id,
            briefing_type=request.briefing_type.value,
            topic=request.topic,
            content=request.content,
            priority=request.priority,
            expires_at=request.expires_at,
            max_uses=request.max_uses,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return TwinBriefingResponse(
        id=briefing.id,
        user_id=briefing.user_id,
        briefing_type=briefing.briefing_type,
        topic=briefing.topic,
        content=briefing.content,
        priority=briefing.priority,
        is_active=briefing.is_active,
        expires_at=briefing.expires_at,
        max_uses=briefing.max_uses,
        use_count=briefing.use_count,
        cleared_at=briefing.cleared_at,
        created_at=briefing.created_at,
        updated_at=briefing.updated_at,
    )


@router.get("/briefings", response_model=TwinBriefingListResponse)
async def list_twin_briefings(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List current user briefings, defaulting to active-only."""
    rows = IdentityService.list_twin_briefings(
        db,
        user_id=current_user.id,
        include_inactive=include_inactive,
    )
    active_count = IdentityService.count_active_twin_briefings(db, current_user.id)

    return TwinBriefingListResponse(
        active_count=active_count,
        items=[
            TwinBriefingResponse(
                id=row.id,
                user_id=row.user_id,
                briefing_type=row.briefing_type,
                topic=row.topic,
                content=row.content,
                priority=row.priority,
                is_active=row.is_active,
                expires_at=row.expires_at,
                max_uses=row.max_uses,
                use_count=row.use_count,
                cleared_at=row.cleared_at,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ],
    )


@router.post("/briefings/{briefing_id}/clear", response_model=TwinBriefingResponse)
async def clear_twin_briefing(
    briefing_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear a briefing immediately so it is no longer active."""
    briefing = IdentityService.clear_twin_briefing(db, current_user.id, briefing_id)
    if not briefing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Briefing not found")

    return TwinBriefingResponse(
        id=briefing.id,
        user_id=briefing.user_id,
        briefing_type=briefing.briefing_type,
        topic=briefing.topic,
        content=briefing.content,
        priority=briefing.priority,
        is_active=briefing.is_active,
        expires_at=briefing.expires_at,
        max_uses=briefing.max_uses,
        use_count=briefing.use_count,
        cleared_at=briefing.cleared_at,
        created_at=briefing.created_at,
        updated_at=briefing.updated_at,
    )


# ── VIP Override / Sender Tiers (Phase 9 PR B) ─────────────────────────────

@router.put("/sender-tiers", response_model=SenderTierResponse)
async def upsert_sender_tier(
    request: SenderTierUpsertRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update routing tier for a sender on a platform."""
    row = IdentityService.upsert_sender_tier(
        db,
        user_id=current_user.id,
        sender_id=request.sender_id,
        platform=request.platform,
        tier=request.tier,
        tier_label=request.tier_label,
        notes=request.notes,
        set_by=request.set_by,
    )

    return SenderTierResponse(
        id=row.id,
        user_id=row.user_id,
        sender_id=row.sender_id,
        platform=row.platform,
        tier=row.tier,
        tier_label=row.tier_label,
        set_by=row.set_by,
        notes=row.notes,
        last_interaction_at=row.last_interaction_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/sender-tiers", response_model=SenderTierListResponse)
async def list_sender_tiers(
    platform: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List sender-tier overrides, optionally filtered by platform."""
    rows = IdentityService.list_sender_tiers(db, current_user.id, platform)
    return SenderTierListResponse(
        total=len(rows),
        items=[
            SenderTierResponse(
                id=row.id,
                user_id=row.user_id,
                sender_id=row.sender_id,
                platform=row.platform,
                tier=row.tier,
                tier_label=row.tier_label,
                set_by=row.set_by,
                notes=row.notes,
                last_interaction_at=row.last_interaction_at,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ],
    )


@router.delete("/sender-tiers/{platform}/{sender_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sender_tier(
    platform: str,
    sender_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete sender-tier override for a platform sender pair."""
    deleted = IdentityService.delete_sender_tier(db, current_user.id, platform, sender_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sender tier not found")


# ── Voice Clone (Phase 6 PR B) ──────────────────────────────────────────────

@router.get("/voice/consent", response_model=VoiceConsentResponse)
async def get_voice_consent(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current voice clone consent state."""
    consent = IdentityService.get_voice_consent(db, current_user.id)
    if not consent:
        return VoiceConsentResponse(
            consent_type="voice_clone",
            granted=False,
            granted_at=None,
            expires_at=None,
        )

    return VoiceConsentResponse(
        consent_type=consent.consent_type,
        granted=consent.granted,
        granted_at=consent.granted_at.isoformat() if consent.granted_at else None,
        expires_at=consent.expires_at.isoformat() if consent.expires_at else None,
    )


@router.post("/voice/consent", response_model=VoiceConsentResponse)
async def set_voice_consent(
    request: VoiceConsentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Grant or revoke consent for voice cloning."""
    consent = IdentityService.set_voice_consent(db, current_user.id, request.granted)
    if not request.granted:
        # Revoke enrolled voice data when consent is revoked.
        IdentityService.clear_voice_profile(db, current_user.id)

    return VoiceConsentResponse(
        consent_type=consent.consent_type,
        granted=consent.granted,
        granted_at=consent.granted_at.isoformat() if consent.granted_at else None,
        expires_at=consent.expires_at.isoformat() if consent.expires_at else None,
    )


@router.get("/voice/profile", response_model=VoiceEnrollmentResponse)
async def get_voice_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current voice enrollment metadata and consent state."""
    profile = IdentityService.get_identity_profile(db, current_user.id)
    consent_granted = IdentityService.is_voice_consent_granted(db, current_user.id)
    enrolled = bool(profile and profile.voice_model_id)

    return VoiceEnrollmentResponse(
        enrolled=enrolled,
        voice_provider=profile.voice_provider if profile else None,
        voice_model_id=profile.voice_model_id if profile else None,
        voice_sample_url=profile.voice_sample_url if profile else None,
        consent_granted=consent_granted,
    )


@router.post("/voice/enroll", response_model=VoiceEnrollmentResponse)
async def enroll_voice_profile(
    request: VoiceEnrollmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enroll or update a voice profile after explicit voice clone consent."""
    if not IdentityService.is_voice_consent_granted(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Voice clone consent is required before enrollment",
        )

    profile = IdentityService.enroll_voice_profile(
        db,
        user_id=current_user.id,
        voice_provider=request.voice_provider,
        voice_model_id=request.voice_model_id,
        voice_sample_url=request.voice_sample_url,
    )

    return VoiceEnrollmentResponse(
        enrolled=bool(profile.voice_model_id),
        voice_provider=profile.voice_provider,
        voice_model_id=profile.voice_model_id,
        voice_sample_url=profile.voice_sample_url,
        consent_granted=True,
    )


@router.delete("/voice/profile", response_model=VoiceEnrollmentResponse)
async def clear_voice_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear voice enrollment metadata while leaving consent unchanged."""
    profile = IdentityService.clear_voice_profile(db, current_user.id)
    consent_granted = IdentityService.is_voice_consent_granted(db, current_user.id)
    return VoiceEnrollmentResponse(
        enrolled=False,
        voice_provider=profile.voice_provider,
        voice_model_id=profile.voice_model_id,
        voice_sample_url=profile.voice_sample_url,
        consent_granted=consent_granted,
    )


# ── Avatar Clone (Phase 7 PR B) ─────────────────────────────────────────────

@router.get("/avatar/consent", response_model=AvatarConsentResponse)
async def get_avatar_consent(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current avatar clone consent state."""
    consent = IdentityService.get_avatar_consent(db, current_user.id)
    if not consent:
        return AvatarConsentResponse(
            consent_type="avatar_clone",
            granted=False,
            granted_at=None,
            expires_at=None,
        )

    return AvatarConsentResponse(
        consent_type=consent.consent_type,
        granted=consent.granted,
        granted_at=consent.granted_at.isoformat() if consent.granted_at else None,
        expires_at=consent.expires_at.isoformat() if consent.expires_at else None,
    )


@router.post("/avatar/consent", response_model=AvatarConsentResponse)
async def set_avatar_consent(
    request: AvatarConsentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Grant or revoke consent for avatar cloning."""
    consent = IdentityService.set_avatar_consent(db, current_user.id, request.granted)
    if not request.granted:
        # Revoke enrolled avatar data when consent is revoked.
        IdentityService.clear_avatar_profile(db, current_user.id)

    return AvatarConsentResponse(
        consent_type=consent.consent_type,
        granted=consent.granted,
        granted_at=consent.granted_at.isoformat() if consent.granted_at else None,
        expires_at=consent.expires_at.isoformat() if consent.expires_at else None,
    )


@router.get("/avatar/profile", response_model=AvatarEnrollmentResponse)
async def get_avatar_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current avatar enrollment metadata and consent state."""
    profile = IdentityService.get_identity_profile(db, current_user.id)
    consent_granted = IdentityService.is_avatar_consent_granted(db, current_user.id)
    enrolled = bool(profile and profile.avatar_model_id)

    return AvatarEnrollmentResponse(
        enrolled=enrolled,
        avatar_provider=profile.avatar_provider if profile else None,
        avatar_model_id=profile.avatar_model_id if profile else None,
        avatar_sample_url=profile.avatar_sample_url if profile else None,
        consent_granted=consent_granted,
    )


@router.post("/avatar/enroll", response_model=AvatarEnrollmentResponse)
async def enroll_avatar_profile(
    request: AvatarEnrollmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enroll or update an avatar profile after explicit avatar clone consent."""
    if not IdentityService.is_avatar_consent_granted(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Avatar clone consent is required before enrollment",
        )

    profile = IdentityService.enroll_avatar_profile(
        db,
        user_id=current_user.id,
        avatar_provider=request.avatar_provider,
        avatar_model_id=request.avatar_model_id,
        avatar_sample_url=request.avatar_sample_url,
    )

    return AvatarEnrollmentResponse(
        enrolled=bool(profile.avatar_model_id),
        avatar_provider=profile.avatar_provider,
        avatar_model_id=profile.avatar_model_id,
        avatar_sample_url=profile.avatar_sample_url,
        consent_granted=True,
    )


@router.delete("/avatar/profile", response_model=AvatarEnrollmentResponse)
async def clear_avatar_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear avatar enrollment metadata while leaving consent unchanged."""
    profile = IdentityService.clear_avatar_profile(db, current_user.id)
    consent_granted = IdentityService.is_avatar_consent_granted(db, current_user.id)
    return AvatarEnrollmentResponse(
        enrolled=False,
        avatar_provider=profile.avatar_provider,
        avatar_model_id=profile.avatar_model_id,
        avatar_sample_url=profile.avatar_sample_url,
        consent_granted=consent_granted,
    )


# ── Multi-Identity Profiles (Phase 10) ─────────────────────────────────────

@router.get("/profiles", response_model=IdentityVariantListResponse)
async def list_profiles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = IdentityService.list_profiles(db, current_user.id)
    return IdentityVariantListResponse(total=len(rows), items=[IdentityVariantResponse.model_validate(r) for r in rows])


@router.post("/profiles", response_model=IdentityVariantResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    request: IdentityVariantCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        row = IdentityService.create_profile(
            db,
            user_id=current_user.id,
            profile_name=request.profile_name,
            profile_type=request.profile_type,
            vocabulary_description=request.vocabulary_description,
            communication_style=request.communication_style,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return IdentityVariantResponse.model_validate(row)


@router.patch("/profiles/{profile_id}", response_model=IdentityVariantResponse)
async def update_profile(
    profile_id: str,
    request: IdentityVariantUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = IdentityService.update_profile(
        db,
        user_id=current_user.id,
        profile_id=profile_id,
        profile_name=request.profile_name,
        profile_type=request.profile_type,
        vocabulary_description=request.vocabulary_description,
        communication_style=request.communication_style,
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return IdentityVariantResponse.model_validate(row)


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = IdentityService.deactivate_profile(db, current_user.id, profile_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")


@router.post("/profiles/{profile_id}/primary", response_model=IdentityVariantResponse)
async def set_primary_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = IdentityService.set_primary_profile(db, current_user.id, profile_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return IdentityVariantResponse.model_validate(row)


@router.get("/channel-mappings", response_model=ChannelProfileMappingListResponse)
async def list_channel_mappings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = IdentityService.list_channel_mappings(db, current_user.id)
    return ChannelProfileMappingListResponse(total=len(rows), items=[ChannelProfileMappingResponse.model_validate(r) for r in rows])


@router.put("/channel-mappings", response_model=ChannelProfileMappingResponse)
async def upsert_channel_mapping(
    request: ChannelProfileMappingUpsertRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = IdentityService.upsert_channel_mapping(
        db,
        user_id=current_user.id,
        profile_id=request.profile_id,
        channel=request.channel,
        platform_account=request.platform_account,
        priority=request.priority,
    )
    return ChannelProfileMappingResponse.model_validate(row)


@router.delete("/channel-mappings/{channel}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel_mapping(
    channel: str,
    platform_account: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = IdentityService.delete_channel_mapping(db, current_user.id, channel, platform_account)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found")
