#!/bin/bash
set -e

# Kith Platform Deployment Script
# This script handles deployment to production

echo "🚀 Starting Kith Platform Deployment..."

# Check if required environment variables are set
if [ -z "$FLASK_SECRET_KEY" ]; then
    echo "❌ FLASK_SECRET_KEY environment variable is required"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: No AI API keys provided (GEMINI_API_KEY or OPENAI_API_KEY)"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads logs docker/nginx/ssl

# Generate SSL certificates if they don't exist
if [ ! -f "docker/nginx/ssl/cert.pem" ] || [ ! -f "docker/nginx/ssl/key.pem" ]; then
    echo "🔐 Generating self-signed SSL certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout docker/nginx/ssl/key.pem \
        -out docker/nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down || true

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🏥 Checking service health..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Application is healthy"
else
    echo "❌ Application health check failed"
    echo "📋 Service logs:"
    docker-compose logs --tail=50
    exit 1
fi

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec web python -m alembic upgrade head

echo "🎉 Deployment completed successfully!"
echo "🌐 Application is available at: https://localhost"
echo "📊 Health check: https://localhost/health"
echo "📈 Metrics: https://localhost/metrics"

# Show running services
echo "📋 Running services:"
docker-compose ps
