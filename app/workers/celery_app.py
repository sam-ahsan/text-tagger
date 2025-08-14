import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RESULT_EXPIRES = int(os.getenv("CELERY_RESULT_EXPIRES", "3600"))
SOFT_LIMIT = int(os.getenv("CELERY_SOFT_TIME_LIMIT", "55"))
HARD_LIMIT = int(os.getenv("CELERY_TIME_LIMIT", "60"))
TAGGING_QUEUE = os.getenv("CELERY_TAGGING_QUEUE", "tagging")

celery_app = Celery(
    "text-tagger",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.services.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=RESULT_EXPIRES,
    
    # Worker behavior
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_time_limit=HARD_LIMIT,
    task_soft_time_limit=SOFT_LIMIT,
    
    # Routing: heavy tasks on their own queue
    task_routes={
        "app.services.tasks.tag_batch_task": {"queue": TAGGING_QUEUE}
    }
)
