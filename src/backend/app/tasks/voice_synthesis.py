"""
Voice synthesis tasks
Phase 6 PR A: provider abstraction + DB orchestration foundation
"""

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

from app.config import get_settings
from app.models import Draft, IdentityProfile
from app.voice.base import VoiceSynthesisRequest
from app.voice.registry import get_voice_provider

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, queue="voice_synthesis")
def synthesize_voice(
    self,
    draft_id: str,
    user_id: str,
    text: str,
    voice_profile_id: str = None,
):
    """
    Synthesize voice for a draft response

    Args:
        draft_id: Draft to generate voice for
        user_id: Owner of the twin
        text: Text to synthesize
        voice_profile_id: Optional provider model ID override
    
    Returns:
        dict with synthesis status and metadata
    """
    settings = get_settings()
    if not settings.feature_voice_clone:
        logger.info("Voice clone feature disabled; skipping draft %s", draft_id)
        return {
            "status": "disabled",
            "draft_id": draft_id,
            "reason": "FEATURE_VOICE_CLONE is disabled",
        }

    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        draft = db.query(Draft).filter(Draft.id == draft_id, Draft.user_id == user_id).first()
        if not draft:
            return {"status": "error", "draft_id": draft_id, "reason": "Draft not found"}

        profile = db.query(IdentityProfile).filter(IdentityProfile.user_id == user_id).first()
        provider_name = profile.voice_provider if profile and profile.voice_provider else settings.voice_provider
        model_id = voice_profile_id or (profile.voice_model_id if profile else None) or settings.voice_default_model_id

        provider = get_voice_provider(provider_name)
        result = provider.synthesize(
            VoiceSynthesisRequest(
                text=text,
                voice_model_id=model_id,
                user_id=user_id,
                draft_id=draft_id,
            )
        )

        draft.voice_provider = result.provider
        draft.voice_model_id = model_id

        if result.ok:
            draft.voice_status = "generated"
            draft.voice_audio_url = result.audio_url
            draft.voice_error = None
            status = "success"
        else:
            draft.voice_status = "failed"
            draft.voice_error = result.error
            status = "failed"

        db.commit()

        return {
            "status": status,
            "draft_id": draft_id,
            "provider": result.provider,
            "voice_status": draft.voice_status,
            "audio_url": draft.voice_audio_url,
            "error": draft.voice_error,
        }
    finally:
        db.close()


@shared_task
def batch_synthesize_voices(draft_ids: list, user_id: str):
    """
    Synthesize voices for multiple drafts in batch
    
    Args:
        draft_ids: List of draft IDs
        user_id: Owner of the twin
    
    Returns:
        dict with processing status
    """
    logger.info(f"[PHASE 6 STUB] Batch voice synthesis queued for {len(draft_ids)} drafts")
    
    return {
        "status": "phase_6_placeholder",
        "drafts_queued": len(draft_ids),
    }
