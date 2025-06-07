"""
Celery configuration for the exam application.
This module sets up Celery for handling background tasks.
"""
import os
from celery import Celery

def make_celery(app):
    """
    Create a Celery instance for the Flask application.
    
    Args:
        app: Flask application instance
        
    Returns:
        Celery instance configured for the Flask app
    """
    celery = Celery(
        app.import_name,
        backend=os.environ.get('CELERY_RESULT_BACKEND', 'rpc://'),
        broker=os.environ.get('CELERY_BROKER_URL', 'amqp://guest:guest@localhost:5672//')
    )
    
    # Configure Celery with Flask app context
    celery.conf.update(app.config)
    
    # Optimize for faster task processing
    celery.conf.update(
        # Increase concurrency for faster processing
        worker_concurrency=4,
        # Prefetch multiplier controls how many tasks a worker prefetches
        worker_prefetch_multiplier=1,
        # Acknowledge tasks as soon as they're received
        task_acks_late=False,
        # Process tasks immediately
        task_always_eager=os.environ.get('CELERY_ALWAYS_EAGER', False),
        # Set a short task time limit (30 seconds)
        task_time_limit=30,
        # Set task priority
        task_default_priority=5,
        # Optimize broker connection pool
        broker_pool_limit=10
    )
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery
