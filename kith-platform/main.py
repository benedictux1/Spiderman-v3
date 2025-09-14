#!/usr/bin/env python3
"""
Kith Platform - Main Application Entry Point
Refactored modular architecture
"""

import os
from app import create_app
from config.settings import DevelopmentConfig, ProductionConfig

# Determine configuration based on environment
config_class = DevelopmentConfig
if os.getenv('FLASK_ENV') == 'production':
    config_class = ProductionConfig

# Create the Flask application
app = create_app(config_class)

if __name__ == '__main__':
    # Development server
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') != 'production'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
