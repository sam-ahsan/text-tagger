import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RESULT_EXPIRES = int(os.getenv("CELERY_RESULT_EXPIRES", "3600"))

celery_app = Celery(
    "text-tagger",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=RESULT_EXPIRES,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_time_limit=int(os.getenv("CELERY_TASK_TIME_LIMIT", "60")),
    task_soft_time_limit=int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "55")),
    include=["app.services.tasks"]
)
