#!/bin/bash

# Wait for RabbitMQ to be ready
/app/wait-for-it.sh rabbitmq:5672 -t 60

# Wait for Celery worker to be ready
/app/wait-for-it.sh celery_worker:8000 -t 30 || true

# Start Flower
exec celery -A app.celery flower --port=5555
