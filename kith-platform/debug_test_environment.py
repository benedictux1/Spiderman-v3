#!/usr/bin/env python3
"""
Debug script to diagnose test environment issues
Run this locally to understand what might be failing in the Render environment
"""
import os
import sys
import subprocess
import tempfile
from pathlib import Path

def debug_test_environment():
    print("🔍 DEBUGGING TEST ENVIRONMENT")
    print("=" * 50)
    
    # 1. Python version and environment
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"PYTHONPATH: {os.getenv('PYTHONPATH', 'Not set')}")
    print()
    
    # 2. Check if we're in the right directory
    print("📁 DIRECTORY STRUCTURE:")
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    print(f"Tests directory exists: {(current_dir / 'tests').exists()}")
    print(f"Requirements.txt exists: {(current_dir / 'requirements.txt').exists()}")
    print(f"App directory exists: {(current_dir / 'app').exists()}")
    
    if (current_dir / 'tests').exists():
        test_files = list((current_dir / 'tests').rglob('test_*.py'))
        print(f"Test files found: {len(test_files)}")
        for test_file in test_files[:5]:  # Show first 5
            print(f"  - {test_file.relative_to(current_dir)}")
        if len(test_files) > 5:
            print(f"  ... and {len(test_files) - 5} more")
    print()
    
    # 3. Check key dependencies
    print("📦 DEPENDENCY CHECK:")
    key_deps = ['pytest', 'factory-boy', 'flask', 'sqlalchemy', 'dependency-injector']
    for dep in key_deps:
        try:
            if dep == 'factory-boy':
                import factory
                print(f"✅ {dep}: {factory.__version__}")
            elif dep == 'dependency-injector':
                import dependency_injector
                print(f"✅ {dep}: {dependency_injector.__version__}")
            else:
                module = __import__(dep.replace('-', '_'))
                version = getattr(module, '__version__', 'unknown')
                print(f"✅ {dep}: {version}")
        except ImportError as e:
            print(f"❌ {dep}: NOT FOUND - {e}")
    print()
    
    # 4. Test discovery simulation
    print("🔍 PYTEST TEST DISCOVERY:")
    try:
        # Simulate the exact command used in the task
        cmd = ["python3", "-m", "pytest", "tests/", "--collect-only", "-q"]
        env = os.environ.copy()
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        env["FORCE_SQLITE_FOR_TESTS"] = "1"
        env["FLASK_ENV"] = "testing"
        
        print(f"Command: {' '.join(cmd)}")
        print("Environment additions:")
        print(f"  PYTEST_DISABLE_PLUGIN_AUTOLOAD: {env.get('PYTEST_DISABLE_PLUGIN_AUTOLOAD')}")
        print(f"  FORCE_SQLITE_FOR_TESTS: {env.get('FORCE_SQLITE_FOR_TESTS')}")
        print(f"  FLASK_ENV: {env.get('FLASK_ENV')}")
        print()
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
        print(f"Return code: {result.returncode}")
        print(f"STDOUT ({len(result.stdout)} chars):")
        print(result.stdout[:1000] + ("..." if len(result.stdout) > 1000 else ""))
        print(f"STDERR ({len(result.stderr)} chars):")
        print(result.stderr[:1000] + ("..." if len(result.stderr) > 1000 else ""))
        
    except subprocess.TimeoutExpired:
        print("❌ Test discovery timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Test discovery failed: {e}")
    print()
    
    # 5. Try importing key test modules
    print("🧪 TEST MODULE IMPORTS:")
    try:
        sys.path.insert(0, str(current_dir))
        import tests.conftest
        print("✅ tests.conftest imported successfully")
    except Exception as e:
        print(f"❌ tests.conftest import failed: {e}")
        
    try:
        from tests.unit import test_database
        print("✅ tests.unit.test_database imported successfully")
    except Exception as e:
        print(f"❌ tests.unit.test_database import failed: {e}")
    print()
    
    # 6. Check if we can create a temporary test
    print("🧪 TEMPORARY TEST EXECUTION:")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            junit_path = os.path.join(temp_dir, "junit.xml")
            cmd = ["python3", "-m", "pytest", "tests/", "-v", f"--junitxml={junit_path}", "--tb=short", "--maxfail=3"]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=60)
            print(f"Test execution return code: {result.returncode}")
            print(f"JUnit XML created: {os.path.exists(junit_path)}")
            if os.path.exists(junit_path):
                print(f"JUnit XML size: {os.path.getsize(junit_path)} bytes")
                
                # Parse JUnit XML to see what we got
                try:
                    import xml.etree.ElementTree as ET
                    tree = ET.parse(junit_path)
                    root = tree.getroot()
                    for ts in root.iter("testsuite"):
                        tests = ts.attrib.get("tests", "0")
                        failures = ts.attrib.get("failures", "0") 
                        errors = ts.attrib.get("errors", "0")
                        skipped = ts.attrib.get("skipped", "0")
                        print(f"JUnit XML summary: {tests} tests, {failures} failures, {errors} errors, {skipped} skipped")
                except Exception as e:
                    print(f"Could not parse JUnit XML: {e}")
            
            print("STDOUT preview:")
            print(result.stdout[:500] + ("..." if len(result.stdout) > 500 else ""))
            print("STDERR preview:")
            print(result.stderr[:500] + ("..." if len(result.stderr) > 500 else ""))
            
    except subprocess.TimeoutExpired:
        print("❌ Test execution timed out after 60 seconds")
    except Exception as e:
        print(f"❌ Test execution failed: {e}")

if __name__ == "__main__":
    debug_test_environment()
