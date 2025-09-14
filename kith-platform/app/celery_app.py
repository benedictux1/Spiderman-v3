from celery import Celery
from config.settings import Config

def create_celery_app():
    """Create and configure Celery application"""
    celery = Celery('kith_platform')
    
    # Configure Celery
    celery.conf.update(
        broker_url=Config.CELERY_BROKER_URL,
        result_backend=Config.CELERY_RESULT_BACKEND,
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
