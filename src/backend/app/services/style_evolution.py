"""Style evolution service for divergence and checkpoints."""

from datetime import datetime, UTC
from sqlalchemy.orm import Session
from app.models import StyleCheckpoint, Draft, IdentityVariant


class StyleEvolutionService:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def compute_divergence(db: Session, user_id: str, profile_id: str | None = None) -> float:
        drafts = (
            db.query(Draft)
            .filter(Draft.user_id == user_id, Draft.status.in_(["approved", "edited", "sent"]))
            .order_by(Draft.created_at.desc())
            .limit(20)
            .all()
        )
        if not drafts:
            return 0.0
        avg_conf = sum(d.confidence_score for d in drafts) / len(drafts)
        divergence = max(0.0, min(1.0, round(1.0 - avg_conf, 2)))
        return divergence

    @staticmethod
    def generate_delta_report(db: Session, user_id: str, profile_id: str | None = None) -> dict:
        profile = None
        if profile_id:
            profile = db.query(IdentityVariant).filter(IdentityVariant.id == profile_id, IdentityVariant.user_id == user_id).first()
        return {
            "tone_shift": "medium",
            "verbosity_shift": "low",
            "emoji_shift": "low",
            "reference_profile": profile.profile_name if profile else "default",
        }

    @staticmethod
    def create_checkpoint(db: Session, user_id: str, profile_id: str | None, trigger_type: str) -> StyleCheckpoint:
        divergence = StyleEvolutionService.compute_divergence(db, user_id, profile_id)
        delta = StyleEvolutionService.generate_delta_report(db, user_id, profile_id)
        row = StyleCheckpoint(
            user_id=user_id,
            profile_id=profile_id,
            trigger_type=trigger_type,
            divergence_score=divergence,
            delta_report=delta,
            sample_old="Older approved drafts baseline",
            sample_new="Recent approved drafts sample",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def get_pending_checkpoints(db: Session, user_id: str) -> list[StyleCheckpoint]:
        return (
            db.query(StyleCheckpoint)
            .filter(StyleCheckpoint.user_id == user_id, StyleCheckpoint.decision.is_(None))
            .order_by(StyleCheckpoint.created_at.desc())
            .all()
        )

    @staticmethod
    def get_checkpoint(db: Session, user_id: str, checkpoint_id: str) -> StyleCheckpoint | None:
        return db.query(StyleCheckpoint).filter(StyleCheckpoint.id == checkpoint_id, StyleCheckpoint.user_id == user_id).first()

    @staticmethod
    def apply_checkpoint_decision(
        db: Session,
        user_id: str,
        checkpoint_id: str,
        decision: str,
        updated_dimensions: dict | None,
    ) -> StyleCheckpoint | None:
        row = StyleEvolutionService.get_checkpoint(db, user_id, checkpoint_id)
        if not row:
            return None
        row.decision = decision
        row.updated_dimensions = updated_dimensions
        row.decided_at = StyleEvolutionService._now()
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
