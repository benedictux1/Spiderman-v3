#!/usr/bin/env python3
"""
WSGI entry point for Kith Platform
This file provides a standard WSGI interface for deployment
"""

import os
from main import app

# Ensure we're in production mode
os.environ.setdefault('FLASK_ENV', 'production')

# The WSGI application object
application = app

if __name__ == "__main__":
    # For development
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
