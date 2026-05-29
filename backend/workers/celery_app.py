"""
Celery Application Configuration
----------------------------------
Celery is the task queue that runs ML jobs asynchronously.
Redis is the message broker — it queues tasks between the API and workers.

Flow:
  API receives request
       ↓
  Creates Celery task → Redis queue
       ↓
  Returns task_id to client immediately
       ↓
  Celery worker picks up task from Redis
       ↓
  Runs ML pipeline (SBERT, TF-IDF, spaCy)
       ↓
  Stores result in Redis
       ↓
  Client polls GET /task/{task_id} for result
"""
from celery import Celery
from core.config import settings

celery_app = Celery(
    "resume_matcher",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["workers.tasks"],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timeouts
    task_soft_time_limit=120,   # warn after 2 min
    task_time_limit=180,        # kill after 3 min

    # Result expiry — keep results for 1 hour
    result_expires=3600,

    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Worker settings
    worker_prefetch_multiplier=1,  # one task at a time per worker (ML tasks are heavy)
    worker_max_tasks_per_child=50, # restart worker every 50 tasks (prevent memory leaks)

    timezone="UTC",
)