from celery import Celery

from repopal.core.config import settings

celery = Celery("worker", broker=settings.REDIS_URL, backend=settings.REDIS_URL)


@celery.task
def example_task():
    return "Task completed"
