from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.utils.database import DatabaseManager
from app.models import Base, TestRun, TestResult

analytics_bp = Blueprint('analytics', __name__)
logger = logging.getLogger(__name__)

@analytics_bp.route('/test-runs', methods=['POST'])
@login_required
def start_test_run():
    """Start a real test run using Celery background worker."""
    try:
        body = request.get_json(silent=True) or {}
        markers = body.get('markers')
        parallel = bool(body.get('parallel', True))

        # Try to get Celery app from Flask extensions
        celery_app = current_app.extensions.get('celery_app')
        if celery_app is None:
            # Fallback: try to import directly
            try:
                from app.celery_app import celery_app
                current_app.extensions['celery_app'] = celery_app
                logger.info("Successfully imported Celery app directly")
            except ImportError as e:
                logger.error(f"Could not import Celery app: {e}")
                return jsonify({
                    'error': 'celery_not_available', 
                    'detail': 'Celery worker not configured. Please set up Redis and Celery worker.',
                    'debug': str(e)
                }), 503

        # CRITICAL: Import test_tasks module to ensure task registration
        try:
            from app.tasks import test_tasks
            logger.info("Successfully imported test_tasks module for task registration")
        except ImportError as e:
            logger.error(f"Could not import test_tasks module: {e}")
            return jsonify({
                'error': 'test_tasks_not_available',
                'detail': 'Test tasks module could not be imported.',
                'debug': str(e)
            }), 503

        # Debug: Log available tasks
        logger.info(f"Celery app tasks: {list(celery_app.tasks.keys())}")
        
        # Try to enqueue via send_task to avoid relying on local task registration
        task_name = 'app.tasks.test_tasks.run_test_suite'
        logger.info(f"Starting test run with markers={markers}, parallel={parallel} using {task_name}")
        try:
            task = celery_app.send_task(task_name, kwargs={'markers': markers, 'parallel': parallel, 'triggered_by': 'admin'})
        except Exception as e:
            available_tasks = list(celery_app.tasks.keys())
            logger.error(f"Failed to enqueue {task_name}: {e}")
            return jsonify({
                'error': 'task_not_found',
                'detail': 'Test runner task not registered. Please check Celery worker setup.',
                'available_tasks': available_tasks,
                'test_tasks': [k for k in available_tasks if 'test' in k.lower()]
            }), 503
        logger.info(f"Task started with ID: {task.id}")
        
        return jsonify({
            'task_id': task.id,
            'message': 'Test run started successfully',
            'status': 'running'
        }), 202
        
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        logger.exception('Failed to start test run')
        return jsonify({
            'error': 'failed_to_start', 
            'detail': str(exc),
            'type': type(exc).__name__,
            'traceback': tb.split('\n')[-5:]  # Last 5 lines of traceback
        }), 500


@analytics_bp.route('/diagnose', methods=['POST'])
@login_required
def run_diagnostic():
    """Run comprehensive diagnostic of the test environment"""
    try:
        # Try Celery first, but fall back to direct execution
        try:
            celery_app = current_app.extensions.get('celery_app')
            if celery_app is None:
                from app.celery_app import celery_app
                current_app.extensions['celery_app'] = celery_app

            from app.tasks import diagnostic_tasks
            task_name = 'app.tasks.diagnostic_tasks.diagnose_test_environment'
            task = celery_app.send_task(task_name)
            
            return jsonify({
                'task_id': task.id,
                'message': 'Diagnostic started successfully (Celery)',
                'status': 'running'
            }), 202
            
        except Exception as celery_error:
            logger.warning(f"Celery diagnostic failed: {celery_error}, falling back to direct execution")
            
            # Fallback: Run diagnostic directly and return results immediately
            try:
                from app.tasks.diagnostic_tasks import diagnose_test_environment
                # Create a mock task object for the diagnostic function
                class MockTask:
                    def update_state(self, **kwargs):
                        pass
                
                mock_task = MockTask()
                # Run diagnostic directly (synchronously)
                results = diagnose_test_environment(mock_task)
                
                return jsonify({
                    'message': 'Diagnostic completed successfully (Direct)',
                    'status': 'completed',
                    'results': results,
                    'fallback_mode': True
                }), 200
                
            except Exception as direct_error:
                return jsonify({
                    'error': 'diagnostic_failed',
                    'celery_error': str(celery_error),
                    'direct_error': str(direct_error),
                    'detail': 'Both Celery and direct execution failed'
                }), 500
            
    except Exception as exc:
        logger.exception('Failed to start diagnostic')
        return jsonify({
            'error': 'failed_to_start_diagnostic', 
            'detail': str(exc)
        }), 500


@analytics_bp.route('/diagnose-direct', methods=['POST'])
@login_required
def run_diagnostic_direct():
    """Run diagnostic directly without Celery - returns results immediately"""
    import os
    import sys
    import subprocess
    import tempfile
    from datetime import datetime
    
    try:
        logger.info("🔍 STARTING DIRECT DIAGNOSTIC")
        logger.info(f"🔧 Current working directory: {os.getcwd()}")
        logger.info(f"🔧 Python version: {sys.version}")
        logger.info(f"🔧 User: {getattr(current_user, 'username', 'Unknown')}")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "mode": "direct_execution",
            "python_info": {},
            "environment": {},
            "directory_structure": {},
            "test_discovery": {},
            "import_tests": {},
            "pytest_execution": {}
        }
        
        # 1. Python and System Info
        results["python_info"] = {
            "version": sys.version,
            "executable": sys.executable,
            "platform": sys.platform,
            "cwd": os.getcwd(),
            "pythonpath": os.getenv('PYTHONPATH', 'Not set')
        }
        
        # 2. Environment Variables
        env_vars = [
            'FLASK_ENV', 'DATABASE_URL', 'REDIS_URL', 'PYTHON_VERSION',
            'FORCE_SQLITE_FOR_TESTS', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD'
        ]
        results["environment"] = {var: os.getenv(var, 'Not set') for var in env_vars}
        
        # 3. Directory Structure
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
        
        # 4. Test Discovery
        logger.info("🔍 Starting test discovery...")
        try:
            python_cmd = "python3" if os.system("which python3 > /dev/null 2>&1") == 0 else "python"
            cmd = [python_cmd, "-m", "pytest", "tests/", "--collect-only", "-q"]
            
            env = os.environ.copy()
            env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
            env["FORCE_SQLITE_FOR_TESTS"] = "1"
            env["FLASK_ENV"] = "testing"
            
            logger.info("🔧 Running pytest --collect-only...")
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            results["test_discovery"] = {
                "command": ' '.join(cmd),
                "return_code": proc.returncode,
                "stdout_preview": proc.stdout[:1000] if proc.stdout else "",
                "stderr_preview": proc.stderr[:1000] if proc.stderr else "",
            }
            
            if proc.stdout:
                discovered_tests = proc.stdout.count("::")
                results["test_discovery"]["discovered_test_count"] = discovered_tests
                
        except subprocess.TimeoutExpired:
            results["test_discovery"] = {"error": "Test discovery timed out after 10 seconds"}
            logger.error("❌ Test discovery timed out")
        except Exception as e:
            results["test_discovery"] = {"error": str(e)}
            logger.error(f"❌ Test discovery failed: {e}")
        
        # 5. Import Tests
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
        
        # 6. Quick pytest execution
        logger.info("🧪 Starting pytest execution...")
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                junit_path = os.path.join(temp_dir, "junit.xml")
                cmd = [python_cmd, "-m", "pytest", "tests/", "-v", f"--junitxml={junit_path}", 
                       "--tb=short", "--maxfail=3"]
                
                logger.info("🔧 Running pytest with limited tests...")
                proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=15)
                
                results["pytest_execution"] = {
                    "return_code": proc.returncode,
                    "junit_created": os.path.exists(junit_path),
                    "stdout_preview": proc.stdout[:2000] if proc.stdout else "",
                    "stderr_preview": proc.stderr[:2000] if proc.stderr else "",
                }
                
                if os.path.exists(junit_path):
                    results["pytest_execution"]["junit_size"] = os.path.getsize(junit_path)
                    
        except subprocess.TimeoutExpired:
            results["pytest_execution"] = {"error": "Pytest execution timed out after 15 seconds"}
            logger.error("❌ Pytest execution timed out")
        except Exception as e:
            results["pytest_execution"] = {"error": str(e)}
            logger.error(f"❌ Pytest execution failed: {e}")
        
        logger.info("✅ DIRECT DIAGNOSTIC COMPLETED")
        
        return jsonify({
            'message': 'Direct diagnostic completed successfully',
            'status': 'completed',
            'results': results
        }), 200
        
    except Exception as exc:
        logger.exception('Direct diagnostic failed')
        return jsonify({
            'error': 'diagnostic_failed', 
            'detail': str(exc),
            'type': type(exc).__name__
        }), 500


@analytics_bp.route('/test-runs', methods=['GET'])
@login_required
def list_test_runs():
    try:
        dm = DatabaseManager()
        with dm.get_session() as s:
            runs = s.query(TestRun).order_by(TestRun.started_at.desc()).limit(50).all()
            data = []
            for r in runs:
                data.append({
                    'id': r.id,
                    'status': r.status,
                    'total_tests': r.total_tests,
                    'passed_tests': r.passed_tests,
                    'failed_tests': r.failed_tests,
                    'skipped_tests': r.skipped_tests,
                    'execution_time_seconds': r.execution_time_seconds,
                    'started_at': r.started_at.isoformat()+'Z' if r.started_at else None,
                    'completed_at': r.completed_at.isoformat()+'Z' if r.completed_at else None,
                    'failure_reason': r.error_message,
                })
            return jsonify({'runs': data})
    except Exception as exc:
        logger.exception('Failed to list test runs')
        return jsonify({'error': 'failed_to_list', 'detail': str(exc)}), 500


@analytics_bp.route('/test-runs/<int:run_id>', methods=['GET'])
@login_required
def get_test_run(run_id: int):
    try:
        dm = DatabaseManager()
        with dm.get_session() as s:
            r = s.get(TestRun, run_id)
            if not r:
                return jsonify({'error': 'not_found'}), 404
            results = s.query(TestResult).filter(TestResult.run_id == run_id).limit(2000).all()
            return jsonify({
                'run': {
                    'id': r.id,
                    'status': r.status,
                    'total_tests': r.total_tests,
                    'passed_tests': r.passed_tests,
                    'failed_tests': r.failed_tests,
                    'skipped_tests': r.skipped_tests,
                    'execution_time_seconds': r.execution_time_seconds,
                    'started_at': r.started_at.isoformat()+'Z' if r.started_at else None,
                    'completed_at': r.completed_at.isoformat()+'Z' if r.completed_at else None,
                    'error_message': r.error_message,
                },
                'results': [
                    {
                        'test_name': tr.test_name,
                        'nodeid': tr.nodeid,
                        'module': tr.test_module,
                        'category': tr.test_category or 'other',
                        'status': tr.status,
                        'execution_time_seconds': tr.execution_time_seconds,
                        'failure_message': tr.failure_message,
                        'traceback_excerpt': tr.traceback_excerpt,
                    } for tr in results
                ]
            })
    except Exception as exc:
        logger.exception('Failed to get test run')
        return jsonify({'error': 'failed_to_get', 'detail': str(exc)}), 500

@analytics_bp.route('/dashboard/overview', methods=['GET'])
@login_required
def get_dashboard_overview():
    """Return high-level overview metrics for the dashboard."""
    try:
        dm = DatabaseManager()
        # Ensure tables exist (safe no-op if already created)
        try:
            Base.metadata.create_all(dm.engine)
        except Exception:
            pass
        since = datetime.utcnow() - timedelta(hours=24)
        with dm.get_session() as s:
            runs = s.query(TestRun).filter(TestRun.started_at >= since).order_by(TestRun.started_at.desc()).all()
            total_tests = sum(r.total_tests or 0 for r in runs) or 0
            total_passed = sum(r.passed_tests or 0 for r in runs) or 0
            total_failed = sum(r.failed_tests or 0 for r in runs) or 0
            avg_time = 0.0
            times = [r.execution_time_seconds or 0.0 for r in runs if (r.execution_time_seconds or 0.0) > 0]
            if times:
                avg_time = sum(times) / len(times)
            success_rate = 0
            if total_tests > 0:
                success_rate = round((total_passed / total_tests) * 100)
            summary = {
                'success_rate_24h': success_rate,
                'failed_tests_24h': int(total_failed),
                'avg_execution_time_seconds': round(avg_time, 2),
            }

            recent_runs: List[Dict[str, Any]] = [
                {
                    'run_id': r.id,
                    'name': f"Run {r.id}",
                    'status': r.status,
                    'total_tests': r.total_tests,
                    'passed_tests': r.passed_tests,
                    'failed_tests': r.failed_tests,
                    'skipped_tests': r.skipped_tests,
                    'execution_time_seconds': r.execution_time_seconds,
                    'started_at': r.started_at.isoformat() + 'Z',
                } for r in runs[:10]
            ]

        return jsonify({
            'summary': summary,
            'recent_runs': recent_runs,
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as exc:
        logger.exception("Failed to compute dashboard overview")
        return jsonify({'error': 'failed_to_compute_overview', 'detail': str(exc)}), 500


@analytics_bp.route('/dashboard/trends', methods=['GET'])
@login_required
def get_dashboard_trends():
    """Return trends over a period of days for charts."""
    try:
        days_param = request.args.get('days', default='7')
        try:
            days = max(1, min(90, int(days_param)))
        except ValueError:
            days = 7

        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days - 1)

        dm = DatabaseManager()
        try:
            Base.metadata.create_all(dm.engine)
        except Exception:
            pass
        trends = []
        with dm.get_session() as s:
            # Build a dict per date
            by_day = {}
            runs = s.query(TestRun).filter(TestRun.started_at >= datetime.combine(start_date, datetime.min.time())).all()
            for r in runs:
                d = r.started_at.date().isoformat()
                rec = by_day.setdefault(d, { 'total':0, 'passed':0, 'times':[] })
                rec['total'] += (r.total_tests or 0)
                rec['passed'] += (r.passed_tests or 0)
                if r.execution_time_seconds:
                    rec['times'].append(r.execution_time_seconds)
            for i in range(days):
                day = (start_date + timedelta(days=i)).isoformat()
                rec = by_day.get(day, { 'total':0, 'passed':0, 'times':[] })
                success = 0.0
                if rec['total'] > 0:
                    success = (rec['passed'] / rec['total']) * 100.0
                avg_time = round(sum(rec['times'])/len(rec['times']), 2) if rec['times'] else 0.0
                trends.append({ 'date': day, 'success_rate': round(success,2), 'avg_execution_time': avg_time })

        return jsonify({'trends': trends, 'range': {'start': start_date.isoformat(), 'end': end_date.isoformat()}})
    except Exception as exc:
        logger.exception("Failed to compute dashboard trends")
        return jsonify({'error': 'failed_to_compute_trends', 'detail': str(exc)}), 500


@analytics_bp.route('/dashboard/test-categories', methods=['GET'])
@login_required
def get_dashboard_test_categories():
    """Return category success rates for donut chart."""
    try:
        dm = DatabaseManager()
        try:
            Base.metadata.create_all(dm.engine)
        except Exception:
            pass
        since = datetime.utcnow() - timedelta(days=7)
        with dm.get_session() as s:
            rows = s.query(TestResult.test_category, TestResult.status).filter(
                TestResult.created_at >= since
            ).all()
            by_cat = {}
            for cat, status in rows:
                key = cat or 'other'
                rec = by_cat.setdefault(key, { 'total':0, 'passed':0 })
                rec['total'] += 1
                if status == 'passed':
                    rec['passed'] += 1
            categories = []
            for cat, rec in by_cat.items():
                rate = 0
                if rec['total'] > 0:
                    rate = round((rec['passed']/rec['total'])*100)
                categories.append({'category': cat, 'success_rate': rate})
        return jsonify({'categories': categories})
    except Exception as exc:
        logger.exception("Failed to compute dashboard categories")
        return jsonify({'error': 'failed_to_compute_categories', 'detail': str(exc)}), 500
