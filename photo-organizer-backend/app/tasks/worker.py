from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "photo-organizer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=1800,   # 30 min: raises SoftTimeLimitExceeded
    task_time_limit=2100,        # 35 min: hard kill
)

celery_app.autodiscover_tasks(["app.tasks"], related_name="pipeline")
