"""
Draft generation tasks using LangGraph twin engine
Phase 0: Stub implementation with placeholder LangGraph orchestration
Phase 1+: Replace with full twin engine integration
"""

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.models import Message
from app.services import DraftService, TwinEngineService
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
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        try:
            # 1. Fetch message
            message = db.query(Message).filter(Message.id == message_id).first()
            if not message:
                logger.error(f"Message {message_id} not found")
                return {"status": "error", "reason": "Message not found"}
            
            # 2. Run Twin Engine Phase 2 pipeline
            pipeline = TwinEngineService.run_twin_pipeline(db, message.id, user_id)
            
            # 6. Create draft
            draft = DraftService.create_draft(
                db=db,
                message_id=message_id,
                user_id=user_id,
                twin_id=pipeline["twin_id"],
                content=pipeline["draft"],
                confidence_score=pipeline["confidence_score"],
                confidence_label=pipeline["confidence_label"],
                confidence_reasoning=pipeline["confidence_reasoning"],
                moderation_passed=pipeline["moderation_passed"],
                moderation_flags=[{"pattern": f.get("pattern"), "risk": f.get("risk")} for f in pipeline["moderation_flags"]],
                generation_source=pipeline.get("generation_source"),
                llm_model=pipeline.get("llm_model"),
                fallback_reason=pipeline.get("fallback_reason"),
                llm_calls=pipeline.get("metrics", {}).get("llm_calls"),
                parse_retry_count=pipeline.get("metrics", {}).get("parse_retry_count"),
                llm_latency_ms=pipeline.get("metrics", {}).get("llm_latency_ms"),
                pipeline_latency_ms=pipeline.get("metrics", {}).get("pipeline_latency_ms"),
                estimated_input_tokens=pipeline.get("estimated_input_tokens"),
                estimated_output_tokens=pipeline.get("estimated_output_tokens"),
                estimated_total_tokens=pipeline.get("estimated_total_tokens"),
                estimated_cost_usd=pipeline.get("estimated_cost_usd"),
            )
            
            # Mark message as draft_ready
            message.status = "draft_ready"
            db.commit()
            
            logger.info(
                "Draft %s created for message %s source=%s pipeline_latency_ms=%s llm_latency_ms=%s parse_retry_count=%s",
                draft.id,
                message_id,
                pipeline.get("generation_source"),
                pipeline.get("metrics", {}).get("pipeline_latency_ms"),
                pipeline.get("metrics", {}).get("llm_latency_ms"),
                pipeline.get("metrics", {}).get("parse_retry_count"),
            )
            
            return {
                "status": "success",
                "draft_id": draft.id,
                "confidence": pipeline["confidence_score"],
                "moderation_passed": pipeline["moderation_passed"],
                "generation_source": pipeline.get("generation_source"),
                "metrics": pipeline.get("metrics", {}),
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


