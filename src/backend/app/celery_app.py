"""
Celery app configuration and initialization
"""

from celery import Celery
from celery.schedules import crontab
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
    broker_connection_retry_on_startup=True,  # keep retrying the broker at boot (Celery 6 default)
    # Never let a Redis outage freeze an API request. Nothing reads task results (callers only
    # keep the task id), so publishing must not touch the result backend at all; before this,
    # `.delay()` retried an unreachable result backend with no practical limit.
    task_ignore_result=True,
    # Bound the broker connection attempt made when publishing from the API process.
    broker_connection_timeout=1,
    broker_transport_options={
        "max_retries": 1,
        "interval_start": 0,
        "interval_step": 0.2,
        "interval_max": 0.5,
        "socket_connect_timeout": 1,
        "socket_timeout": 2,
    },
    task_publish_retry_policy={"max_retries": 1, "interval_start": 0, "interval_step": 0.2, "interval_max": 0.5},
    redis_socket_connect_timeout=1,
    redis_socket_timeout=2,
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
    beat_schedule={
        "proactive-scan-every-6h": {
            "task": "tasks.run_proactive_scan",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        "surge-check-every-15m": {
            "task": "tasks.run_surge_check",
            "schedule": crontab(minute="*/15"),
        },
        "style-evolution-quarterly": {
            "task": "tasks.run_style_evolution",
            "schedule": crontab(minute=0, hour=0, day_of_month="1", month_of_year="*/3"),
        },
        "t2t-maintenance-hourly": {
            "task": "tasks.run_t2t_maintenance",
            "schedule": crontab(minute=0),
        },
    },
)

# Make this the default app so shared_task `.delay()` calls from any process use this broker.
celery_app.set_default()

# Auto-discover tasks from tasks module
celery_app.autodiscover_tasks(["app.tasks"])


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery connection"""
    print(f"Request: {self.request!r}")
