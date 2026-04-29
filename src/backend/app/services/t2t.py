"""Twin-to-twin session handshake and negotiation service."""

from datetime import datetime, UTC, timedelta
from sqlalchemy.orm import Session
from app.models import T2TSession


class T2TService:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def detect_t2t_capable(message_content: str) -> bool:
        lower = message_content.lower()
        return "x-selph-t2t" in lower or "powered by selph" in lower

    @staticmethod
    def initiate_session(db: Session, initiating_twin: str, receiving_twin: str, session_type: str) -> T2TSession:
        now = T2TService._now()
        row = T2TSession(
            initiating_twin=initiating_twin,
            receiving_twin=receiving_twin,
            session_type=session_type,
            status="handshake",
            negotiation_log=[{"event": "initiated", "at": now.isoformat()}],
            started_at=now,
            expires_at=now + timedelta(hours=48),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def list_sessions(db: Session, twin_id: str) -> list[T2TSession]:
        return (
            db.query(T2TSession)
            .filter((T2TSession.initiating_twin == twin_id) | (T2TSession.receiving_twin == twin_id))
            .order_by(T2TSession.created_at.desc())
            .all()
        )

    @staticmethod
    def get_session(db: Session, session_id: str) -> T2TSession | None:
        return db.query(T2TSession).filter(T2TSession.id == session_id).first()

    @staticmethod
    def add_negotiation_turn(db: Session, session_id: str, turn: dict) -> T2TSession | None:
        row = T2TService.get_session(db, session_id)
        if not row:
            return None
        log = list(row.negotiation_log or [])
        log.append(turn)
        row.negotiation_log = log
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def propose_outcome(db: Session, session_id: str, proposal: dict) -> T2TSession | None:
        row = T2TService.get_session(db, session_id)
        if not row:
            return None
        row.proposal = proposal
        row.status = "proposed"
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def record_approval(db: Session, session_id: str, twin_id: str, approved: bool) -> T2TSession | None:
        row = T2TService.get_session(db, session_id)
        if not row:
            return None

        if row.expires_at <= T2TService._now():
            row.status = "expired"
            db.add(row)
            db.commit()
            db.refresh(row)
            return row

        if twin_id == row.initiating_twin:
            row.initiator_approved = approved
        elif twin_id == row.receiving_twin:
            row.receiver_approved = approved

        if row.initiator_approved is True and row.receiver_approved is True:
            row.status = "completed"
            row.completed_at = T2TService._now()
        elif approved is False:
            row.status = "rejected"

        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def exit_session(db: Session, session_id: str) -> T2TSession | None:
        row = T2TService.get_session(db, session_id)
        if not row:
            return None
        row.status = "exited"
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def expire_stale_sessions(db: Session) -> int:
        now = T2TService._now()
        rows = db.query(T2TSession).filter(T2TSession.status.in_(["handshake", "proposed"]), T2TSession.expires_at <= now).all()
        for row in rows:
            row.status = "expired"
            db.add(row)
        db.commit()
        return len(rows)
