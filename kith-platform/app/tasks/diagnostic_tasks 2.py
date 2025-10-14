"""
Diagnostic tasks to help understand the Render environment
"""
import os
import sys
import subprocess
import tempfile
from datetime import datetime
from app.celery_app import celery_app
from app.utils.database import DatabaseManager
from app.models import TestRun
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='app.tasks.diagnostic_tasks.diagnose_test_environment')
def diagnose_test_environment(self):
    """Comprehensive diagnostic of the test environment"""
    
    logger.info("🔍 STARTING COMPREHENSIVE TEST ENVIRONMENT DIAGNOSIS")
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "python_info": {},
        "environment": {},
        "directory_structure": {},
        "test_discovery": {},
        "import_tests": {},
        "pytest_execution": {}
    }
    
    # 1. Python and System Info
    logger.info("📊 Gathering Python and system information...")
    results["python_info"] = {
        "version": sys.version,
        "executable": sys.executable,
        "platform": sys.platform,
        "cwd": os.getcwd(),
        "pythonpath": os.getenv('PYTHONPATH', 'Not set')
    }
    
    # 2. Environment Variables
    logger.info("🔧 Checking environment variables...")
    env_vars = [
        'FLASK_ENV', 'DATABASE_URL', 'REDIS_URL', 'PYTHON_VERSION',
        'FORCE_SQLITE_FOR_TESTS', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD'
    ]
    results["environment"] = {var: os.getenv(var, 'Not set') for var in env_vars}
    
    # 3. Directory Structure
    logger.info("📁 Analyzing directory structure...")
    cwd = os.getcwd()
    results["directory_structure"] = {
        "current_directory": cwd,
        "tests_exists": os.path.exists(os.path.join(cwd, "tests")),
        "requirements_exists": os.path.exists(os.path.join(cwd, "requirements.txt")),
        "app_exists": os.path.exists(os.path.join(cwd, "app")),
    }
    
    # Count test files
    test_files = []
    if os.path.exists(os.path.join(cwd, "tests")):
        for root, dirs, files in os.walk(os.path.join(cwd, "tests")):
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    test_files.append(os.path.relpath(os.path.join(root, file), cwd))
    
    results["directory_structure"]["test_files"] = test_files
    results["directory_structure"]["test_file_count"] = len(test_files)
    
    # 4. Test Discovery with pytest
    logger.info("🔍 Testing pytest discovery...")
    try:
        # Use the same command as the test task
        python_cmd = "python3" if os.system("which python3 > /dev/null 2>&1") == 0 else "python"
        cmd = [python_cmd, "-m", "pytest", "tests/", "--collect-only", "-q"]
        
        env = os.environ.copy()
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        env["FORCE_SQLITE_FOR_TESTS"] = "1"
        env["FLASK_ENV"] = "testing"
        
        logger.info(f"Running discovery command: {' '.join(cmd)}")
        
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        results["test_discovery"] = {
            "command": ' '.join(cmd),
            "return_code": proc.returncode,
            "stdout_length": len(proc.stdout),
            "stderr_length": len(proc.stderr),
            "stdout_preview": proc.stdout[:1000] if proc.stdout else "",
            "stderr_preview": proc.stderr[:1000] if proc.stderr else "",
            "timed_out": False
        }
        
        # Count discovered tests
        if proc.stdout:
            discovered_tests = proc.stdout.count("::")
            results["test_discovery"]["discovered_test_count"] = discovered_tests
        
    except subprocess.TimeoutExpired:
        results["test_discovery"] = {
            "error": "Test discovery timed out after 30 seconds",
            "timed_out": True
        }
    except Exception as e:
        results["test_discovery"] = {
            "error": f"Test discovery failed: {str(e)}",
            "exception_type": type(e).__name__
        }
    
    # 5. Import Tests
    logger.info("🧪 Testing critical imports...")
    import_tests = {}
    
    critical_modules = [
        "tests.conftest",
        "tests.unit.test_database", 
        "tests.unit.test_monitoring",
        "app.utils.dependencies",
        "app.services.contact_service",
        "dependency_injector",
        "factory"
    ]
    
    for module in critical_modules:
        try:
            __import__(module)
            import_tests[module] = {"status": "success", "error": None}
        except Exception as e:
            import_tests[module] = {"status": "failed", "error": str(e), "type": type(e).__name__}
    
    results["import_tests"] = import_tests
    
    # 6. Quick pytest execution test
    logger.info("🧪 Testing quick pytest execution...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            junit_path = os.path.join(temp_dir, "junit.xml")
            cmd = [python_cmd, "-m", "pytest", "tests/", "-v", f"--junitxml={junit_path}", 
                   "--tb=short", "--maxfail=3"]
            
            proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=60)
            
            results["pytest_execution"] = {
                "return_code": proc.returncode,
                "junit_created": os.path.exists(junit_path),
                "stdout_preview": proc.stdout[:1000] if proc.stdout else "",
                "stderr_preview": proc.stderr[:1000] if proc.stderr else "",
                "timed_out": False
            }
            
            if os.path.exists(junit_path):
                results["pytest_execution"]["junit_size"] = os.path.getsize(junit_path)
                
                # Try to parse JUnit XML
                try:
                    import xml.etree.ElementTree as ET
                    tree = ET.parse(junit_path)
                    root = tree.getroot()
                    for ts in root.iter("testsuite"):
                        results["pytest_execution"]["junit_summary"] = {
                            "tests": ts.attrib.get("tests", "0"),
                            "failures": ts.attrib.get("failures", "0"),
                            "errors": ts.attrib.get("errors", "0"),
                            "skipped": ts.attrib.get("skipped", "0")
                        }
                        break
                except Exception as e:
                    results["pytest_execution"]["junit_parse_error"] = str(e)
            
    except subprocess.TimeoutExpired:
        results["pytest_execution"] = {"error": "Pytest execution timed out", "timed_out": True}
    except Exception as e:
        results["pytest_execution"] = {"error": str(e), "exception_type": type(e).__name__}
    
    # Store results in database
    try:
        dm = DatabaseManager()
        dm.initialize()
        with dm.get_session() as session:
            # Create a diagnostic test run record
            run = TestRun(
                status="diagnostic",
                triggered_by="diagnostic_task",
                trigger_type="diagnostic",
                environment=os.getenv("FLASK_ENV", "production"),
                version=os.getenv("GIT_COMMIT", "unknown"),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                total_tests=results.get("test_discovery", {}).get("discovered_test_count", 0),
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                execution_time_seconds=0,
                error_message=f"Diagnostic results: {len(import_tests)} imports tested"
            )
            session.add(run)
            session.commit()
            
            results["database_storage"] = {"status": "success", "run_id": run.id}
            
    except Exception as e:
        results["database_storage"] = {"status": "failed", "error": str(e)}
    
    logger.info("✅ DIAGNOSTIC COMPLETED")
    logger.info(f"📊 Summary: {results['directory_structure']['test_file_count']} test files found")
    logger.info(f"📊 Test discovery: {results.get('test_discovery', {}).get('discovered_test_count', 'unknown')} tests")
    logger.info(f"📊 Import tests: {sum(1 for t in import_tests.values() if t['status'] == 'success')}/{len(import_tests)} successful")
    
    return results
