# Comprehensive Diagnostic Testing Framework
## Celery Task Execution and 503 Error Root Cause Analysis

### Executive Summary
This framework provides a systematic approach to diagnose the root causes of 503 errors and task failures in the Kith Platform's Celery-based task execution system. While the investigation document identified Redis URL configuration as a likely cause, this framework goes beyond that to identify ALL potential failure modes.

### System Architecture Overview
- **Web Service**: Flask application serving API endpoints (`kith-platform` on Render)
- **Worker Service**: Celery worker process (`Spiderman-v3-1` on Render)
- **Message Broker**: Redis (internal Render Redis service)
- **Database**: PostgreSQL (for test results persistence)
- **Task Flow**: Web API → Redis → Celery Worker → Database → Response

---

## Diagnostic Test Hierarchy
### Tests ordered from most likely to least likely causes, based on system architecture and failure patterns

## TIER 1: Critical Infrastructure (Most Likely)
*Tests that address fundamental connectivity and configuration issues*

### 1.1 Redis Broker Connectivity
**Problem**: Web service cannot reach Redis broker
**Symptoms**: 503 errors, `send_task` exceptions
**Priority**: CRITICAL

#### Automated Tests:
```bash
# Test 1.1.1: Basic Redis Connection from Web Service
curl -X POST https://<web-service>/api/diagnostics/redis-test
# Expected: 200 with connection status

# Test 1.1.2: Redis URL Resolution Check
curl -X GET https://<web-service>/api/diagnostics/config
# Expected: Shows resolved REDIS_URL (first 20 chars for security)

# Test 1.1.3: Redis Ping Test
redis-cli -u $REDIS_URL ping
# Expected: PONG
```

#### Manual Verification:
```bash
# Verify REDIS_URL is set on web service
render env get -s kith-platform | grep REDIS_URL

# Test Redis connectivity from worker (should work)
render logs -s Spiderman-v3-1 --tail 100 | grep -i redis

# Test Redis connectivity from web service
render logs -s kith-platform --tail 100 | grep -i redis
```

### 1.2 Service Identity and Routing
**Problem**: Admin UI hitting wrong service or suspended service
**Symptoms**: 503 errors, task registry mismatches
**Priority**: CRITICAL

#### Automated Tests:
```bash
# Test 1.2.1: Service Health and Identity Check
curl -X GET https://<your-admin-url>/health
# Expected: 200 with service name "kith-platform"

# Test 1.2.2: Service Status Verification
render services list
# Expected: kith-platform = active, others = suspended

# Test 1.2.3: Celery App Instance Test
curl -X GET https://<web-service>/api/diagnostics/celery-info
# Expected: Shows Celery app name, broker URL pattern
```

### 1.3 Worker Process Health
**Problem**: Worker not running, crashed, or in bad state
**Symptoms**: Tasks hang indefinitely, no task processing
**Priority**: CRITICAL

#### Automated Tests:
```bash
# Test 1.3.1: Worker Heartbeat Check
curl -X POST https://<web-service>/api/diagnostics/worker-ping
# Expected: Worker responds within 5 seconds

# Test 1.3.2: Worker Task Registry Check
curl -X GET https://<web-service>/api/diagnostics/worker-tasks
# Expected: Lists all registered tasks including test_tasks
```

#### Manual Verification:
```bash
# Check worker is running and ready
render logs -s Spiderman-v3-1 --tail 50 | grep -E "(ready|connected|mingle)"

# Check worker resource usage
render metrics -s Spiderman-v3-1 --period 1h
```

---

## TIER 2: Configuration and Protocol Issues (Likely)

### 2.1 Environment Variable Resolution
**Problem**: Environment variables not properly resolved or interpolated
**Symptoms**: Redis URL contains `${{...}}`, connection failures
**Priority**: HIGH

#### Automated Tests:
```bash
# Test 2.1.1: Environment Variable Dump
curl -X GET https://<web-service>/api/diagnostics/env-check
# Expected: Shows all critical env vars resolved properly

# Test 2.1.2: Redis URL Validation
curl -X POST https://<web-service>/api/diagnostics/redis-url-test
# Expected: Validates URL format and reachability
```

### 2.2 Task Serialization and Protocol Compatibility
**Problem**: Version mismatches, serialization issues between services
**Symptoms**: Tasks accepted but fail to execute, serialization errors
**Priority**: HIGH

#### Automated Tests:
```bash
# Test 2.2.1: Basic Task Serialization Test
curl -X POST https://<web-service>/api/diagnostics/test-serialization \
  -H "Content-Type: application/json" \
  -d '{"test_data": {"complex": "object", "numbers": [1,2,3]}}'
# Expected: Task completes successfully with data round-trip

# Test 2.2.2: Task Protocol Compatibility
curl -X POST https://<web-service>/api/diagnostics/protocol-test
# Expected: Tests all supported content types and serializers
```

### 2.3 Database Connectivity from Worker
**Problem**: Worker can receive tasks but fails during database operations
**Symptoms**: Tasks start but fail during execution, DB connection errors
**Priority**: HIGH

#### Automated Tests:
```bash
# Test 2.3.1: Database Connection from Worker
curl -X POST https://<web-service>/api/diagnostics/worker-db-test
# Expected: Worker successfully connects to DB and runs query

# Test 2.3.2: Database Schema Validation
curl -X POST https://<web-service>/api/diagnostics/db-schema-test
# Expected: All required tables exist with correct schema
```

---

## TIER 3: Resource and Performance Issues (Moderate Likelihood)

### 3.1 Memory and Resource Constraints
**Problem**: Worker OOM, resource exhaustion
**Symptoms**: Tasks killed mid-execution, worker restarts
**Priority**: MODERATE

#### Automated Tests:
```bash
# Test 3.1.1: Memory Usage Test
curl -X POST https://<web-service>/api/diagnostics/memory-test
# Expected: Shows current memory usage, triggers memory-intensive task

# Test 3.1.2: Resource Limits Check
curl -X GET https://<web-service>/api/diagnostics/resource-limits
# Expected: Shows configured limits vs current usage
```

#### Manual Verification:
```bash
# Check memory usage trends
render metrics -s Spiderman-v3-1 --metric memory --period 6h

# Check for OOM kills in logs
render logs -s Spiderman-v3-1 --tail 500 | grep -E "(killed|oom|memory)"
```

### 3.2 Queue and Task Routing
**Problem**: Tasks routed to wrong queue or queue overflow
**Symptoms**: Tasks appear to start but never execute
**Priority**: MODERATE

#### Automated Tests:
```bash
# Test 3.2.1: Queue Inspection
curl -X GET https://<web-service>/api/diagnostics/queue-status
# Expected: Shows active queues, pending tasks, worker assignments

# Test 3.2.2: Task Routing Test
curl -X POST https://<web-service>/api/diagnostics/routing-test
# Expected: Confirms tasks route to correct worker and queue
```

### 3.3 Network and DNS Resolution
**Problem**: Intermittent network issues, DNS resolution failures
**Symptoms**: Sporadic failures, timeouts
**Priority**: MODERATE

#### Automated Tests:
```bash
# Test 3.3.1: Network Connectivity Between Services
curl -X POST https://<web-service>/api/diagnostics/network-test
# Expected: Tests connectivity to Redis, Database, and worker

# Test 3.3.2: DNS Resolution Check
curl -X GET https://<web-service>/api/diagnostics/dns-test
# Expected: Validates DNS resolution for all service dependencies
```

---

## TIER 4: Edge Cases and Advanced Issues (Less Likely)

### 4.1 Concurrency and Race Conditions
**Problem**: Race conditions in task execution, concurrent access issues
**Symptoms**: Inconsistent behavior, data corruption
**Priority**: LOW

#### Automated Tests:
```bash
# Test 4.1.1: Concurrent Task Execution Test
curl -X POST https://<web-service>/api/diagnostics/concurrency-test \
  -H "Content-Type: application/json" \
  -d '{"concurrent_tasks": 5, "task_duration": 10}'
# Expected: All tasks complete without interference

# Test 4.1.2: Database Lock Test
curl -X POST https://<web-service>/api/diagnostics/db-lock-test
# Expected: Tests database locking behavior under concurrent access
```

### 4.2 Task Timeout and Cleanup
**Problem**: Tasks hanging beyond time limits, zombie processes
**Symptoms**: Worker becomes unresponsive, tasks never complete
**Priority**: LOW

#### Automated Tests:
```bash
# Test 4.2.1: Task Timeout Behavior
curl -X POST https://<web-service>/api/diagnostics/timeout-test \
  -H "Content-Type: application/json" \
  -d '{"timeout_seconds": 30}'
# Expected: Task properly times out and cleans up

# Test 4.2.2: Process Cleanup Test
curl -X GET https://<web-service>/api/diagnostics/process-status
# Expected: No zombie processes, proper cleanup after task completion
```

### 4.3 Authentication and Permissions
**Problem**: Service authentication issues, permission denied errors
**Symptoms**: Auth failures in logs, service-to-service communication issues
**Priority**: LOW

#### Automated Tests:
```bash
# Test 4.3.1: Service Authentication Test
curl -X POST https://<web-service>/api/diagnostics/auth-test
# Expected: All service-to-service auth mechanisms working

# Test 4.3.2: Permission Validation
curl -X GET https://<web-service>/api/diagnostics/permissions
# Expected: All required permissions are granted
```

---

## Isolation Testing Procedures

### Layer Isolation Tests
*These tests isolate problems to specific system layers*

#### 4.4.1 Broker Isolation Test
```bash
# Test direct broker functionality bypassing application logic
redis-cli -u $REDIS_URL
> LPUSH test_queue '{"test": "message"}'
> BRPOP test_queue 5
# Expected: Message successfully queued and retrieved
```

#### 4.4.2 Database Isolation Test
```bash
# Test direct database connectivity bypassing ORM
psql $DATABASE_URL -c "SELECT COUNT(*) FROM test_runs;"
# Expected: Query executes successfully
```

#### 4.4.3 Worker Isolation Test
```bash
# Test worker functionality without web service involvement
celery -A app.celery_app.celery_app call app.tasks.test_tasks.run_test_suite
# Expected: Task executes directly on worker
```

#### 4.4.4 Application Logic Isolation Test
```bash
# Test application logic without external dependencies
curl -X POST https://<web-service>/api/diagnostics/logic-test
# Expected: Core business logic works without external calls
```

---

## Automated Test Implementation

### Diagnostic API Endpoints
*These endpoints should be added to the web service for automated testing*

```python
# File: /kith-platform/app/api/diagnostics.py

from flask import Blueprint, jsonify, request
from app.celery_app import celery_app
import redis
import os
import psutil
import subprocess

diagnostics = Blueprint('diagnostics', __name__)

@diagnostics.route('/redis-test', methods=['POST'])
def test_redis_connectivity():
    """Test 1.1.1: Basic Redis Connection"""
    try:
        redis_url = os.getenv('REDIS_URL')
        r = redis.from_url(redis_url)
        r.ping()
        return jsonify({
            'status': 'success',
            'redis_url_pattern': redis_url[:20] + '...' if redis_url else None,
            'connection': 'active'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'redis_url_pattern': redis_url[:20] + '...' if redis_url else None
        }), 500

@diagnostics.route('/celery-info', methods=['GET'])
def get_celery_info():
    """Test 1.2.3: Celery App Instance Test"""
    try:
        return jsonify({
            'app_name': celery_app.main,
            'broker_url_pattern': str(celery_app.conf.broker_url)[:30] + '...',
            'task_count': len(celery_app.tasks.keys()),
            'tasks_available': list(celery_app.tasks.keys())[:10],  # Limit for readability
            'test_tasks': [k for k in celery_app.tasks.keys() if 'test' in k.lower()]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@diagnostics.route('/worker-ping', methods=['POST'])
def test_worker_ping():
    """Test 1.3.1: Worker Heartbeat Check"""
    try:
        # Send a simple task to test worker responsiveness
        task = celery_app.send_task('celery.ping', timeout=5)
        result = task.get(timeout=5)
        return jsonify({
            'status': 'success',
            'worker_response_time': '< 5s',
            'worker_status': 'responsive'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'worker_status': 'unresponsive'
        }), 500

# Add more diagnostic endpoints following the same pattern...
```

### Command-Line Diagnostic Scripts

#### Primary Diagnostic Script
```bash
#!/bin/bash
# File: /kith-platform/scripts/diagnose_system.sh

echo "=== KITH PLATFORM DIAGNOSTIC FRAMEWORK ==="
echo "Timestamp: $(date)"
echo ""

# Configuration
WEB_SERVICE_URL="https://kith-platform-xxx.onrender.com"  # Replace with actual URL
REDIS_URL=${REDIS_URL:-"redis://localhost:6379/0"}

# TIER 1 TESTS
echo "=== TIER 1: CRITICAL INFRASTRUCTURE ==="

echo "1.1 Testing Redis Broker Connectivity..."
if curl -s -f "$WEB_SERVICE_URL/api/diagnostics/redis-test" > /tmp/redis_test.json; then
    echo "✅ Redis connectivity test passed"
    cat /tmp/redis_test.json | jq '.redis_url_pattern'
else
    echo "❌ Redis connectivity test FAILED"
    echo "   This is likely the root cause of 503 errors"
    cat /tmp/redis_test.json 2>/dev/null || echo "   No response from diagnostic endpoint"
fi

echo ""
echo "1.2 Testing Service Identity..."
if curl -s -f "$WEB_SERVICE_URL/health" > /tmp/health.json; then
    echo "✅ Service health check passed"
    cat /tmp/health.json | jq '.service_name'
else
    echo "❌ Service health check FAILED"
    echo "   Web service may be down or wrong URL"
fi

echo ""
echo "1.3 Testing Worker Health..."
if curl -s -f "$WEB_SERVICE_URL/api/diagnostics/worker-ping" > /tmp/worker_ping.json; then
    echo "✅ Worker ping test passed"
    cat /tmp/worker_ping.json | jq '.worker_status'
else
    echo "❌ Worker ping test FAILED"
    echo "   Worker may be down or unresponsive"
    cat /tmp/worker_ping.json 2>/dev/null || echo "   No response from diagnostic endpoint"
fi

# TIER 2 TESTS
echo ""
echo "=== TIER 2: CONFIGURATION AND PROTOCOL ==="

echo "2.1 Testing Environment Variables..."
if curl -s -f "$WEB_SERVICE_URL/api/diagnostics/env-check" > /tmp/env_check.json; then
    echo "✅ Environment variables test passed"
    cat /tmp/env_check.json | jq '.critical_vars'
else
    echo "⚠️  Environment variables test failed or endpoint unavailable"
fi

echo "2.2 Testing Task Serialization..."
if curl -s -f -X POST "$WEB_SERVICE_URL/api/diagnostics/test-serialization" \
    -H "Content-Type: application/json" \
    -d '{"test_data": {"complex": "object", "numbers": [1,2,3]}}' > /tmp/serialization.json; then
    echo "✅ Task serialization test passed"
else
    echo "⚠️  Task serialization test failed"
    cat /tmp/serialization.json 2>/dev/null
fi

# Continue with additional tiers as needed...

echo ""
echo "=== DIAGNOSTIC SUMMARY ==="
echo "Check the results above to identify the root cause."
echo "Focus on any ❌ FAILED tests first, as they indicate critical issues."
echo ""
echo "Next steps:"
echo "1. If Redis connectivity failed: Check REDIS_URL environment variable"
echo "2. If service health failed: Verify the web service URL and status"
echo "3. If worker ping failed: Check worker service status and logs"
echo ""
echo "For detailed investigation, run individual diagnostic commands:"
echo "  curl $WEB_SERVICE_URL/api/diagnostics/redis-test"
echo "  curl $WEB_SERVICE_URL/api/diagnostics/celery-info"
echo "  render logs -s kith-platform --tail 100"
echo "  render logs -s Spiderman-v3-1 --tail 100"
```

---

## Monitoring and Logging Strategy

### 5.1 Real-time Monitoring Setup

#### Application Performance Monitoring
```python
# File: /kith-platform/app/utils/monitoring.py

import logging
import time
import functools
from flask import g
from app.celery_app import celery_app

# Custom logger for diagnostics
diagnostic_logger = logging.getLogger('diagnostics')
diagnostic_logger.setLevel(logging.INFO)

# File handler for diagnostic logs
handler = logging.FileHandler('/tmp/kith_diagnostics.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
diagnostic_logger.addHandler(handler)

def monitor_task_execution(func):
    """Decorator to monitor task execution performance"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        task_name = func.__name__

        try:
            diagnostic_logger.info(f"Task {task_name} started")
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            diagnostic_logger.info(f"Task {task_name} completed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            diagnostic_logger.error(f"Task {task_name} failed after {execution_time:.2f}s: {str(e)}")
            raise
    return wrapper

def monitor_redis_operations(func):
    """Decorator to monitor Redis operations"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        operation = func.__name__

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            diagnostic_logger.info(f"Redis {operation} completed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            diagnostic_logger.error(f"Redis {operation} failed after {execution_time:.3f}s: {str(e)}")
            raise
    return wrapper
```

### 5.2 Health Check Endpoints

```python
# File: /kith-platform/app/api/health.py

from flask import Blueprint, jsonify
from app.celery_app import celery_app
import redis
import os
import psutil
from datetime import datetime

health = Blueprint('health', __name__)

@health.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        'timestamp': datetime.utcnow().isoformat(),
        'service_name': 'kith-platform',
        'status': 'healthy',
        'checks': {}
    }

    # Redis connectivity check
    try:
        redis_url = os.getenv('REDIS_URL')
        r = redis.from_url(redis_url)
        r.ping()
        health_status['checks']['redis'] = {'status': 'healthy', 'response_time': '< 100ms'}
    except Exception as e:
        health_status['checks']['redis'] = {'status': 'unhealthy', 'error': str(e)}
        health_status['status'] = 'degraded'

    # Celery worker check
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        if active_workers:
            health_status['checks']['celery_workers'] = {
                'status': 'healthy',
                'worker_count': len(active_workers),
                'workers': list(active_workers.keys())
            }
        else:
            health_status['checks']['celery_workers'] = {'status': 'unhealthy', 'error': 'No active workers'}
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['checks']['celery_workers'] = {'status': 'unhealthy', 'error': str(e)}
        health_status['status'] = 'degraded'

    # System resources check
    try:
        memory_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent(interval=1)
        health_status['checks']['system_resources'] = {
            'status': 'healthy' if memory_percent < 90 and cpu_percent < 90 else 'warning',
            'memory_usage': f"{memory_percent}%",
            'cpu_usage': f"{cpu_percent}%"
        }
    except Exception as e:
        health_status['checks']['system_resources'] = {'status': 'unknown', 'error': str(e)}

    # Determine overall status
    if health_status['status'] == 'degraded':
        return jsonify(health_status), 503
    else:
        return jsonify(health_status), 200

@health.route('/health/deep', methods=['GET'])
def deep_health_check():
    """Deep health check that tests actual functionality"""
    try:
        # Test task dispatch
        task = celery_app.send_task('celery.ping', timeout=10)
        result = task.get(timeout=10)

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'deep_check': True,
            'task_dispatch': 'working',
            'worker_response': result
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'deep_check': True,
            'error': str(e)
        }), 503
```

### 5.3 Log Analysis Scripts

```bash
#!/bin/bash
# File: /kith-platform/scripts/analyze_logs.sh

echo "=== LOG ANALYSIS FOR CELERY TASK FAILURES ==="

# Analyze recent Redis connection errors
echo "Redis Connection Errors (last 100 lines):"
render logs -s kith-platform --tail 100 | grep -i -E "(redis|connection|broker)" | head -20

echo ""
echo "Worker Task Processing (last 100 lines):"
render logs -s Spiderman-v3-1 --tail 100 | grep -i -E "(task|received|success|failed)" | head -20

echo ""
echo "503 Error Patterns:"
render logs -s kith-platform --tail 200 | grep -i "503\|send_task\|failed to enqueue" | head -10

echo ""
echo "Memory and Resource Issues:"
render logs -s Spiderman-v3-1 --tail 200 | grep -i -E "(memory|oom|killed|resource)" | head -10

echo ""
echo "Task Registration Issues:"
render logs -s Spiderman-v3-1 --tail 100 | grep -i -E "(register|task.*not.*found|autodiscover)" | head -10
```

---

## Quick Diagnostic Command Reference

### Immediate Problem Identification
```bash
# 1. Quick health check
curl -s https://<web-service>/health | jq '.'

# 2. Check Redis connectivity
curl -s https://<web-service>/api/diagnostics/redis-test | jq '.'

# 3. Verify worker is responsive
curl -s -X POST https://<web-service>/api/diagnostics/worker-ping | jq '.'

# 4. Check available tasks
curl -s https://<web-service>/api/diagnostics/celery-info | jq '.test_tasks'

# 5. Test actual task execution
curl -s -X POST https://<web-service>/api/analytics/test-runs \
  -H "Content-Type: application/json" \
  -d '{"markers": ["unit"], "parallel": false}'
```

### Service Status Verification
```bash
# Check service status on Render
render services list

# Check recent deployments
render deploys list -s kith-platform
render deploys list -s Spiderman-v3-1

# Check environment variables
render env get -s kith-platform | grep -E "REDIS_URL|DATABASE_URL"
render env get -s Spiderman-v3-1 | grep -E "REDIS_URL|DATABASE_URL"
```

### Resource and Performance Monitoring
```bash
# Check resource usage
render metrics -s kith-platform --period 1h --metric memory
render metrics -s Spiderman-v3-1 --period 1h --metric memory

# Check recent error rates
render logs -s kith-platform --tail 500 | grep -c "ERROR\|500\|503"
render logs -s Spiderman-v3-1 --tail 500 | grep -c "ERROR\|CRITICAL"
```

---

## Expected Results and Failure Indicators

### Normal Operation Indicators
- ✅ Health endpoint returns 200 with all checks "healthy"
- ✅ Redis test returns successful connection
- ✅ Worker ping responds within 5 seconds
- ✅ Task dispatch returns 202 with task_id
- ✅ Worker logs show task execution completion

### Critical Failure Indicators
- ❌ Redis test fails → **REDIS_URL issue or Redis service down**
- ❌ Worker ping timeout → **Worker service crashed or overloaded**
- ❌ Health check returns 503 → **Multiple system failures**
- ❌ Task dispatch returns 503 → **Broker connectivity or task routing failure**

### Warning Indicators
- ⚠️ High memory usage (>80%) → **Resource constraint approaching**
- ⚠️ Slow task execution (>30s for simple tasks) → **Performance degradation**
- ⚠️ Intermittent failures → **Network or resource intermittency**

---

## Implementation Priority

### Phase 1: Immediate Implementation (Critical)
1. Add basic diagnostic endpoints (`/health`, `/api/diagnostics/redis-test`)
2. Implement primary diagnostic script
3. Set up log monitoring for Redis connection errors

### Phase 2: Enhanced Monitoring (High Priority)
1. Add worker health and task serialization tests
2. Implement resource monitoring
3. Add deep health checks

### Phase 3: Advanced Diagnostics (Medium Priority)
1. Add concurrency and timeout testing
2. Implement automated alert systems
3. Add performance trend monitoring

This framework provides a comprehensive, systematic approach to identifying any root cause of 503 errors and task failures, going well beyond the Redis URL issue to cover the full spectrum of potential failure modes in the distributed system.