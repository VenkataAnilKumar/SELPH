"""
Draft generation tasks using LangGraph twin engine
Phase 0: Stub implementation with placeholder LangGraph orchestration
Phase 1+: Replace with full twin engine integration
"""

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.models import Message, Draft, Twin, IdentityProfile
from app.services import DraftService, ModerationService, IdentityService
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(bind=True, max_retries=3)
def generate_draft_for_message(self, message_id: str, user_id: str):
    """
    Generate a draft response for an incoming message
    
    Orchestration flow:
    1. Fetch message + twin + identity
    2. Run moderation on incoming message
    3. Call LangGraph twin engine to generate response
    4. Calculate confidence score
    5. Create draft in database
    
    Phase 0: Stub with placeholder engine
    Phase 1: Integrate full LangGraph twin engine
    
    Args:
        message_id: Message to respond to
        user_id: Owner of the twin
    """
    try:
        # Create database session
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # 1. Fetch message
            message = db.query(Message).filter(Message.id == message_id).first()
            if not message:
                logger.error(f"Message {message_id} not found")
                return {"status": "error", "reason": "Message not found"}
            
            # 2. Fetch twin + identity
            twin = db.query(Twin).filter(Twin.user_id == user_id).first()
            identity = db.query(IdentityProfile).filter(IdentityProfile.user_id == user_id).first()
            
            if not twin or not identity:
                logger.error(f"Twin or identity not found for user {user_id}")
                return {"status": "error", "reason": "Twin or identity not found"}
            
            # 3. Run moderation on incoming message
            moderation_passed, flags, risk_score = ModerationService.check_content_safety(
                message.content
            )
            
            logger.info(
                f"Message {message_id} moderation: passed={moderation_passed}, "
                f"risk={risk_score}, flags={len(flags)}"
            )
            
            # 4. Generate draft using placeholder engine
            # Phase 1: Replace with real LangGraph orchestration
            draft_content = _generate_draft_placeholder(
                message=message,
                twin=twin,
                identity=identity,
            )
            
            # 5. Calculate confidence score
            confidence_score = ModerationService.calculate_confidence_score(
                user_interaction_count=1,
                moderation_passed=moderation_passed,
                topic_match=0.5,  # Placeholder: would come from semantic matching
            )
            confidence_label = ModerationService.get_confidence_label(confidence_score)
            
            # 6. Create draft
            draft = DraftService.create_draft(
                db=db,
                message_id=message_id,
                user_id=user_id,
                twin_id=twin.id,
                content=draft_content,
                confidence_score=confidence_score,
                confidence_label=confidence_label,
                confidence_reasoning="Phase 0 placeholder generation",
                moderation_passed=moderation_passed,
                moderation_flags=[{"pattern": f.get("pattern"), "risk": f.get("risk")} for f in flags],
            )
            
            # Mark message as draft_ready
            message.status = "draft_ready"
            db.commit()
            
            logger.info(f"Draft {draft.id} created for message {message_id}")
            
            return {
                "status": "success",
                "draft_id": draft.id,
                "confidence": confidence_score,
                "moderation_passed": moderation_passed,
            }
        
        finally:
            db.close()
    
    except Exception as exc:
        logger.error(f"Error generating draft: {exc}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def process_draft_generation(message_id: str, user_id: str):
    """
    Async wrapper for draft generation - called from routers
    
    This task queues the actual draft generation without blocking the request
    """
    return generate_draft_for_message.delay(message_id, user_id)


def _generate_draft_placeholder(message, twin, identity) -> str:
    """
    Placeholder draft generation for Phase 0
    
    Phase 0: Rule-based template responses
    Phase 1: Full LangGraph twin engine with:
    - Memory retrieval system
    - Context window management
    - Style/tone application
    - Topic awareness
    - User feedback incorporation
    
    Args:
        message: Incoming message
        twin: Twin profile
        identity: Twin identity profile
    
    Returns:
        Generated draft response
    """
    # Phase 0 placeholder: Echo with twin personality
    sender_name = message.sender_name or "Friend"
    
    templates = {
        "professional": f"Thank you for reaching out, {sender_name}. I appreciate your message.",
        "casual": f"Hey {sender_name}! Thanks for the message.",
        "creative": f"Interesting point, {sender_name}! Let me think about that...",
        "supportive": f"I'm here for you, {sender_name}. Let's talk about this.",
    }
    
    tone = twin.tone.lower() if twin.tone else "professional"
    template = templates.get(tone, templates["professional"])
    
    # Append message preview
    preview = message.content[:50] + "..." if len(message.content) > 50 else message.content
    draft = f"{template}\n\nRe: {preview}"
    
    return draft
