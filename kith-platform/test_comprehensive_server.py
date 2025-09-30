#!/usr/bin/env python3
"""
Test server to verify comprehensive features work
"""
import os
import sys

# Set up environment
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'
os.environ['DATABASE_URL'] = 'sqlite:///test_kith.db'

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🚀 Starting Comprehensive Kith Platform Test Server")
print("📍 Server URL: http://localhost:8000")
print("🔧 Press Ctrl+C to stop")
print("=" * 50)

try:
    from app import create_app
    
    app = create_app()
    
    print("✅ App created successfully")
    print("📊 Registered API routes:")
    
    api_routes = []
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith('/api/'):
            api_routes.append(f"  {rule.rule} -> {rule.methods}")
    
    for route in sorted(api_routes)[:10]:  # Show first 10
        print(route)
    
    if len(api_routes) > 10:
        print(f"  ... and {len(api_routes) - 10} more API routes")
    
    print("=" * 50)
    
    # Run the server
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=True,
        use_reloader=False
    )
    
except Exception as e:
    print(f"❌ Failed to start server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
