import os
import logging
from celery import Celery
from config.settings import Config

logger = logging.getLogger(__name__)

def create_celery_app():
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
    )
    
    # Auto-discover tasks
    celery.autodiscover_tasks(['app.tasks'])
    
    return celery

# Create the Celery app instance
celery_app = create_celery_app()
