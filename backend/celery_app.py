"""Celery application."""
from celery import Celery
from utils.config import settings

app = Celery(
    "clipify",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["tasks.pipeline"],
)
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "cleanup-old-clips": {
            "task": "tasks.pipeline.cleanup_old_clips",
            "schedule": 86400.0,  # every 24h
        },
        "run-scheduled-publishes": {
            "task": "tasks.pipeline.run_scheduled_publishes",
            "schedule": 60.0,  # every minute
        },
    },
)
