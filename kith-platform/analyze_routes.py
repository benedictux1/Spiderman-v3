#!/usr/bin/env python3
"""
Route Analysis Script for Flask App Consolidation
Analyzes app.py and app/__init__.py to identify unique routes and features
"""

import re
import sys
from pathlib import Path

def extract_routes_from_file(filepath):
    """Extract all @app.route decorators from a Python file"""
    routes = []
    with open(filepath, 'r') as f:
        content = f.read()
        lines = content.split('\n')
        
    for i, line in enumerate(lines):
        # Match @app.route or @blueprint.route patterns
        route_match = re.search(r'@\w+\.route\(["\']([^"\']+)["\'](?:,\s*methods=\[([^\]]+)\])?\)', line)
        if route_match:
            route_path = route_match.group(1)
            methods = route_match.group(2) if route_match.group(2) else 'GET'
            
            # Get function name from next few lines
            func_name = None
            for j in range(i+1, min(i+5, len(lines))):
                func_match = re.search(r'def\s+(\w+)\(', lines[j])
                if func_match:
                    func_name = func_match.group(1)
                    break
            
            routes.append({
                'path': route_path,
                'methods': methods,
                'function': func_name,
                'line': i + 1
            })
    
    return routes

def find_unique_features(app_py_path, app_init_path):
    """Find features in app.py that aren't in app/__init__.py"""
    
    with open(app_py_path, 'r') as f:
        app_py_content = f.read()
    
    with open(app_init_path, 'r') as f:
        app_init_content = f.read()
    
    features = {
        'chromadb': 'chromadb' in app_py_content.lower() and 'chromadb' not in app_init_content.lower(),
        'cache_redis': 'Cache(app)' in app_py_content and 'Cache(app)' not in app_init_content,
        'calendar': 'CalendarIntegration' in app_py_content and 'CalendarIntegration' not in app_init_content,
        'flask_login_custom': 'login_manager = LoginManager()' in app_py_content,
    }
    
    return features

def main():
    base_path = Path(__file__).parent
    app_py = base_path / 'app.py'
    app_init = base_path / 'app' / '__init__.py'
    
    print("=" * 80)
    print("FLASK APP CONSOLIDATION - ROUTE ANALYSIS")
    print("=" * 80)
    print()
    
    # Extract routes
    print("📊 Extracting routes from app.py...")
    app_py_routes = extract_routes_from_file(app_py)
    print(f"   Found {len(app_py_routes)} routes")
    
    print("\n📊 Extracting routes from app/__init__.py...")
    app_init_routes = extract_routes_from_file(app_init)
    print(f"   Found {len(app_init_routes)} routes")
    
    # Find unique routes
    app_py_paths = {r['path'] for r in app_py_routes}
    app_init_paths = {r['path'] for r in app_init_routes}
    unique_to_app_py = app_py_paths - app_init_paths
    
    print("\n" + "=" * 80)
    print(f"UNIQUE ROUTES IN app.py (not in app/__init__.py): {len(unique_to_app_py)}")
    print("=" * 80)
    
    for route in sorted(app_py_routes, key=lambda x: x['line']):
        if route['path'] in unique_to_app_py:
            print(f"  {route['path']:<40} {route['methods']:<20} (line {route['line']})")
    
    # Find unique features
    print("\n" + "=" * 80)
    print("UNIQUE FEATURES IN app.py")
    print("=" * 80)
    
    features = find_unique_features(app_py, app_init)
    for feature, present in features.items():
        status = "✅ PRESENT" if present else "❌ ABSENT"
        print(f"  {feature:<30} {status}")
    
    # Generate markdown report
    report_path = base_path / 'MIGRATION_INVENTORY.md'
    with open(report_path, 'w') as f:
        f.write("# Flask App Migration Inventory\n\n")
        f.write(f"Generated: {Path(__file__).name}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- Routes in app.py: {len(app_py_routes)}\n")
        f.write(f"- Routes in app/__init__.py: {len(app_init_routes)}\n")
        f.write(f"- Unique routes to migrate: {len(unique_to_app_py)}\n\n")
        
        f.write("## Routes in app.py NOT in app/__init__.py\n\n")
        f.write("| Route | Methods | Function | Line |\n")
        f.write("|-------|---------|----------|------|\n")
        
        for route in sorted(app_py_routes, key=lambda x: x['line']):
            if route['path'] in unique_to_app_py:
                f.write(f"| `{route['path']}` | {route['methods']} | `{route['function']}` | {route['line']} |\n")
        
        f.write("\n## Middleware & Config Differences\n\n")
        for feature, present in features.items():
            status = "✅ Present" if present else "❌ Absent"
            f.write(f"- **{feature}**: {status}\n")
        
        f.write("\n## Migration Checklist\n\n")
        f.write("### Core Infrastructure\n")
        f.write("- [ ] ChromaDB client initialization\n")
        f.write("- [ ] Cache configuration (Redis/SimpleCache)\n")
        f.write("- [ ] Calendar integration\n")
        f.write("- [ ] Flask-Login setup\n\n")
        
        f.write("### Routes to Migrate\n")
        for route in sorted(app_py_routes, key=lambda x: x['path']):
            if route['path'] in unique_to_app_py:
                f.write(f"- [ ] `{route['path']}` - {route['function']}\n")
    
    print(f"\n✅ Report generated: {report_path}")
    print()

if __name__ == '__main__':
    main()

