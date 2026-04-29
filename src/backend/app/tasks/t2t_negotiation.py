"""Celery task for expiring stale T2T sessions."""

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.services.t2t import T2TService


settings = get_settings()


@shared_task(name="tasks.run_t2t_maintenance")
def run_t2t_maintenance() -> dict:
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        expired = T2TService.expire_stale_sessions(db)
        return {"expired": expired}
    finally:
        db.close()
