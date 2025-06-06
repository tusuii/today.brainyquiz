#!/bin/bash
set -e

# Wait for the database to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! pg_isready -h db -p 5432 -U quizuser; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Run our custom script to add is_live column
echo "Running custom script to add is_live column..."
python add_is_live_column.py

# Start the application
echo "Starting the application..."
exec gunicorn --bind 0.0.0.0:5000 --log-level debug "app:create_app()"
