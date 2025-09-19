#!/usr/bin/env python3
"""
WSGI entry point for Kith Platform.

Uses the new modular application structure with proper PostgreSQL support.
"""

import os
from app import create_app
from config.settings import ProductionConfig, DevelopmentConfig

# Ensure we're in production mode
os.environ.setdefault('FLASK_ENV', 'production')

# Create the app using the appropriate configuration
config_class = ProductionConfig if os.getenv('FLASK_ENV') == 'production' else DevelopmentConfig
app = create_app(config_class)

# Gunicorn expects `application` by default
application = app

if __name__ == "__main__":
    # For local development
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
