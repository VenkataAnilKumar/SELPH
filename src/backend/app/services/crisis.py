"""Crisis and surge mode service."""

from datetime import datetime, UTC, timedelta
from sqlalchemy.orm import Session
from app.models import Message, Twin, SurgeEvent, CrisisTemplate


class CrisisService:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def get_twin_mode(db: Session, user_id: str) -> str:
        twin = db.query(Twin).filter(Twin.user_id == user_id).first()
        return twin.twin_operating_mode if twin else "normal"

    @staticmethod
    def get_active_surge_event(db: Session, user_id: str) -> SurgeEvent | None:
        return (
            db.query(SurgeEvent)
            .filter(SurgeEvent.user_id == user_id, SurgeEvent.resolved_at.is_(None))
            .order_by(SurgeEvent.created_at.desc())
            .first()
        )

    @staticmethod
    def check_surge(db: Session, user_id: str) -> dict:
        now = CrisisService._now()
        hour_ago = now - timedelta(hours=1)
        week_ago = now - timedelta(days=7)

        recent = db.query(Message).filter(Message.user_id == user_id, Message.created_at >= hour_ago).count()
        weekly = db.query(Message).filter(Message.user_id == user_id, Message.created_at >= week_ago).count()

        baseline_rate = max(1.0, weekly / (7 * 24))
        trigger = recent >= (baseline_rate * 5)
        return {
            "trigger": trigger,
            "trigger_type": "volume_surge",
            "peak_rate": float(recent),
            "baseline_rate": float(round(baseline_rate, 2)),
            "threshold_value": float(round(baseline_rate * 5, 2)),
        }

    @staticmethod
    def activate_crisis_mode(db: Session, user_id: str, trigger_type: str, mode: str) -> SurgeEvent:
        twin = db.query(Twin).filter(Twin.user_id == user_id).first()
        if not twin:
            raise ValueError("Twin not found")

        surge = CrisisService.check_surge(db, user_id)
        event = SurgeEvent(
            user_id=user_id,
            trigger_type=trigger_type,
            trigger_value=surge["peak_rate"],
            threshold_value=surge["threshold_value"],
            baseline_rate=surge["baseline_rate"],
            peak_rate=surge["peak_rate"],
            mode_activated=mode,
        )
        twin.twin_operating_mode = mode
        db.add(event)
        db.add(twin)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def resolve_crisis(db: Session, user_id: str, resolution_type: str = "manual_resume") -> bool:
        twin = db.query(Twin).filter(Twin.user_id == user_id).first()
        event = CrisisService.get_active_surge_event(db, user_id)
        if not twin:
            return False

        twin.twin_operating_mode = "normal"
        db.add(twin)
        if event:
            event.resolved_at = CrisisService._now()
            event.resolution_type = resolution_type
            db.add(event)
        db.commit()
        return True

    @staticmethod
    def list_crisis_templates(db: Session, user_id: str) -> list[CrisisTemplate]:
        return db.query(CrisisTemplate).filter(CrisisTemplate.user_id == user_id).order_by(CrisisTemplate.created_at.desc()).all()

    @staticmethod
    def create_crisis_template(db: Session, user_id: str, label: str, content: str, template_type: str) -> CrisisTemplate:
        existing = db.query(CrisisTemplate).filter(CrisisTemplate.user_id == user_id).count()
        if existing >= 5:
            raise ValueError("Maximum of 5 crisis templates reached")

        row = CrisisTemplate(
            user_id=user_id,
            label=label,
            content=content,
            template_type=template_type,
            approved_at=CrisisService._now(),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def delete_crisis_template(db: Session, user_id: str, template_id: str) -> bool:
        row = db.query(CrisisTemplate).filter(CrisisTemplate.id == template_id, CrisisTemplate.user_id == user_id).first()
        if not row:
            return False
        db.delete(row)
        db.commit()
        return True
