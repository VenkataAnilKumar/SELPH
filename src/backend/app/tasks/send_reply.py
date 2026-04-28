"""
Celery task: send an approved draft reply through its originating channel.
Queued after draft approval to deliver the reply asynchronously.
"""

import logging

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.services.channel import ChannelService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30, queue="channels")
def send_channel_reply(self, draft_id: str) -> dict:
    """
    Send an approved draft reply through its originating channel.

    Retries up to 3 times with 30-second delays on transient failures
    (e.g., rate limits, temporary API unavailability).

    Args:
        draft_id: The Draft.id to send.

    Returns:
        { status: "sent" | "skipped", draft_id: str }
    """
    settings = get_settings()

    try:
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        try:
            success = ChannelService.send_draft_reply(db, draft_id)
            result_status = "sent" if success else "skipped"
            logger.info("send_channel_reply: draft=%s status=%s", draft_id, result_status)
            return {"status": result_status, "draft_id": draft_id}
        finally:
            db.close()

    except Exception as exc:
        logger.error("send_channel_reply failed for draft=%s: %s", draft_id, exc)
        raise self.retry(exc=exc)
