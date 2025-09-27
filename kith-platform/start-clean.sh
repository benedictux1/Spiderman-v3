#!/bin/bash
# Clean startup script that prevents Redis contamination
# This script ensures a clean environment every time

echo "🧹 CLEAN STARTUP SCRIPT"
echo "========================"

# Kill any existing processes
echo "🔪 Killing existing processes..."
pkill -f "python.*celery" 2>/dev/null || true
pkill -f "python.*flask" 2>/dev/null || true
pkill -f "python.*start-kith-local" 2>/dev/null || true

# Kill any process using port 8000
echo "🔌 Freeing port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Clear Redis completely
echo "🗑️  Clearing Redis queue..."
redis-cli FLUSHALL

# Wait a moment for processes to die
sleep 2

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

echo "✅ Environment set up"
echo "🚀 Starting services..."

# Start Celery worker (test tasks only)
echo "📋 Starting Celery worker (test tasks only)..."
python3 -m celery -A app.celery_app worker --loglevel=info --concurrency=1 --include=app.tasks.test_tasks --purge &
CELERY_PID=$!

# Wait for Celery to start
sleep 3

# Check if Celery is running
if ps -p $CELERY_PID > /dev/null; then
    echo "✅ Celery worker started (PID: $CELERY_PID)"
else
    echo "❌ Celery worker failed to start"
    exit 1
fi

# Start Flask server
echo "🌐 Starting Flask server..."
cd ..
python3 start-kith-local.py &
FLASK_PID=$!

# Wait for Flask to start
sleep 5

# Check if Flask is running
if ps -p $FLASK_PID > /dev/null; then
    echo "✅ Flask server started (PID: $FLASK_PID)"
else
    echo "❌ Flask server failed to start"
    kill $CELERY_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "🎉 ALL SERVICES STARTED SUCCESSFULLY!"
echo "======================================"
echo "📍 Flask Server: http://localhost:8000"
echo "🔧 Celery Worker: Running (test tasks only)"
echo "🗄️  Database: SQLite (local_kith_platform.db)"
echo "👤 Admin: admin / admin123"
echo ""
echo "💡 To stop all services:"
echo "   kill $CELERY_PID $FLASK_PID"
echo ""
echo "🔍 To check status:"
echo "   ps aux | grep -E '(celery|flask|start-kith)'"
echo ""

# Keep script running to show status
echo "📊 Monitoring services... (Press Ctrl+C to stop)"
while true; do
    sleep 10
    if ! ps -p $CELERY_PID > /dev/null; then
        echo "❌ Celery worker died!"
        break
    fi
    if ! ps -p $FLASK_PID > /dev/null; then
        echo "❌ Flask server died!"
        break
    fi
    echo "✅ Services running normally..."
done
