#!/usr/bin/env python3
"""
Test script to check what routes are actually registered in the Flask app
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the Flask app from app.py (not app/ directory)
    import importlib.util
    kith_dir = os.path.dirname(os.path.abspath(__file__))
    app_py_path = os.path.join(kith_dir, 'app.py')
    spec = importlib.util.spec_from_file_location("main_app_module", app_py_path)
    main_app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_app)
    app = main_app.app
    
    print("=" * 80)
    print("REGISTERED ROUTES IN FLASK APP")
    print("=" * 80)
    
    # Get all registered routes
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
            'path': str(rule)
        })
    
    # Sort by path
    routes.sort(key=lambda x: x['path'])
    
    # Filter to show categories routes
    print("\n🔍 SEARCHING FOR CATEGORY ROUTES:")
    print("-" * 80)
    category_routes = [r for r in routes if 'categor' in r['path'].lower()]
    if category_routes:
        for route in category_routes:
            print(f"✅ {route['methods']:15s} {route['path']}")
            print(f"   └─ Endpoint: {route['endpoint']}")
    else:
        print("❌ NO CATEGORY ROUTES FOUND!")
    
    # Show all /api/contact/ routes
    print("\n🔍 ALL /api/contact/ ROUTES:")
    print("-" * 80)
    contact_routes = [r for r in routes if '/api/contact' in r['path']]
    for route in contact_routes:
        print(f"{route['methods']:15s} {route['path']}")
    
    print("\n" + "=" * 80)
    print(f"Total routes registered: {len(routes)}")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

