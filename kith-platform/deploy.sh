#!/bin/bash

# Kith Platform Deployment Script
# This script runs tests, checks code quality, and prepares for deployment

set -e  # Exit on any error

echo "🚀 Starting Kith Platform deployment process..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Virtual environment not activated. Please run: source venv/bin/activate"
    exit 1
fi

# Run tests
echo "🧪 Running automated tests..."
python -m pytest test_app.py -v --tb=short

if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Tests failed. Please fix issues before deployment."
    exit 1
fi

# Check code coverage
echo "📊 Checking code coverage..."
python -m pytest test_app.py --cov=app --cov-report=term-missing --cov-fail-under=65

if [ $? -eq 0 ]; then
    echo "✅ Code coverage requirements met!"
else
    echo "⚠️  Code coverage below 65%. Consider adding more tests for Phase 2 features."
fi

# Check for environment variables
echo "🔧 Checking environment configuration..."
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  GEMINI_API_KEY not set in environment"
else
    echo "✅ GEMINI_API_KEY is configured"
fi

# Validate requirements.txt
echo "📦 Validating dependencies..."
pip check

if [ $? -eq 0 ]; then
    echo "✅ Dependencies are compatible"
else
    echo "❌ Dependency conflicts found. Please resolve before deployment."
    exit 1
fi

# Check if render.yaml exists
if [ -f "render.yaml" ]; then
    echo "✅ Render.com configuration found"
else
    echo "❌ render.yaml not found. Please create deployment configuration."
    exit 1
fi

# Check if .env file exists (for local development)
if [ -f ".env" ]; then
    echo "✅ Environment file found"
else
    echo "⚠️  .env file not found. Create one for local development."
fi

echo ""
echo "🎉 Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. Commit your changes: git add . && git commit -m 'Deployment ready'"
echo "2. Push to GitHub: git push origin main"
echo "3. Deploy on Render.com using the render.yaml configuration"
echo ""
echo "Remember to set environment variables on Render.com:"
echo "- GEMINI_API_KEY: Your Google AI Studio API key"
echo "- DATABASE_URL: PostgreSQL connection string (optional for MVP)" 