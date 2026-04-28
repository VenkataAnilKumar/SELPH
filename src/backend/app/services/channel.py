"""
ChannelService — high-level orchestration for OAuth credential management
and reply delivery through channels.
"""

import json
import logging
from datetime import datetime, UTC

from sqlalchemy.orm import Session

from app.channels.registry import get_adapter
from app.models import ChannelCredential, Draft, Message
from app.models.base import utcnow

logger = logging.getLogger(__name__)


class ChannelService:
    """
    High-level channel operations.
    All methods are static; no instance state is needed.
    """

    @staticmethod
    def get_credential(
        db: Session, user_id: str, channel: str
    ) -> ChannelCredential | None:
        """
        Return the active ChannelCredential for a user+channel pair, or None.
        Normalizes 'instagram' → 'instagram_dm' for lookup consistency.
        """
        normalized = _normalize_channel(channel)
        return (
            db.query(ChannelCredential)
            .filter(
                ChannelCredential.user_id == user_id,
                ChannelCredential.channel == normalized,
                ChannelCredential.is_active == True,
            )
            .first()
        )

    @staticmethod
    def upsert_credential(
        db: Session,
        user_id: str,
        channel: str,
        credential_value: str,
        scope: str | None = None,
    ) -> ChannelCredential:
        """
        Create or update a ChannelCredential for a user+channel pair.
        Marks existing credential as active if it was previously disconnected.

        Args:
            db:               SQLAlchemy session.
            user_id:          SELPH user ID.
            channel:          Channel name (normalized before storage).
            credential_value: OAuth access token or JSON blob with token data.
            scope:            JSON string with extra metadata, e.g. { page_id, email }.

        Returns:
            The created or updated ChannelCredential instance.
        """
        normalized = _normalize_channel(channel)
        existing = (
            db.query(ChannelCredential)
            .filter(
                ChannelCredential.user_id == user_id,
                ChannelCredential.channel == normalized,
            )
            .first()
        )

        if existing:
            existing.credential_value = credential_value
            existing.scope = scope
            existing.is_active = True
            existing.last_used_at = utcnow()
        else:
            existing = ChannelCredential(
                user_id=user_id,
                channel=normalized,
                credential_type="oauth_token",
                credential_value=credential_value,
                scope=scope,
                is_active=True,
            )
            db.add(existing)

        db.commit()
        db.refresh(existing)
        return existing

    @staticmethod
    def find_user_by_instagram_page(db: Session, page_id: str) -> str | None:
        """
        Find a SELPH user_id by their connected Instagram page ID.
        The page_id is stored as JSON in the ChannelCredential.scope field:
          scope = '{"page_id": "12345678"}'

        Returns user_id string or None if not found.
        """
        credentials = (
            db.query(ChannelCredential)
            .filter(
                ChannelCredential.channel == "instagram_dm",
                ChannelCredential.is_active == True,
            )
            .all()
        )
        for cred in credentials:
            try:
                scope_data = json.loads(cred.scope) if cred.scope else {}
                if scope_data.get("page_id") == page_id:
                    return cred.user_id
            except (json.JSONDecodeError, AttributeError):
                continue
        return None

    @staticmethod
    def find_user_by_gmail_address(db: Session, email: str) -> str | None:
        """
        Find a SELPH user_id by their connected Gmail email address.
        The email is stored as JSON in the ChannelCredential.scope field:
          scope = '{"email": "user@example.com"}'

        Returns user_id string or None if not found.
        """
        credentials = (
            db.query(ChannelCredential)
            .filter(
                ChannelCredential.channel == "gmail",
                ChannelCredential.is_active == True,
            )
            .all()
        )
        for cred in credentials:
            try:
                scope_data = json.loads(cred.scope) if cred.scope else {}
                if scope_data.get("email") == email:
                    return cred.user_id
            except (json.JSONDecodeError, AttributeError):
                continue
        return None

    @staticmethod
    def send_draft_reply(db: Session, draft_id: str) -> bool:
        """
        Send an approved draft back through its originating channel.

        Flow:
          1. Load draft + its parent message
          2. Look up active ChannelCredential for user+channel
          3. Get the channel adapter from registry
          4. Call adapter.send_reply()
          5. Update draft.status = 'sent' (success) or 'send_failed' (failure)

        Returns:
            True if the reply was sent successfully, False otherwise.
            Returns False (not raises) on any failure — callers should log and retry via Celery.
        """
        draft = db.query(Draft).filter(Draft.id == draft_id).first()
        if not draft:
            logger.error("send_draft_reply: draft %s not found", draft_id)
            return False

        message = db.query(Message).filter(Message.id == draft.message_id).first()
        if not message:
            logger.error(
                "send_draft_reply: message %s not found for draft %s",
                draft.message_id,
                draft_id,
            )
            return False

        cred = ChannelService.get_credential(db, draft.user_id, message.channel)
        if not cred:
            logger.warning(
                "send_draft_reply: no credential for channel=%s user=%s — reply not sent",
                message.channel,
                draft.user_id,
            )
            return False

        reply_text = draft.edited_content or draft.content
        if not reply_text:
            logger.error("send_draft_reply: no reply content for draft %s", draft_id)
            return False

        try:
            adapter = get_adapter(message.channel)
        except ValueError as exc:
            logger.error("send_draft_reply: %s", exc)
            return False

        success = adapter.send_reply(
            credential_value=cred.credential_value,
            recipient_id=message.sender_id,
            text=reply_text,
            metadata=message.channel_metadata,
        )

        if success:
            draft.status = "sent"
            draft.sent_response = reply_text
            message.status = "sent"
        else:
            draft.status = "send_failed"

        db.commit()
        return success


def _normalize_channel(channel: str) -> str:
    """
    Normalize channel names for consistent storage.
    'instagram' → 'instagram_dm' so both forms resolve to the same credential row.
    """
    mapping = {
        "instagram": "instagram_dm",
    }
    return mapping.get(channel.lower().strip(), channel.lower().strip())
