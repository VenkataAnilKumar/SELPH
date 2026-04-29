"""Celery task for crisis surge checks."""

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models import User
from app.services.crisis import CrisisService


settings = get_settings()


@shared_task(name="tasks.run_surge_check")
def run_surge_check(user_id: str | None = None) -> dict:
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    activated = 0
    try:
        if user_id:
            status = CrisisService.check_surge(db, user_id)
            if status["trigger"]:
                CrisisService.activate_crisis_mode(db, user_id, "volume_surge", "crisis_alert")
                activated += 1
            return {"user_id": user_id, "activated": activated}

        users = db.query(User).filter(User.is_active.is_(True)).all()
        for user in users:
            status = CrisisService.check_surge(db, user.id)
            if status["trigger"]:
                CrisisService.activate_crisis_mode(db, user.id, "volume_surge", "crisis_alert")
                activated += 1
        return {"users_scanned": len(users), "activated": activated}
    finally:
        db.close()
