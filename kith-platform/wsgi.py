#!/usr/bin/env python3
"""
WSGI entry point for Kith Platform.

Important: We explicitly load the monolithic `app.py` (Flask app instance named `app`)
to avoid name collision with the `app/` package directory. Importing `app` by name
would resolve to the package, not the file. Using SourceFileLoader guarantees we load
the intended module.
"""

import os
from importlib.machinery import SourceFileLoader

# Ensure we're in production mode
os.environ.setdefault('FLASK_ENV', 'production')

# Resolve path to the monolithic Flask app file
BASE_DIR = os.path.dirname(__file__)
APP_FILE_PATH = os.path.join(BASE_DIR, 'app.py')

# Dynamically load the `app.py` module and retrieve the Flask app object
mono_module = SourceFileLoader('kith_mono_app', APP_FILE_PATH).load_module()
app = getattr(mono_module, 'app')

# Gunicorn expects `application` by default
application = app

if __name__ == "__main__":
    # For local development
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
