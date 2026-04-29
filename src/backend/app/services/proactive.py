"""Proactive suggestion detection and actions."""

from datetime import datetime, UTC, timedelta
from sqlalchemy.orm import Session
from app.models import Message, Draft, ProactiveSuggestion, ProactivePreference


class ProactiveService:
    DEAL_KEYWORDS = ("collab", "sponsor", "partnership", "rate", "deal")

    @staticmethod
    def get_or_create_preferences(db: Session, user_id: str) -> ProactivePreference:
        prefs = db.query(ProactivePreference).filter(ProactivePreference.user_id == user_id).first()
        if prefs:
            return prefs
        prefs = ProactivePreference(user_id=user_id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
        return prefs

    @staticmethod
    def update_preferences(db: Session, user_id: str, updates: dict) -> ProactivePreference:
        prefs = ProactiveService.get_or_create_preferences(db, user_id)
        for key, value in updates.items():
            if value is not None:
                setattr(prefs, key, value)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
        return prefs

    @staticmethod
    def _under_daily_limit(db: Session, user_id: str, prefs: ProactivePreference) -> bool:
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        count = db.query(ProactiveSuggestion).filter(
            ProactiveSuggestion.user_id == user_id,
            ProactiveSuggestion.created_at >= today_start,
        ).count()
        return count < prefs.max_suggestions_per_day

    @staticmethod
    def create_suggestion(
        db: Session,
        user_id: str,
        suggestion_type: str,
        contact_id: str | None,
        signal_summary: str,
        draft_message: str,
        urgency: float,
        value: float,
    ) -> ProactiveSuggestion:
        row = ProactiveSuggestion(
            user_id=user_id,
            suggestion_type=suggestion_type,
            contact_id=contact_id,
            signal_summary=signal_summary,
            draft_message=draft_message,
            urgency_score=urgency,
            value_score=value,
            status="pending",
        )
        db.add(row)
        db.flush()
        return row

    @staticmethod
    def _detect_cold_relationships(db: Session, user_id: str, threshold_days: int) -> list[dict]:
        threshold = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=threshold_days)
        messages = db.query(Message).filter(
            Message.user_id == user_id,
            Message.created_at <= threshold,
        ).order_by(Message.created_at.asc()).limit(20).all()
        items = []
        for msg in messages:
            items.append(
                {
                    "type": "cold_relationship",
                    "contact_id": msg.sender_id,
                    "summary": f"No recent conversation with {msg.sender_name}.",
                    "draft": f"Hey {msg.sender_name}, just checking in. Hope you are doing well.",
                    "urgency": 0.55,
                    "value": 0.6,
                }
            )
        return items

    @staticmethod
    def _detect_open_threads(db: Session, user_id: str, threshold_hours: int) -> list[dict]:
        threshold = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=threshold_hours)
        rows = (
            db.query(Message)
            .outerjoin(Draft, Draft.message_id == Message.id)
            .filter(
                Message.user_id == user_id,
                Message.created_at <= threshold,
                Draft.id.is_(None),
            )
            .order_by(Message.created_at.asc())
            .limit(20)
            .all()
        )
        return [
            {
                "type": "open_thread",
                "contact_id": msg.sender_id,
                "summary": f"Open thread from {msg.sender_name} waiting for reply.",
                "draft": f"Thanks for your message, {msg.sender_name}. I will get back with details shortly.",
                "urgency": 0.7,
                "value": 0.55,
            }
            for msg in rows
        ]

    @staticmethod
    def _detect_deal_signals(db: Session, user_id: str) -> list[dict]:
        rows = db.query(Message).filter(Message.user_id == user_id).order_by(Message.created_at.desc()).limit(50).all()
        matches = []
        for msg in rows:
            lower = msg.content.lower()
            if any(word in lower for word in ProactiveService.DEAL_KEYWORDS):
                matches.append(
                    {
                        "type": "deal_signal",
                        "contact_id": msg.sender_id,
                        "summary": f"Potential deal signal from {msg.sender_name}.",
                        "draft": f"Thanks {msg.sender_name}, happy to explore this opportunity. Could you share next steps?",
                        "urgency": 0.8,
                        "value": 0.8,
                    }
                )
        return matches

    @staticmethod
    def _detect_follow_ups(db: Session, user_id: str) -> list[dict]:
        rows = db.query(Message).filter(Message.user_id == user_id).order_by(Message.created_at.desc()).limit(20).all()
        return [
            {
                "type": "follow_up",
                "contact_id": msg.sender_id,
                "summary": f"Follow-up suggested for {msg.sender_name}.",
                "draft": f"Quick follow-up on this, {msg.sender_name}. Let me know what works best for you.",
                "urgency": 0.5,
                "value": 0.5,
            }
            for msg in rows[:3]
        ]

    @staticmethod
    def scan_signals(db: Session, user_id: str) -> list[ProactiveSuggestion]:
        prefs = ProactiveService.get_or_create_preferences(db, user_id)
        if not prefs.enabled or not ProactiveService._under_daily_limit(db, user_id, prefs):
            return []

        candidates = []
        if "cold_relationship" in prefs.enabled_types:
            candidates.extend(ProactiveService._detect_cold_relationships(db, user_id, prefs.cold_threshold_days))
        if "open_thread" in prefs.enabled_types:
            candidates.extend(ProactiveService._detect_open_threads(db, user_id, prefs.open_thread_hours))
        if "deal_signal" in prefs.enabled_types:
            candidates.extend(ProactiveService._detect_deal_signals(db, user_id))
        if "follow_up" in prefs.enabled_types:
            candidates.extend(ProactiveService._detect_follow_ups(db, user_id))

        created = []
        for item in candidates[: prefs.max_suggestions_per_day]:
            if not ProactiveService._under_daily_limit(db, user_id, prefs):
                break
            created.append(
                ProactiveService.create_suggestion(
                    db,
                    user_id,
                    item["type"],
                    item["contact_id"],
                    item["summary"],
                    item["draft"],
                    item["urgency"],
                    item["value"],
                )
            )

        db.commit()
        for row in created:
            db.refresh(row)
        return created

    @staticmethod
    def list_suggestions(db: Session, user_id: str, status: str | None = None, limit: int = 50) -> list[ProactiveSuggestion]:
        query = db.query(ProactiveSuggestion).filter(ProactiveSuggestion.user_id == user_id)
        if status:
            query = query.filter(ProactiveSuggestion.status == status)
        return query.order_by(ProactiveSuggestion.created_at.desc()).limit(limit).all()

    @staticmethod
    def act_on_suggestion(
        db: Session,
        suggestion_id: str,
        user_id: str,
        action: str,
        edited_message: str | None,
        snooze_days: int,
    ) -> ProactiveSuggestion | None:
        row = db.query(ProactiveSuggestion).filter(
            ProactiveSuggestion.id == suggestion_id,
            ProactiveSuggestion.user_id == user_id,
        ).first()
        if not row:
            return None

        now = datetime.now(UTC).replace(tzinfo=None)
        if action == "approve":
            row.status = "approved"
            if edited_message:
                row.draft_message = edited_message
            row.acted_at = now
        elif action == "dismiss":
            row.status = "dismissed"
            row.acted_at = now
        elif action == "never":
            row.status = "never"
            row.acted_at = now
        elif action == "snooze":
            row.status = "snoozed"
            row.snoozed_until = now + timedelta(days=snooze_days)
        else:
            raise ValueError("Unsupported action")

        db.add(row)
        db.commit()
        db.refresh(row)
        return row
