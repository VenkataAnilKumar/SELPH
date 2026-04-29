"""Celery task for style evolution checkpoints."""

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models import User
from app.services.style_evolution import StyleEvolutionService


settings = get_settings()


@shared_task(name="tasks.run_style_evolution")
def run_style_evolution(user_id: str | None = None) -> dict:
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        created = 0
        if user_id:
            StyleEvolutionService.create_checkpoint(db, user_id, None, "automatic")
            return {"user_id": user_id, "created": 1}

        users = db.query(User).filter(User.is_active.is_(True)).all()
        for user in users:
            StyleEvolutionService.create_checkpoint(db, user.id, None, "automatic")
            created += 1
        return {"users_scanned": len(users), "created": created}
    finally:
        db.close()
