"""
Celery task: send an approved draft reply through its originating channel.
Queued after draft approval to deliver the reply asynchronously.
"""

import logging

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models import Draft
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
            transient = False
            if not success:
                draft = db.query(Draft).filter(Draft.id == draft_id).first()
                # send_failed = the channel API rejected/failed the call: worth retrying.
                # Anything else (no credential, not approved, already sent) is final.
                transient = bool(draft and draft.status == "send_failed")
            result_status = "sent" if success else "skipped"
            logger.info("send_channel_reply: draft=%s status=%s transient=%s", draft_id, result_status, transient)
        finally:
            db.close()
    except Exception as exc:
        logger.error("send_channel_reply failed for draft=%s: %s", draft_id, exc)
        raise self.retry(exc=exc)

    if transient:
        raise self.retry(exc=RuntimeError(f"channel send failed for draft {draft_id}"))
    return {"status": result_status, "draft_id": draft_id}
