#!/bin/bash

# Navigate to the kith-platform directory
cd "$(dirname "$0")"

# Set environment variables
export FLASK_ENV=development
export FLASK_SECRET_KEY=local-dev-secret-key-for-testing-12345
export DATABASE_URL=sqlite:///local_kith_platform.db
export DEFAULT_ADMIN_USER=admin
export DEFAULT_ADMIN_PASS=admin123

# Set Python path to include current directory
export PYTHONPATH="$(pwd)"

echo "🚀 Starting Celery Worker..."
echo "📁 Working directory: $(pwd)"
echo "🐍 Python path: $PYTHONPATH"

# Start Celery worker
python3 -m celery -A app.celery_app worker --loglevel=info --concurrency=1
