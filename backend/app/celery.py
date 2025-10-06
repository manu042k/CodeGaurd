from celery import Celery
import os

# Create Celery instance
celery_app = Celery(
    "codeguard",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_serializer_max_retry_delay=30 * 60,  # 30 minutes
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.services'])

if __name__ == "__main__":
    celery_app.start()
