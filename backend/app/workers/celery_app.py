from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "threatwatch",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'app.workers.data_collection',
        'app.workers.threat_analysis',
        'app.workers.notifications'
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'app.workers.data_collection.*': {'queue': 'data_collection'},
        'app.workers.threat_analysis.*': {'queue': 'threat_analysis'},
        'app.workers.notifications.*': {'queue': 'notifications'},
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'collect-mentions-every-15-minutes': {
            'task': 'app.workers.data_collection.collect_all_mentions',
            'schedule': 900.0,  # 15 minutes
        },
        'analyze-mentions-every-5-minutes': {
            'task': 'app.workers.threat_analysis.analyze_unprocessed_mentions',
            'schedule': 300.0,  # 5 minutes
        },
        'cleanup-old-data-daily': {
            'task': 'app.workers.data_collection.cleanup_old_data',
            'schedule': 86400.0,  # 24 hours
        },
    }
)

# Auto-discover tasks
celery_app.autodiscover_tasks()