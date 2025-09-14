#!/bin/bash
set -e

echo "Starting Kith Platform..."

# Wait for database to be ready
echo "Waiting for database..."
while ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER; do
  echo "Database is unavailable - sleeping"
  sleep 1
done
echo "Database is ready!"

# Run database migrations
echo "Running database migrations..."
python -m alembic upgrade head

# Create uploads directory if it doesn't exist
mkdir -p /app/uploads
mkdir -p /app/logs

# Set proper permissions
chown -R app:app /app/uploads /app/logs

echo "Starting application..."
exec "$@"
