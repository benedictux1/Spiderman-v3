#!/bin/bash
# Local Render Simulation Setup Script

echo "🚀 Setting up local Render simulation..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create network if it doesn't exist
docker network create kith-network 2>/dev/null || true

echo "🔧 Starting PostgreSQL and Redis..."
# Start PostgreSQL
docker run -d \
    --name kith-postgres \
    --network kith-network \
    -e POSTGRES_DB=kith_db \
    -e POSTGRES_USER=kith_user \
    -e POSTGRES_PASSWORD=kith_pass \
    -p 5432:5432 \
    postgres:15 2>/dev/null || echo "PostgreSQL container already running"

# Start Redis
docker run -d \
    --name kith-redis \
    --network kith-network \
    -p 6379:6379 \
    redis:7-alpine 2>/dev/null || echo "Redis container already running"

echo "⏳ Waiting for databases to start..."
sleep 5

# Load environment variables
export $(cat local.env | xargs)

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🗄️ Setting up database..."
# Run database initialization
python -c "
import os
from app import create_app
from app.utils.database import DatabaseManager
from app.models import Base, User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    db_manager = DatabaseManager()
    
    # Create tables
    Base.metadata.create_all(db_manager.engine)
    print('✅ Database tables created')
    
    # Create admin user
    with db_manager.get_session() as session:
        admin_user = session.query(User).filter(User.username == 'admin').first()
        if not admin_user:
            hashed = generate_password_hash('admin123', method='pbkdf2:sha256')
            admin_user = User(
                username='admin',
                password_hash=hashed,
                password_plaintext='admin123',
                role='admin'
            )
            session.add(admin_user)
            session.commit()
            print('✅ Admin user created: admin / admin123')
        else:
            print('✅ Admin user already exists')
"

echo ""
echo "🎉 Local Render simulation is ready!"
echo ""
echo "📋 Next steps:"
echo "  1. Start the web server:"
echo "     python -m gunicorn --workers 2 --bind 0.0.0.0:5000 wsgi:application --reload"
echo ""
echo "  2. In another terminal, start Celery worker:"
echo "     celery -A app.celery_app.celery_app worker --loglevel=info"
echo ""
echo "  3. Open your browser to:"
echo "     http://localhost:5000"
echo ""
echo "  4. Login with:"
echo "     Username: admin"
echo "     Password: admin123"
echo ""
echo "🔧 To stop databases later:"
echo "  docker stop kith-postgres kith-redis"
echo "  docker rm kith-postgres kith-redis"
