#!/usr/bin/env python3
"""
Start the Flask server on port 8001 to bypass browser caching issues.
"""

import sys
import os

# Add current directory to path
sys.path.append('.')

try:
    from app import create_app
    
    print('🚀 Starting Flask development server on port 8001...')
    print('📍 Server will be available at: http://localhost:8001')
    print('🔧 Press Ctrl+C to stop')
    print('🔄 This bypasses browser caching issues')
    
    app = create_app()
    
    # Enable template auto-reload to fix caching issues
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    app.run(host='0.0.0.0', port=8001, debug=True)
    
except Exception as e:
    print(f'❌ Error starting server: {e}')
    import traceback
    traceback.print_exc()
