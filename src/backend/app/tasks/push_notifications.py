"""
Push notification tasks — send Expo push notifications to mobile devices.

Only sends if the user has a registered push_token.
Uses the Expo Push Notification API (https://exp.host/--/api/v2/push/send).
Failures are logged and do not raise so the caller (draft_generation) never
blocks on a notification error.
"""

import logging
import urllib.request
import json

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def _send_expo_push(token: str, title: str, body: str, data: dict) -> None:
    """
    Fire-and-forget HTTP POST to the Expo push service.
    Raises on non-2xx so the caller can log the failure.
    """
    payload = json.dumps(
        {
            "to": token,
            "title": title,
            "body": body,
            "data": data,
            "sound": "default",
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        EXPO_PUSH_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status >= 400:
            raise RuntimeError(f"Expo push API returned {resp.status}")


@shared_task
def notify_draft_ready(user_id: str, draft_id: str) -> dict:
    """
    Send a push notification to a user's mobile device when a new draft
    is ready for approval.

    Args:
        user_id: Owner of the draft
        draft_id: ID of the newly created draft
    """
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.push_token:
            logger.debug(
                "notify_draft_ready: user %s has no push token, skipping", user_id
            )
            return {"sent": False, "reason": "no_token"}

        _send_expo_push(
            token=user.push_token,
            title="New draft ready",
            body="Your twin generated a reply — tap to review it.",
            data={"draft_id": draft_id, "type": "draft_ready"},
        )

        logger.info(
            "notify_draft_ready: sent push to user %s for draft %s", user_id, draft_id
        )
        return {"sent": True}

    except Exception as exc:  # noqa: BLE001
        # Notification failure must never block the main pipeline
        logger.warning(
            "notify_draft_ready: failed to send push to user %s: %s", user_id, exc
        )
        return {"sent": False, "reason": str(exc)}

    finally:
        db.close()
