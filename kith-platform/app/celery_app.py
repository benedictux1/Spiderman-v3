import os
import logging
from celery import Celery
from typing import Optional
from config.settings import Config

logger = logging.getLogger(__name__)

def create_celery_app(flask_app: Optional[object] = None):
    """Create and configure Celery application"""
    # Get Redis URL with fallback and validation
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    logger.info(f"Initializing Celery with Redis URL pattern: {redis_url[:20]}...")
    
    if redis_url.startswith('${{'):
        logger.error(f"Environment variable not resolved: {redis_url}")
        # Fallback for development
        redis_url = 'redis://localhost:6379/0'
        logger.warning(f"Using fallback Redis URL: {redis_url}")
    
    celery = Celery('kith_platform')
    
    # Configure Celery
    celery.conf.update(
        broker_url=redis_url,
        result_backend=redis_url,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,  # 25 minutes
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        # Keep memory small on Starter (512MB)
        worker_concurrency=1,
        worker_pool='solo',
        # Reduce result backend pressure
        result_expires=3600,
    )
    
    # Configure modules for worker to import at startup to avoid circular imports
    celery.conf.update(
        include=[
            'app.tasks.ai_tasks',
            'app.tasks.telegram_tasks',
            'app.tasks.test_tasks',
        ]
    )
    # As a light fallback in dev, attempt autodiscovery of 'tasks' modules under 'app'
    try:
        celery.autodiscover_tasks(['app'])
    except Exception as e:
        logger.debug(f"Autodiscover skipped: {e}")
    
    # Optionally bind Flask app context for tasks
    if flask_app is not None:
        TaskBase = celery.Task
        class ContextTask(TaskBase):
            def __call__(self, *args, **kwargs):
                with flask_app.app_context():
                    return TaskBase.__call__(self, *args, **kwargs)
        celery.Task = ContextTask
        logger.info("Celery tasks bound to Flask application context")

    return celery

# Create the Celery app instance
try:
    # Try to import the Flask app to bind context when used from worker
    from app import create_app
    _flask_app = create_app()
    celery_app = create_celery_app(_flask_app)
except Exception as _bind_err:
    logger.warning(f"Could not bind Celery to Flask app at import time: {_bind_err}")
    celery_app = create_celery_app()
