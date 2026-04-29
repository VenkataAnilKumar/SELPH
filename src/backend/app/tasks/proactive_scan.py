"""Celery task for proactive signal scanning."""

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models import User
from app.services.proactive import ProactiveService


settings = get_settings()


@shared_task(name="tasks.run_proactive_scan")
def run_proactive_scan(user_id: str | None = None) -> dict:
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        if user_id:
            created = ProactiveService.scan_signals(db, user_id)
            return {"user_id": user_id, "suggestions_created": len(created)}

        users = db.query(User).filter(User.is_active.is_(True)).all()
        total = 0
        for user in users:
            total += len(ProactiveService.scan_signals(db, user.id))
        return {"users_scanned": len(users), "suggestions_created": total}
    finally:
        db.close()
