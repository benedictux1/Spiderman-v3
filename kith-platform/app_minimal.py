#!/usr/bin/env python3
"""
Minimal Flask app for deployment - fast startup
"""

from flask import Flask, jsonify
import os

# Create minimal Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'fallback-secret-key')

# Simple health check
@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy', 'version': '3.0.0'}), 200

# Root endpoint
@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({'message': 'Kith Platform API', 'status': 'running', 'version': '3.0.0'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
