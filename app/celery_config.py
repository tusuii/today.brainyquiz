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
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery
