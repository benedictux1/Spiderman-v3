from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
import logging
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
