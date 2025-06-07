#!/bin/bash

# Wait for RabbitMQ to be ready
/app/wait-for-it.sh rabbitmq:5672 -t 60

# Start Celery worker
exec celery -A app.celery worker --loglevel=info
