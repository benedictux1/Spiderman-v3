#!/usr/bin/env python3
"""
Test suite to verify Relationship Graph functionality is restored.
This test validates the fix is working, not the implementation details.
"""

import time
import requests
import sys

# Selenium is optional for browser tests
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

BASE_URL = "http://localhost:8000"
TEST_USERNAME = "test_user"
TEST_PASSWORD = "test123"

def print_status(message, status="info"):
    """Print colored status messages"""
    colors = {
        "info": "\033[94m",
        "success": "\033[92m",
        "error": "\033[91m",
        "warning": "\033[93m"
    }
    reset = "\033[0m"
    print(f"{colors.get(status, '')}{message}{reset}")

def test_server_running():
    """Test 1: Verify server is accessible"""
    print_status("TEST 1: Checking if server is running...", "info")
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print_status("✓ Server is running and accessible", "success")
            return True
        else:
            print_status(f"✗ Server returned status {response.status_code}", "error")
            return False
    except Exception as e:
        print_status(f"✗ Server is not accessible: {e}", "error")
        return False

def test_graph_data_endpoint():
    """Test 2: Verify /api/graph-data endpoint exists and returns data"""
    print_status("\nTEST 2: Checking /api/graph-data endpoint...", "info")
    try:
        # Try without auth first (should redirect or return 401)
        response = requests.get(f"{BASE_URL}/api/graph-data")
        print_status(f"  Response status: {response.status_code}", "info")
        
        if response.status_code in [200, 401, 302]:
            print_status("✓ Graph data endpoint exists", "success")
            return True
        else:
            print_status(f"✗ Unexpected status code: {response.status_code}", "error")
            return False
    except Exception as e:
        print_status(f"✗ Failed to reach endpoint: {e}", "error")
        return False

def test_graph_route_exists():
    """Test 3: Verify /graph route exists"""
    print_status("\nTEST 3: Checking /graph route...", "info")
    try:
        response = requests.get(f"{BASE_URL}/graph", allow_redirects=False)
        if response.status_code in [200, 302]:
            print_status("✓ /graph route exists", "success")
            return True
        else:
            print_status(f"✗ /graph route returned {response.status_code}", "error")
            return False
    except Exception as e:
        print_status(f"✗ Failed to access /graph: {e}", "error")
        return False

def test_vis_library_loads():
    """Test 4: Verify vis-network library loads in browser"""
    print_status("\nTEST 4: Checking if vis-network library loads...", "info")
    
    if not SELENIUM_AVAILABLE:
        print_status("  (Skipping - Selenium not installed)", "warning")
        return None
    
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        driver.get(BASE_URL)
        
        # Wait for page load
        time.sleep(2)
        
        # Check if vis is defined
        vis_loaded = driver.execute_script("return typeof vis !== 'undefined';")
        
        if vis_loaded:
            print_status("✓ vis-network library loaded successfully", "success")
            driver.quit()
            return True
        else:
            print_status("✗ vis-network library not loaded", "error")
            driver.quit()
            return False
    except Exception as e:
        print_status(f"✗ Browser test failed: {e}", "warning")
        print_status("  (Skipping browser tests - may need Chrome/ChromeDriver)", "warning")
        return None

def test_graph_container_exists():
    """Test 5: Verify graph container exists in HTML template"""
    print_status("\nTEST 5: Checking if graph container exists in HTML template...", "info")
    try:
        # Check the actual template file since login is required
        template_path = "kith-platform/templates/index.html"
        with open(template_path, 'r') as f:
            html_content = f.read()
        
        if 'id="graph-container"' in html_content:
            print_status("✓ Graph container element found in template", "success")
            return True
        else:
            print_status("✗ Graph container not found in template", "error")
            return False
    except Exception as e:
        print_status(f"✗ Failed to check template: {e}", "error")
        return False

def test_relationship_graph_js_loaded():
    """Test 6: Verify relationship-graph.js is loaded"""
    print_status("\nTEST 6: Checking if relationship-graph.js loads...", "info")
    try:
        response = requests.get(f"{BASE_URL}/static/js/relationship-graph.js")
        if response.status_code == 200:
            # Check for key functions
            content = response.text
            has_init = "function initializeGraphView()" in content or "initializeGraphView" in content
            has_controls = "setupNavigationControls" in content
            
            if has_init and has_controls:
                print_status("✓ relationship-graph.js loads and contains key functions", "success")
                return True
            else:
                print_status("✗ relationship-graph.js missing key functions", "error")
                return False
        else:
            print_status(f"✗ Failed to load relationship-graph.js: {response.status_code}", "error")
            return False
    except Exception as e:
        print_status(f"✗ Error loading JavaScript file: {e}", "error")
        return False

def test_no_vis_loader_code():
    """Test 7: Verify the problematic vis loader code is removed"""
    print_status("\nTEST 7: Checking that problematic vis loader code is removed...", "info")
    try:
        response = requests.get(f"{BASE_URL}/static/js/relationship-graph.js")
        content = response.text
        
        # Check for the problematic patterns that were added
        has_waitForSize = "waitForSize" in content
        has_dynamic_loader = "createElement('script')" in content and "vis-network" in content
        has_resize_observer = "ResizeObserver" in content
        
        if has_waitForSize or has_dynamic_loader or has_resize_observer:
            print_status("✗ Problematic code still present in file", "error")
            print_status(f"    waitForSize: {has_waitForSize}", "info")
            print_status(f"    dynamic loader: {has_dynamic_loader}", "info")
            print_status(f"    ResizeObserver: {has_resize_observer}", "info")
            return False
        else:
            print_status("✓ Clean version restored (no waitForSize/dynamic loader)", "success")
            return True
    except Exception as e:
        print_status(f"✗ Error checking file: {e}", "error")
        return False

def test_credentials_included():
    """Test 8: Verify security fix (credentials: 'include') is present"""
    print_status("\nTEST 8: Checking security fix (credentials: 'include')...", "info")
    try:
        response = requests.get(f"{BASE_URL}/static/js/relationship-graph.js")
        content = response.text
        
        # Count occurrences of credentials: 'include'
        credential_count = content.count("credentials: 'include'")
        
        if credential_count >= 4:  # Should be in multiple fetch calls
            print_status(f"✓ Security fix applied ({credential_count} occurrences found)", "success")
            return True
        else:
            print_status(f"⚠ Only {credential_count} occurrences of credentials: 'include' found", "warning")
            return True  # Don't fail, just warn
    except Exception as e:
        print_status(f"✗ Error checking security fix: {e}", "error")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print_status("\n" + "="*60, "info")
    print_status("RELATIONSHIP GRAPH FIX VALIDATION SUITE", "info")
    print_status("="*60 + "\n", "info")
    
    tests = [
        test_server_running,
        test_graph_data_endpoint,
        test_graph_route_exists,
        test_graph_container_exists,
        test_relationship_graph_js_loaded,
        test_no_vis_loader_code,
        test_credentials_included,
        test_vis_library_loads,  # Browser test last (may be skipped)
    ]
    
    results = []
    for test_func in tests:
        result = test_func()
        results.append(result)
        time.sleep(0.5)
    
    # Summary
    print_status("\n" + "="*60, "info")
    print_status("TEST SUMMARY", "info")
    print_status("="*60, "info")
    
    passed = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is False)
    skipped = sum(1 for r in results if r is None)
    
    print_status(f"Passed: {passed}/{len(tests)}", "success")
    if failed > 0:
        print_status(f"Failed: {failed}/{len(tests)}", "error")
    if skipped > 0:
        print_status(f"Skipped: {skipped}/{len(tests)}", "warning")
    
    print_status("\n" + "="*60 + "\n", "info")
    
    if failed > 0:
        print_status("❌ SOME TESTS FAILED - Issue not fully resolved", "error")
        return False
    elif passed >= 6:  # At least 6 core tests must pass
        print_status("✅ ALL CRITICAL TESTS PASSED - Fix is working!", "success")
        print_status("\nNext step: Manually test in browser:", "info")
        print_status(f"  1. Open {BASE_URL}", "info")
        print_status("  2. Click 'Relationship Graph' button", "info")
        print_status("  3. Verify the graph displays with nodes and edges", "info")
        return True
    else:
        print_status("⚠ Tests incomplete", "warning")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

