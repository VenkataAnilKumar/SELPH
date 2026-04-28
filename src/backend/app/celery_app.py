"""
Celery app configuration and initialization
"""

from celery import Celery
from app.config import get_settings

settings = get_settings()

# Initialize Celery app
celery_app = Celery(
    "selph",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # Results expire in 1 hour
)

# Auto-discover tasks from tasks module
celery_app.autodiscover_tasks(["app.tasks"])


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery connection"""
    print(f"Request: {self.request!r}")
