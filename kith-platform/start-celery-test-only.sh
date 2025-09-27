#!/bin/bash
# Start Celery worker for TEST TASKS ONLY
# This prevents AI task contamination

echo "🧪 Starting Celery worker for TEST TASKS ONLY"
echo "============================================="

# Navigate to kith-platform directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Set environment variables
export FLASK_ENV=development
export FLASK_SECRET_KEY=local-dev-secret-key-for-testing-12345
export DATABASE_URL=sqlite:///local_kith_platform.db
export DEFAULT_ADMIN_USER=admin
export DEFAULT_ADMIN_PASS=admin123
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Clear Redis to remove any contaminated tasks
echo "🗑️  Clearing Redis queue..."
redis-cli FLUSHALL

# Start Celery worker with ONLY test tasks
echo "🚀 Starting Celery worker (test tasks only)..."
python3 -m celery -A app.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    --include=app.tasks.test_tasks \
    --purge \
    --queues=test_queue
