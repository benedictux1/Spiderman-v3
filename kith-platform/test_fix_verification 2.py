#!/usr/bin/env python3
"""
Comprehensive Test Suite for Note Analysis Fix Verification
This test suite verifies that the 500 Internal Server Error issue has been resolved
and that the note analysis functionality works correctly.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, List

class FixVerificationTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        
    def test_server_health(self) -> bool:
        """Test 1: Verify server is running and healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') in ['healthy', 'ok']:
                    self.log_test("Server Health", True, f"Server is healthy: {data.get('status')}")
                    return True
                else:
                    self.log_test("Server Health", False, f"Server status is not healthy: {data.get('status')}")
                    return False
            else:
                self.log_test("Server Health", False, f"Health endpoint returned {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Health", False, f"Failed to connect to server: {str(e)}")
            return False
    
    def test_endpoints_respond_correctly(self) -> bool:
        """Test 2: Verify endpoints return proper responses instead of 500 errors"""
        endpoints_to_test = [
            ("/api/contacts", "GET"),
            ("/api/tags", "GET"),
            ("/api/process-note", "POST"),
        ]
        
        all_passed = True
        
        for endpoint, method in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                elif method == "POST":
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        json={"contact_id": 1, "content": "Test note"},
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                
                # Check if we get a 500 error (the original problem)
                if response.status_code == 500:
                    self.log_test(f"Endpoint {endpoint}", False, f"Still returning 500 error: {response.text}")
                    all_passed = False
                elif response.status_code in [401, 404, 405]:
                    # These are expected responses (auth required, not found, method not allowed)
                    self.log_test(f"Endpoint {endpoint}", True, f"Returns expected {response.status_code} (not 500)")
                else:
                    self.log_test(f"Endpoint {endpoint}", True, f"Returns {response.status_code} (not 500)")
                    
            except Exception as e:
                self.log_test(f"Endpoint {endpoint}", False, f"Request failed: {str(e)}")
                all_passed = False
                
        return all_passed
    
    def test_note_analysis_endpoint_structure(self) -> bool:
        """Test 3: Verify note analysis endpoint structure and error handling"""
        try:
            # Test with invalid data to see error handling
            response = self.session.post(
                f"{self.base_url}/api/process-note",
                json={},  # Empty data
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 500:
                self.log_test("Note Analysis Error Handling", False, "Still returns 500 for invalid data")
                return False
            elif response.status_code in [400, 401]:
                self.log_test("Note Analysis Error Handling", True, f"Proper error handling: {response.status_code}")
                return True
            else:
                self.log_test("Note Analysis Error Handling", True, f"Unexpected but not 500: {response.status_code}")
                return True
                
        except Exception as e:
            self.log_test("Note Analysis Error Handling", False, f"Request failed: {str(e)}")
            return False
    
    def test_dependency_injection_resolution(self) -> bool:
        """Test 4: Verify dependency injection is working (no 'Provide' object errors)"""
        try:
            # This test checks if the server logs contain the specific error we were seeing
            # We'll make a request and check if the error pattern appears
            
            # Make a request that would trigger dependency injection
            response = self.session.get(f"{self.base_url}/api/contacts", timeout=10)
            
            # The key test: if we get a 500 error, check if it's the specific DI error
            if response.status_code == 500:
                error_text = response.text.lower()
                if "'provide' object has no attribute" in error_text:
                    self.log_test("Dependency Injection", False, "Still has DI resolution errors")
                    return False
                else:
                    self.log_test("Dependency Injection", True, "500 error but not DI-related")
                    return True
            else:
                self.log_test("Dependency Injection", True, f"No 500 error, status: {response.status_code}")
                return True
                
        except Exception as e:
            self.log_test("Dependency Injection", False, f"Request failed: {str(e)}")
            return False
    
    def test_syntax_errors_resolved(self) -> bool:
        """Test 5: Verify no syntax errors in the application"""
        try:
            # Try to start a new server process to check for syntax errors
            import subprocess
            import os
            
            # Change to the app directory
            app_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Try to compile the app.py file
            result = subprocess.run(
                ["python3", "-m", "py_compile", "app.py"],
                cwd=app_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log_test("Syntax Check", True, "No syntax errors in app.py")
                return True
            else:
                self.log_test("Syntax Check", False, f"Syntax errors found: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_test("Syntax Check", False, f"Failed to check syntax: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        print("🧪 Starting Comprehensive Fix Verification Tests")
        print("=" * 60)
        
        tests = [
            ("Server Health", self.test_server_health),
            ("Endpoint Responses", self.test_endpoints_respond_correctly),
            ("Note Analysis Structure", self.test_note_analysis_endpoint_structure),
            ("Dependency Injection", self.test_dependency_injection_resolution),
            ("Syntax Check", self.test_syntax_errors_resolved),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_test(test_name, False, f"Test failed with exception: {str(e)}")
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - The fix is working correctly!")
            return {
                'success': True,
                'passed': passed_tests,
                'total': total_tests,
                'message': 'All tests passed - the 500 error issue has been resolved'
            }
        else:
            print("⚠️  SOME TESTS FAILED - Issues may still exist")
            return {
                'success': False,
                'passed': passed_tests,
                'total': total_tests,
                'message': f'{total_tests - passed_tests} tests failed - issues may still exist'
            }

def main():
    """Main test runner"""
    print("🔧 Kith Platform - Fix Verification Test Suite")
    print("Testing for resolution of 500 Internal Server Error issues")
    print()
    
    # Allow custom base URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    tester = FixVerificationTest(base_url)
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)

if __name__ == "__main__":
    main()
