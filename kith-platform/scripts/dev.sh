#!/bin/bash
set -e

# Kith Platform Development Script
# This script sets up the development environment

echo "🛠️  Setting up Kith Platform Development Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads logs

# Start development services
echo "🚀 Starting development services..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 15

# Check if services are healthy
echo "🏥 Checking service health..."
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Application is healthy"
else
    echo "⚠️  Application health check failed, but continuing..."
fi

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f docker-compose.dev.yml exec web python -m alembic upgrade head

echo "🎉 Development environment is ready!"
echo "🌐 Application: http://localhost:5000"
echo "📊 Health check: http://localhost:5000/health"
echo "📈 Metrics: http://localhost:5000/metrics"
echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose -f docker-compose.dev.yml logs -f"
echo "  Stop services: docker-compose -f docker-compose.dev.yml down"
echo "  Restart services: docker-compose -f docker-compose.dev.yml restart"
echo "  Run tests: docker-compose -f docker-compose.dev.yml exec web python simple_test_runner.py"

# Show running services
echo ""
echo "📋 Running services:"
docker-compose -f docker-compose.dev.yml ps
