#!/bin/bash
set -e

# Wait for the database to be ready
echo "Waiting for PostgreSQL to be ready..."
# Use DB_HOST environment variable if set, otherwise default to postgres
DB_HOST=${DB_HOST:-postgres}
while ! pg_isready -h $DB_HOST -p 5432 -U "${POSTGRES_USER:-quizuser}"; do
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
echo "Starting the application in production mode..."
exec gunicorn --bind 0.0.0.0:5000 --workers 4 --log-level warning "app:create_app()"
