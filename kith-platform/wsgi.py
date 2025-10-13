#!/usr/bin/env python3
"""
WSGI entry point for Kith Platform.

Uses the new modular application structure with proper PostgreSQL support.
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app import create_app
from config.settings import ProductionConfig, DevelopmentConfig

# Ensure we're in production mode
os.environ.setdefault('FLASK_ENV', 'production')

logger.info(f"🔧 WSGI: Starting application in {os.getenv('FLASK_ENV')} mode")
logger.info(f"🔧 WSGI: DATABASE_URL set: {bool(os.getenv('DATABASE_URL'))}")

# Create the app using the appropriate configuration
config_class = ProductionConfig if os.getenv('FLASK_ENV') == 'production' else DevelopmentConfig
app = create_app(config_class)

# Gunicorn expects `application` by default, but also provide `app` for backward compatibility
application = app

logger.info("✅ WSGI: Application created successfully")

if __name__ == "__main__":
    # For local development
    logger.info("🔧 WSGI: Running in development mode")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
