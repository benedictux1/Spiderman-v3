"""
Diagnostic API endpoints for system health monitoring and troubleshooting.
These endpoints provide comprehensive testing of all system components.
"""

from flask import Blueprint, jsonify, request
from app.celery_app import celery_app
import redis
import os
import psutil
import subprocess
import time
import logging
from datetime import datetime
from typing import Dict, Any

# Create blueprint
diagnostics = Blueprint('diagnostics', __name__)

# Logger for diagnostics
logger = logging.getLogger(__name__)

def safe_execute(func, default=None):
    """Safely execute a function and return result or error info"""
    try:
        return {'status': 'success', 'data': func()}
    except Exception as e:
        logger.error(f"Diagnostic function failed: {str(e)}")
        return {'status': 'error', 'error': str(e), 'data': default}

@diagnostics.route('/redis-test', methods=['POST'])
def test_redis_connectivity():
    """Test 1.1: Basic Redis Connection from Web Service"""
    def redis_test():
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            raise Exception("REDIS_URL environment variable not set")

        if redis_url.startswith('${{'):
            raise Exception(f"REDIS_URL not properly resolved: {redis_url}")

        # Test basic connectivity
        start_time = time.time()
        r = redis.from_url(redis_url)
        r.ping()
        response_time = time.time() - start_time

        # Test basic operations
        test_key = "diagnostic_test"
        r.set(test_key, "test_value", ex=60)  # Expires in 60 seconds
        value = r.get(test_key)
        r.delete(test_key)

        return {
            'redis_url_pattern': redis_url[:20] + '...' if len(redis_url) > 20 else redis_url,
            'connection': 'active',
            'response_time_ms': round(response_time * 1000, 2),
            'operations_test': 'passed',
            'redis_info': {
                'version': r.info().get('redis_version', 'unknown'),
                'connected_clients': r.info().get('connected_clients', 0),
                'used_memory_human': r.info().get('used_memory_human', 'unknown')
            }
        }

    result = safe_execute(redis_test)
    status_code = 200 if result['status'] == 'success' else 500
    return jsonify(result), status_code

@diagnostics.route('/celery-info', methods=['GET'])
def get_celery_info():
    """Test 1.2: Celery App Instance and Configuration Test"""
    def celery_info():
        broker_url = str(celery_app.conf.broker_url)
        result_backend = str(celery_app.conf.result_backend)

        return {
            'app_name': celery_app.main,
            'broker_url_pattern': broker_url[:30] + '...' if len(broker_url) > 30 else broker_url,
            'result_backend_pattern': result_backend[:30] + '...' if len(result_backend) > 30 else result_backend,
            'task_count': len(celery_app.tasks.keys()),
            'configuration': {
                'task_serializer': celery_app.conf.task_serializer,
                'result_serializer': celery_app.conf.result_serializer,
                'timezone': celery_app.conf.timezone,
                'worker_concurrency': celery_app.conf.worker_concurrency,
                'worker_pool': celery_app.conf.worker_pool
            },
            'tasks_available': sorted(list(celery_app.tasks.keys())),
            'test_tasks': [k for k in celery_app.tasks.keys() if 'test' in k.lower()],
            'ai_tasks': [k for k in celery_app.tasks.keys() if 'ai' in k.lower()]
        }

    result = safe_execute(celery_info)
    status_code = 200 if result['status'] == 'success' else 500
    return jsonify(result), status_code

@diagnostics.route('/worker-ping', methods=['POST'])
def test_worker_ping():
    """Test 1.3: Worker Heartbeat and Responsiveness Check"""
    def worker_ping():
        start_time = time.time()

        # Try to ping workers using Celery's control interface
        inspect = celery_app.control.inspect()

        # Get worker statistics
        stats = inspect.stats()
        active_tasks = inspect.active()
        registered_tasks = inspect.registered()

        if not stats:
            raise Exception("No workers responding to ping")

        response_time = time.time() - start_time

        worker_info = {}
        for worker_name, worker_stats in stats.items():
            worker_info[worker_name] = {
                'status': 'responsive',
                'pool': worker_stats.get('pool', {}).get('implementation', 'unknown'),
                'processes': worker_stats.get('pool', {}).get('processes', 0),
                'total_tasks': worker_stats.get('total', {}),
                'active_tasks': len(active_tasks.get(worker_name, [])),
                'registered_tasks': len(registered_tasks.get(worker_name, []))
            }

        return {
            'response_time_seconds': round(response_time, 3),
            'worker_count': len(stats),
            'workers': worker_info,
            'total_active_tasks': sum(len(tasks) for tasks in active_tasks.values()),
            'test_task_registered': any('test_tasks' in str(tasks) for tasks in registered_tasks.values())
        }

    result = safe_execute(worker_ping)
    status_code = 200 if result['status'] == 'success' else 500
    return jsonify(result), status_code

@diagnostics.route('/env-check', methods=['GET'])
def check_environment_variables():
    """Test 2.1: Environment Variable Resolution Check"""
    def env_check():
        critical_vars = {
            'REDIS_URL': os.getenv('REDIS_URL'),
            'DATABASE_URL': os.getenv('DATABASE_URL'),
            'FLASK_ENV': os.getenv('FLASK_ENV'),
            'FLASK_SECRET_KEY': os.getenv('FLASK_SECRET_KEY')
        }

        # Check for unresolved template variables
        unresolved = {}
        for key, value in critical_vars.items():
            if value and value.startswith('${{'):
                unresolved[key] = value

        # Mask sensitive information
        masked_vars = {}
        for key, value in critical_vars.items():
            if value:
                if key in ['REDIS_URL', 'DATABASE_URL']:
                    masked_vars[key] = value[:20] + '...' if len(value) > 20 else 'SET'
                elif key == 'FLASK_SECRET_KEY':
                    masked_vars[key] = 'SET' if value else 'NOT_SET'
                else:
                    masked_vars[key] = value
            else:
                masked_vars[key] = 'NOT_SET'

        return {
            'critical_vars': masked_vars,
            'unresolved_vars': unresolved,
            'environment_issues': len(unresolved) > 0,
            'flask_env': os.getenv('FLASK_ENV', 'unknown'),
            'total_env_vars': len(os.environ)
        }

    result = safe_execute(env_check)
    return jsonify(result), 200

@diagnostics.route('/resource-status', methods=['GET'])
def check_resource_status():
    """Test 3.1: System Resource Monitoring"""
    def resource_check():
        # Memory information
        memory = psutil.virtual_memory()

        # CPU information
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()

        # Disk information for current directory
        disk = psutil.disk_usage('/')

        return {
            'memory': {
                'total_mb': round(memory.total / 1024 / 1024, 2),
                'available_mb': round(memory.available / 1024 / 1024, 2),
                'percent_used': memory.percent,
                'status': 'warning' if memory.percent > 80 else 'healthy'
            },
            'cpu': {
                'percent_used': cpu_percent,
                'core_count': cpu_count,
                'status': 'warning' if cpu_percent > 80 else 'healthy'
            },
            'disk': {
                'total_gb': round(disk.total / 1024 / 1024 / 1024, 2),
                'free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
                'percent_used': round((disk.used / disk.total) * 100, 1),
                'status': 'warning' if (disk.used / disk.total) > 0.8 else 'healthy'
            },
            'overall_status': 'healthy'  # Could be computed based on individual statuses
        }

    result = safe_execute(resource_check, {
        'memory': {'status': 'unknown'},
        'cpu': {'status': 'unknown'},
        'disk': {'status': 'unknown'},
        'overall_status': 'unknown'
    })
    return jsonify(result), 200

@diagnostics.route('/queue-status', methods=['GET'])
def check_queue_status():
    """Test 3.2: Queue Status and Task Distribution Check"""
    def queue_check():
        inspect = celery_app.control.inspect()

        # Get active tasks
        active_tasks = inspect.active() or {}

        # Get scheduled tasks
        scheduled_tasks = inspect.scheduled() or {}

        # Get reserved tasks
        reserved_tasks = inspect.reserved() or {}

        # Try to get queue lengths (requires Redis access)
        try:
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                r = redis.from_url(redis_url)
                celery_queue_length = r.llen('celery')
            else:
                celery_queue_length = 'unknown'
        except Exception:
            celery_queue_length = 'unknown'

        total_active = sum(len(tasks) for tasks in active_tasks.values())
        total_scheduled = sum(len(tasks) for tasks in scheduled_tasks.values())
        total_reserved = sum(len(tasks) for tasks in reserved_tasks.values())

        return {
            'queue_lengths': {
                'celery_queue': celery_queue_length
            },
            'task_distribution': {
                'active_tasks': total_active,
                'scheduled_tasks': total_scheduled,
                'reserved_tasks': total_reserved
            },
            'workers': {
                worker: {
                    'active': len(active_tasks.get(worker, [])),
                    'scheduled': len(scheduled_tasks.get(worker, [])),
                    'reserved': len(reserved_tasks.get(worker, []))
                }
                for worker in set(
                    list(active_tasks.keys()) +
                    list(scheduled_tasks.keys()) +
                    list(reserved_tasks.keys())
                )
            },
            'status': 'healthy' if total_active < 100 else 'warning'  # Arbitrary threshold
        }

    result = safe_execute(queue_check)
    return jsonify(result), 200

@diagnostics.route('/test-serialization', methods=['POST'])
def test_task_serialization():
    """Test 2.2: Task Serialization and Protocol Compatibility"""
    def serialization_test():
        # Get test data from request
        test_data = request.get_json() or {'test': 'default_data'}

        # Try to serialize and send a simple task
        try:
            # Use a built-in Celery task for testing
            task = celery_app.send_task(
                'celery.ping',
                timeout=10
            )

            # Wait for result with timeout
            result = task.get(timeout=10)

            return {
                'serialization': 'success',
                'task_dispatch': 'success',
                'task_execution': 'success',
                'task_id': task.id,
                'result': result,
                'test_data_received': test_data
            }
        except Exception as e:
            return {
                'serialization': 'unknown',
                'task_dispatch': 'failed',
                'error': str(e),
                'test_data_received': test_data
            }

    result = safe_execute(serialization_test)
    status_code = 200 if result['status'] == 'success' else 500
    return jsonify(result), status_code

@diagnostics.route('/full-diagnostic', methods=['GET'])
def run_full_diagnostic():
    """Comprehensive diagnostic that runs all tests"""
    start_time = time.time()

    # Run all diagnostic tests
    tests = {
        'redis_connectivity': test_redis_connectivity(),
        'celery_info': get_celery_info(),
        'worker_ping': test_worker_ping(),
        'environment_check': check_environment_variables(),
        'resource_status': check_resource_status(),
        'queue_status': check_queue_status()
    }

    # Extract results and status codes
    results = {}
    overall_status = 'healthy'

    for test_name, (response, status_code) in tests.items():
        result_data = response.get_json()
        results[test_name] = {
            'status_code': status_code,
            'result': result_data
        }

        # Update overall status based on individual test results
        if status_code >= 500:
            overall_status = 'critical'
        elif status_code >= 400 and overall_status != 'critical':
            overall_status = 'degraded'
        elif status_code >= 300 and overall_status == 'healthy':
            overall_status = 'warning'

    execution_time = time.time() - start_time

    summary = {
        'timestamp': datetime.utcnow().isoformat(),
        'execution_time_seconds': round(execution_time, 2),
        'overall_status': overall_status,
        'test_results': results,
        'summary': {
            'tests_passed': sum(1 for r in results.values() if r['status_code'] < 300),
            'tests_failed': sum(1 for r in results.values() if r['status_code'] >= 400),
            'total_tests': len(results)
        }
    }

    status_code = 200 if overall_status in ['healthy', 'warning'] else 503
    return jsonify(summary), status_code