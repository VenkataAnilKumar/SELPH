"""
Message processing tasks
Handles incoming messages from channels and queues draft generation
"""

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.models import Message
from app.services import MessageService
from app.tasks.draft_generation import process_draft_generation
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(bind=True, max_retries=3)
def process_incoming_message(
    self,
    user_id: str,
    channel: str,
    sender_id: str,
    sender_name: str,
    content: str,
    channel_metadata: dict = None,
):
    """
    Process an incoming message from a channel
    
    Flow:
    1. Create message in database
    2. Queue draft generation task
    3. Return message ID for webhook response
    
    Args:
        user_id: Owner of the twin
        channel: Channel name (instagram_dm, gmail, slack, etc.)
        sender_id: External sender ID from channel
        sender_name: Sender's display name
        content: Message content
        channel_metadata: Channel-specific metadata
    
    Returns:
        dict with message_id and status
    """
    try:
        # Create database session
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # 1. Create message in database
            message = MessageService.create_message(
                db=db,
                user_id=user_id,
                channel=channel,
                sender_id=sender_id,
                sender_name=sender_name,
                content=content,
                channel_metadata=channel_metadata or {},
            )
            
            logger.info(f"Message {message.id} created from {channel}")
            
            # 2. Queue draft generation task
            process_draft_generation.delay(message.id, user_id)
            logger.info(f"Draft generation queued for message {message.id}")
            
            return {
                "status": "success",
                "message_id": message.id,
                "channel": channel,
            }
        
        finally:
            db.close()
    
    except Exception as exc:
        logger.error(f"Error processing incoming message: {exc}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def batch_process_messages(user_id: str, channel: str, messages: list):
    """
    Process multiple messages in a batch (e.g., sync from channel)
    
    Args:
        user_id: Owner of the twin
        channel: Channel name
        messages: List of dicts with sender_id, sender_name, content, metadata
    
    Returns:
        dict with processed count and task IDs
    """
    results = []
    
    for msg in messages:
        task = process_incoming_message.delay(
            user_id=user_id,
            channel=channel,
            sender_id=msg.get("sender_id"),
            sender_name=msg.get("sender_name"),
            content=msg.get("content"),
            channel_metadata=msg.get("metadata", {}),
        )
        results.append(task.id)
    
    logger.info(f"Batch processed {len(results)} messages for user {user_id}")
    
    return {
        "status": "success",
        "messages_queued": len(results),
        "task_ids": results,
    }
