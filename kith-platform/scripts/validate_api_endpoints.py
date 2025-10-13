#!/usr/bin/env python3
"""
API Endpoint Validation Script

This script validates that frontend API calls match registered backend routes.
Run this script regularly to catch URL mismatches before they cause bugs.

Usage:
    python scripts/validate_api_endpoints.py
    
Returns exit code 0 if all endpoints match, non-zero if mismatches found.
"""

import re
import os
import sys
from pathlib import Path
from typing import List, Tuple, Set
from collections import defaultdict

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def find_backend_routes(app_dir: Path) -> Set[str]:
    """Extract all Flask route definitions from backend code."""
    routes = set()
    
    # Patterns to match Flask routes
    patterns = [
        r"@app\.route\(['\"]([^'\"]+)['\"]",
        r"@\w+_bp\.route\(['\"]([^'\"]+)['\"]",
        r"Blueprint\([^)]+url_prefix=['\"]([^'\"]+)['\"]",
    ]
    
    # Files to scan
    files_to_scan = [
        app_dir / 'app.py',
        app_dir / 'legacy_app.py',
    ]
    
    # Add all API blueprint files
    api_dir = app_dir / 'app' / 'api'
    if api_dir.exists():
        files_to_scan.extend(api_dir.glob('*.py'))
    
    for file_path in files_to_scan:
        if not file_path.exists():
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    route = match.group(1)
                    # Normalize route - remove trailing slashes for comparison
                    route = route.rstrip('/')
                    # Convert <int:id> to /<id> for pattern matching
                    route = re.sub(r'<[^>]+:(\w+)>', r'<\1>', route)
                    routes.add(route)
    
    return routes

def find_frontend_calls(static_dir: Path, templates_dir: Path) -> List[Tuple[str, str, int]]:
    """Extract all API calls from frontend JavaScript and HTML."""
    calls = []
    
    # Patterns to match fetch/axios/ajax calls
    patterns = [
        r"fetch\([`'\"]([^`'\"]+)[`'\"]",
        r"axios\.\w+\([`'\"]([^`'\"]+)[`'\"]",
        r"\$\.ajax\([^)]*url:\s*[`'\"]([^`'\"]+)[`'\"]",
        r"new\s+Request\([`'\"]([^`'\"]+)[`'\"]",
    ]
    
    # Files to scan
    files_to_scan = []
    
    if static_dir.exists():
        files_to_scan.extend(static_dir.rglob('*.js'))
    
    if templates_dir.exists():
        files_to_scan.extend(templates_dir.rglob('*.html'))
    
    for file_path in files_to_scan:
        if not file_path.exists():
            continue
            
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                for pattern in patterns:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        url = match.group(1)
                        # Only include API calls
                        if '/api/' in url:
                            # Extract the path part (remove template literals)
                            # Convert ${id} to <id> for comparison
                            url = re.sub(r'\$\{(\w+)\}', r'<\1>', url)
                            url = url.rstrip('/')
                            calls.append((url, str(file_path), line_num))
    
    return calls

def normalize_route(route: str) -> str:
    """Normalize a route for comparison."""
    # Remove query parameters
    if '?' in route:
        route = route.split('?')[0]
    
    # Remove trailing slash
    route = route.rstrip('/')
    
    # Normalize parameter names
    route = re.sub(r'<\w+>', '<id>', route)
    
    return route

def validate_endpoints(kith_platform_dir: Path) -> Tuple[List[str], List[str]]:
    """
    Validate that frontend calls match backend routes.
    
    Returns:
        Tuple of (matched routes, unmatched routes with details)
    """
    print(f"{Colors.BLUE}🔍 Scanning for API endpoints...{Colors.END}\n")
    
    # Find backend routes
    backend_routes = find_backend_routes(kith_platform_dir)
    print(f"{Colors.GREEN}✓ Found {len(backend_routes)} backend routes{Colors.END}")
    
    # Find frontend calls
    static_dir = kith_platform_dir / 'static'
    templates_dir = kith_platform_dir / 'templates'
    frontend_calls = find_frontend_calls(static_dir, templates_dir)
    print(f"{Colors.GREEN}✓ Found {len(frontend_calls)} frontend API calls{Colors.END}\n")
    
    # Normalize backend routes for comparison
    normalized_backend = {normalize_route(r) for r in backend_routes}
    
    # Check each frontend call
    matched = []
    unmatched = []
    
    for url, file_path, line_num in frontend_calls:
        normalized_url = normalize_route(url)
        
        # Check if it matches any backend route
        if normalized_url in normalized_backend:
            matched.append(f"{url} (in {file_path}:{line_num})")
        else:
            # Check for close matches (potential typos)
            close_matches = [r for r in normalized_backend if similarity(normalized_url, r) > 0.8]
            
            detail = f"{Colors.RED}✗{Colors.END} {url}"
            detail += f"\n  Location: {file_path}:{line_num}"
            if close_matches:
                detail += f"\n  {Colors.YELLOW}Did you mean:{Colors.END} {', '.join(close_matches)}"
            unmatched.append(detail)
    
    return matched, unmatched

def similarity(s1: str, s2: str) -> float:
    """Calculate similarity between two strings (simple Levenshtein-inspired)."""
    if s1 == s2:
        return 1.0
    
    # Simple similarity: count common characters
    common = sum(1 for c in s1 if c in s2)
    return common / max(len(s1), len(s2))

def main():
    """Main entry point."""
    # Find kith-platform directory
    script_dir = Path(__file__).parent
    kith_platform_dir = script_dir.parent
    
    if not kith_platform_dir.exists():
        print(f"{Colors.RED}Error: Could not find kith-platform directory{Colors.END}")
        sys.exit(1)
    
    print(f"{Colors.BOLD}API Endpoint Validator{Colors.END}")
    print(f"Scanning: {kith_platform_dir}\n")
    
    # Validate endpoints
    matched, unmatched = validate_endpoints(kith_platform_dir)
    
    # Print results
    print(f"\n{Colors.BOLD}=== Results ==={Colors.END}\n")
    
    if matched:
        print(f"{Colors.GREEN}✓ {len(matched)} endpoints validated{Colors.END}")
    
    if unmatched:
        print(f"\n{Colors.RED}✗ {len(unmatched)} unmatched frontend calls:{Colors.END}\n")
        for detail in unmatched:
            print(detail)
            print()
        
        print(f"\n{Colors.YELLOW}⚠️  Please verify these endpoints exist in the backend{Colors.END}")
        print(f"{Colors.YELLOW}   or update the frontend to use the correct URLs.{Colors.END}\n")
        sys.exit(1)
    else:
        print(f"\n{Colors.GREEN}✅ All frontend API calls match backend routes!{Colors.END}\n")
        sys.exit(0)

if __name__ == '__main__':
    main()

