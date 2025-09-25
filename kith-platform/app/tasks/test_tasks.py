import os
import tempfile
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional
from celery import states, Task
from app.celery_app import celery_app
from app.utils.database import DatabaseManager
from app.models import Base, TestRun, TestResult


def _ensure_tables(dm: DatabaseManager):
    try:
        Base.metadata.create_all(dm.engine)
    except Exception:
        # Best-effort; migrations should normally handle this
        pass


# Register task on the project Celery app to ensure proper discovery by the worker
@celery_app.task(bind=True, name='app.tasks.test_tasks.run_test_suite')
def run_test_suite(self: Task, markers: Optional[List[str]] = None, parallel: bool = True, triggered_by: str = "admin"):
    """Execute pytest, collect JUnit XML, and persist results to DB.

    Args:
        markers: Optional list of pytest markers to select subsets (e.g., ["api", "unit"]).
        parallel: Currently unused placeholder for future xdist usage.
        triggered_by: Who triggered the run.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔧 DEBUG: Starting test suite execution...")
    logger.info(f"🔧 DEBUG: Parameters - markers: {markers}, parallel: {parallel}, triggered_by: {triggered_by}")
    logger.info(f"🔧 DEBUG: Environment variables:")
    logger.info(f"  - DATABASE_URL: {os.getenv('DATABASE_URL')}")
    logger.info(f"  - FORCE_SQLITE_FOR_TESTS: {os.getenv('FORCE_SQLITE_FOR_TESTS')}")
    logger.info(f"  - FLASK_ENV: {os.getenv('FLASK_ENV')}")
    logger.info(f"  - PYTEST_DISABLE_PLUGIN_AUTOLOAD: {os.getenv('PYTEST_DISABLE_PLUGIN_AUTOLOAD')}")
    
    dm = DatabaseManager()
    logger.info("🔧 DEBUG: Database manager created")
    _ensure_tables(dm)
    logger.info("🔧 DEBUG: Database tables ensured")

    with dm.get_session() as session:
        logger.info("🔧 DEBUG: Creating test run record...")
        run = TestRun(
            status="running",
            triggered_by=triggered_by,
            trigger_type="manual",
            environment=os.getenv("FLASK_ENV", "production"),
            version=os.getenv("GIT_COMMIT", "unknown"),
            started_at=datetime.utcnow(),
        )
        session.add(run)
        session.flush()
        run_id = run.id
        logger.info(f"🔧 DEBUG: Test run created with ID: {run_id}")

    self.update_state(state=states.STARTED, meta={"run_id": run_id, "status": "running"})
    logger.info("🔧 DEBUG: Celery task state updated to STARTED")

    # Build pytest command
    with tempfile.TemporaryDirectory() as td:
        junit_path = os.path.join(td, "junit.xml")
        cmd = ["python3", "-m", "pytest", "-q", f"--junitxml={junit_path}"]
        logger.info(f"🔧 DEBUG: Base pytest command: {cmd}")
        
        # Disable external plugins for stability
        env = os.environ.copy()
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        env["FORCE_SQLITE_FOR_TESTS"] = "1"
        
        logger.info(f"🔧 DEBUG: Environment variables for pytest:")
        logger.info(f"  - PYTEST_DISABLE_PLUGIN_AUTOLOAD: {env.get('PYTEST_DISABLE_PLUGIN_AUTOLOAD')}")
        logger.info(f"  - FORCE_SQLITE_FOR_TESTS: {env.get('FORCE_SQLITE_FOR_TESTS')}")
        logger.info(f"  - DATABASE_URL: {env.get('DATABASE_URL')}")
        
        if markers:
            # Combine markers with or logic: -m "m1 or m2"
            expr = " or ".join(markers)
            cmd += ["-m", expr]
            logger.info(f"🔧 DEBUG: Added markers: {expr}")

        logger.info(f"🔧 DEBUG: Final pytest command: {cmd}")
        logger.info(f"🔧 DEBUG: Working directory: {os.getcwd()}")
        logger.info(f"🔧 DEBUG: JUnit XML path: {junit_path}")

        # Run pytest from the worker's repository root (Render sets cwd to /opt/render/project/src/kith-platform)
        logger.info("🔧 DEBUG: Executing pytest...")
        proc = subprocess.run(cmd, cwd=os.getcwd(), env=env, capture_output=True, text=True)
        
        logger.info(f"🔧 DEBUG: Pytest completed with return code: {proc.returncode}")
        logger.info(f"🔧 DEBUG: stdout length: {len(proc.stdout)} characters")
        logger.info(f"🔧 DEBUG: stderr length: {len(proc.stderr)} characters")
        
        if proc.stdout:
            logger.info(f"🔧 DEBUG: stdout preview: {proc.stdout[:500]}...")
        if proc.stderr:
            logger.info(f"🔧 DEBUG: stderr preview: {proc.stderr[:500]}...")

        total = passed = failed = skipped = 0
        duration_sum = 0.0
        results: list[TestResult] = []

        # Parse JUnit XML if exists
        logger.info(f"🔧 DEBUG: Checking for JUnit XML at: {junit_path}")
        if os.path.exists(junit_path):
            logger.info("🔧 DEBUG: JUnit XML found, parsing...")
            try:
                tree = ET.parse(junit_path)
                root = tree.getroot()
                logger.info(f"🔧 DEBUG: JUnit XML root tag: {root.tag}")
                
                # JUnit schema variants: testsuite or testsuites
                for ts in root.iter("testsuite"):
                    logger.info(f"🔧 DEBUG: Found testsuite with {len(list(ts.iter('testcase')))} test cases")
                    for tc in ts.iter("testcase"):
                        total += 1
                        name = tc.attrib.get("name", "")
                        classname = tc.attrib.get("classname", "")
                        time_s = float(tc.attrib.get("time", 0.0) or 0.0)
                        duration_sum += time_s
                        status = "passed"
                        failure_message = None
                        traceback_excerpt = None
                        category = None

                        # Status detection
                        failure = tc.find("failure")
                        skipped_tag = tc.find("skipped")
                        if failure is not None:
                            status = "failed"
                            failed += 1
                            failure_message = failure.attrib.get("message") or (failure.text or "").strip()[:2000]
                            traceback_excerpt = (failure.text or "").strip()[:4000]
                            logger.info(f"🔧 DEBUG: Test failed: {name} - {failure_message[:100]}...")
                        elif skipped_tag is not None:
                            status = "skipped"
                            skipped += 1
                            logger.info(f"🔧 DEBUG: Test skipped: {name}")
                        else:
                            passed += 1
                            logger.info(f"🔧 DEBUG: Test passed: {name}")

                        # Derive category from classname or markers in name (best effort)
                        lname = (name or "").lower()
                        if "health" in lname:
                            category = "health_check"
                        elif "component" in lname:
                            category = "component"
                        elif "integration" in lname:
                            category = "integration"
                        elif "performance" in lname:
                            category = "performance"

                        results.append(TestResult(
                            run_id=run_id,
                            test_name=name,
                            nodeid=f"{classname}::{name}" if classname else name,
                            test_module=classname,
                            test_category=category,
                            status=status,
                            execution_time_seconds=time_s,
                            failure_message=failure_message,
                            traceback_excerpt=traceback_excerpt,
                        ))
                
                logger.info(f"🔧 DEBUG: Parsed {total} tests: {passed} passed, {failed} failed, {skipped} skipped")
            except Exception as e:
                logger.error(f"❌ JUnit XML parsing error: {e}")
                logger.error(f"🔧 DEBUG: Error type: {type(e).__name__}")
                logger.error(f"🔧 DEBUG: Error details: {str(e)}")
                # Fall back to aggregate only
                pass
        else:
            logger.warning("⚠️ JUnit XML not found, using subprocess return code only")

    # Persist aggregate and details
    logger.info("🔧 DEBUG: Persisting test results to database...")
    with dm.get_session() as session:
        run = session.get(TestRun, run_id)
        if run:
            final_status = "completed" if proc.returncode == 0 else "failed"
            run.status = final_status
            run.total_tests = total
            run.passed_tests = passed
            run.failed_tests = failed
            run.skipped_tests = skipped
            run.execution_time_seconds = duration_sum
            run.completed_at = datetime.utcnow()
            
            logger.info(f"🔧 DEBUG: Final test results: {total} total, {passed} passed, {failed} failed, {skipped} skipped")
            logger.info(f"🔧 DEBUG: Pytest return code: {proc.returncode}")
            logger.info(f"🔧 DEBUG: Final status: {final_status}")
            
            if proc.returncode != 0 and failed == 0:
                run.error_message = "Test process returned non-zero exit code"
                logger.warning("⚠️ Test process returned non-zero exit code but no individual test failures detected")
            
            logger.info(f"🔧 DEBUG: Adding {len(results)} individual test results...")
            for r in results:
                session.add(r)
            
            logger.info("✅ Test results persisted to database")

    result = {"run_id": run_id, "status": "completed" if proc.returncode == 0 else "failed"}
    logger.info(f"🔧 DEBUG: Returning result: {result}")
    return result


