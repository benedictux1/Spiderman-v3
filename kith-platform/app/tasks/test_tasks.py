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
    dm = DatabaseManager()
    _ensure_tables(dm)

    with dm.get_session() as session:
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

    self.update_state(state=states.STARTED, meta={"run_id": run_id, "status": "running"})

    # Build pytest command
    with tempfile.TemporaryDirectory() as td:
        junit_path = os.path.join(td, "junit.xml")
        cmd = ["python3", "-m", "pytest", "-q", f"--junitxml={junit_path}"]
        # Disable external plugins for stability
        env = os.environ.copy()
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        if markers:
            # Combine markers with or logic: -m "m1 or m2"
            expr = " or ".join(markers)
            cmd += ["-m", expr]

        # Run pytest from the worker's repository root (Render sets cwd to /opt/render/project/src/kith-platform)
        proc = subprocess.run(cmd, cwd=os.getcwd(), env=env)

        total = passed = failed = skipped = 0
        duration_sum = 0.0
        results: list[TestResult] = []

        # Parse JUnit XML if exists
        if os.path.exists(junit_path):
            try:
                tree = ET.parse(junit_path)
                root = tree.getroot()
                # JUnit schema variants: testsuite or testsuites
                for ts in root.iter("testsuite"):
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
                        elif skipped_tag is not None:
                            status = "skipped"
                            skipped += 1
                        else:
                            passed += 1

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
            except Exception as e:
                # Fall back to aggregate only
                pass

    # Persist aggregate and details
    with dm.get_session() as session:
        run = session.get(TestRun, run_id)
        if run:
            run.status = "completed" if proc.returncode == 0 else "failed"
            run.total_tests = total
            run.passed_tests = passed
            run.failed_tests = failed
            run.skipped_tests = skipped
            run.execution_time_seconds = duration_sum
            run.completed_at = datetime.utcnow()
            if proc.returncode != 0 and failed == 0:
                run.error_message = "Test process returned non-zero exit code"
            for r in results:
                session.add(r)

    return {"run_id": run_id, "status": "completed" if proc.returncode == 0 else "failed"}


