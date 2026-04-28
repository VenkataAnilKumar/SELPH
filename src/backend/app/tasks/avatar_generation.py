"""Avatar generation tasks
Phase 7 PR A: provider abstraction + DB orchestration foundation
"""

import logging

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.avatar.base import AvatarSynthesisRequest
from app.avatar.registry import get_avatar_provider
from app.config import get_settings
from app.models import Draft, IdentityProfile

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, queue="avatar_generation")
def generate_avatar(
    self,
    draft_id: str,
    user_id: str,
    text: str,
    avatar_style_id: str = None,
    voice_audio_url: str = None,
):
    """Generate avatar video for a draft response."""
    settings = get_settings()
    if not settings.feature_avatar_clone:
        logger.info("Avatar clone feature disabled; skipping draft %s", draft_id)
        return {
            "status": "disabled",
            "draft_id": draft_id,
            "reason": "FEATURE_AVATAR_CLONE is disabled",
        }

    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        draft = db.query(Draft).filter(Draft.id == draft_id, Draft.user_id == user_id).first()
        if not draft:
            return {"status": "error", "draft_id": draft_id, "reason": "Draft not found"}

        profile = db.query(IdentityProfile).filter(IdentityProfile.user_id == user_id).first()
        provider_name = profile.avatar_provider if profile and profile.avatar_provider else settings.avatar_provider
        model_id = avatar_style_id or (profile.avatar_model_id if profile else None) or settings.avatar_default_model_id

        provider = get_avatar_provider(provider_name)
        result = provider.synthesize(
            AvatarSynthesisRequest(
                text=text,
                avatar_model_id=model_id,
                voice_audio_url=voice_audio_url,
                user_id=user_id,
                draft_id=draft_id,
            )
        )

        draft.avatar_provider = result.provider
        draft.avatar_model_id = model_id

        if result.ok:
            draft.avatar_status = "generated"
            draft.avatar_video_url = result.video_url
            draft.avatar_error = None
            status = "success"
        else:
            draft.avatar_status = "failed"
            draft.avatar_error = result.error
            status = "failed"

        db.commit()

        return {
            "status": status,
            "draft_id": draft_id,
            "provider": result.provider,
            "avatar_status": draft.avatar_status,
            "video_url": draft.avatar_video_url,
            "error": draft.avatar_error,
        }
    finally:
        db.close()


@shared_task
def batch_generate_avatars(draft_ids: list, user_id: str):
    """Generate avatars for multiple drafts in batch."""
    logger.info("[PHASE 7 FOUNDATION] Batch avatar generation queued for %d drafts", len(draft_ids))

    return {
        "status": "phase_7_foundation",
        "drafts_queued": len(draft_ids),
    }
