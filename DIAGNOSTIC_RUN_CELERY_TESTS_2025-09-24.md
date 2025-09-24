## Diagnostic Run – Celery Test Task (2025-09-24)

### Scope
- Consolidate findings from `DIAGNOSTIC_IMPLEMENTATION_GUIDE.md`, `COMPREHENSIVE_DIAGNOSTIC_FRAMEWORK.md`, and `CELERY_TEST_TASK_INVESTIGATION.md` with fresh service and log checks.
- Identify root causes for: Admin “Run Tests” → "Test runner task not registered".
- Propose a ranked, minimal-risk fix plan; no code changes in this document.

### Current Symptom (UI)
- Error shown:
  - Failed: Test runner task not registered. Please check Celery worker setup.
  - Available tasks: only `app.tasks.ai_tasks.*` and core Celery tasks; empty "Test tasks found:".

### Known Architecture
- Background worker (active): `Spiderman-v3-1` (srv-d39pn30dl3ps73ae8i4g), Celery worker.
- Web service (active): `kith-platform` (srv-d2rqbhm3jp1c738aom9g), serves Admin UI and API.
- Redis (internal): broker observed in worker logs: `redis://red-d39bh4nfte5s73cnatfg:6379/`.

### Relevant Code – Key References
- Celery app configuration includes the test tasks module:
```1:45:/Users/benedictleong/Library/Mobile Documents/com~apple~CloudDocs/2. Archive/2. Pet Projects /Spiderman-v3-main/kith-platform/app/celery_app.py
import os
import logging
from celery import Celery
from config.settings import Config

logger = logging.getLogger(__name__)

def create_celery_app():
    """Create and configure Celery application"""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    logger.info(f"Initializing Celery with Redis URL pattern: {redis_url[:20]}...")
    celery = Celery('kith_platform')
    celery.conf.update(
        broker_url=redis_url,
        result_backend=redis_url,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,
        task_soft_time_limit=25 * 60,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        worker_concurrency=1,
        worker_pool='solo',
        result_expires=3600,
    )
    celery.conf.update(
        include=[
            'app.tasks.ai_tasks',
            'app.tasks.telegram_tasks',
            'app.tasks.test_tasks',
        ]
    )
    try:
        celery.autodiscover_tasks(['app'])
    except Exception as e:
        logger.debug(f"Autodiscover skipped: {e}")
    return celery

celery_app = create_celery_app()
```

- Test task definition and registration on Celery app:
```1:25:/Users/benedictleong/Library/Mobile Documents/com~apple~CloudDocs/2. Archive/2. Pet Projects /Spiderman-v3-main/kith-platform/app/tasks/test_tasks.py
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

@celery_app.task(bind=True, name='app.tasks.test_tasks.run_test_suite')
def run_test_suite(self: Task, markers: Optional[List[str]] = None, parallel: bool = True, triggered_by: str = "admin"):
    ...
```

- API endpoint that triggers the run (intended to use broker even if local registry is empty):
```38:63:/Users/benedictleong/Library/Mobile Documents/com~apple~CloudDocs/2. Archive/2. Pet Projects /Spiderman-v3-main/kith-platform/app/api/analytics.py
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
```

### Fresh Evidence (Services and Logs)
- Worker logs (latest live): show `. app.tasks.test_tasks.run_test_suite` registered and worker READY on Redis.
- Web service logs (after latest deploy):
  - Many health and GET requests. No clear POST `/api/analytics/test-runs` entries captured in sampled window.
  - Error entries at various times: `app.api.analytics - ERROR - run_test_suite task not found. Available test tasks: []` (indicates code path checking local registry, i.e., older code path).
- Local workspace status shows web/API files modified but not committed/pushed (explains why web still runs older code):
  - Modified: `app/api/analytics.py`, `app/celery_app.py`, `app/tasks/test_tasks.py` (uncommitted locally).

### Hypotheses (ranked)
1) Web service is running older code (pre-change) that requires local task registration and errors out when the test task isn’t locally visible.
   - Evidence: Web error log message text matches the pre-change path; local git shows uncommitted changes.
   - Impact: `send_task` improvement not deployed; UI keeps failing with “task not registered”.
2) Web service broker env not set or mismatched.
   - We set `REDIS_URL` and saw a live deploy; less likely now, but still verify on service env page.
3) Intermittent DNS scope to internal Redis host from web.
   - If using internal hostname, should resolve; keep as a fallback check.
4) Queue mismatch (non-default queue).
   - Worker shows default `celery` queue; API does not set a custom queue; unlikely.

### Minimal-Risk Resolution Plan
- Step 1: Commit and push current changes so web service deploys the broker-based `send_task` path.
  - Commit: `app/api/analytics.py`, `app/celery_app.py`, `app/tasks/test_tasks.py`.
  - Deploy: auto-deploy on `kith-platform` should pick up changes.
- Step 2: Post-deploy validation
  - Trigger `POST /api/analytics/test-runs` via Admin UI.
  - Expect 202 and `task_id` in response.
  - Confirm worker logs show acceptance of `app.tasks.test_tasks.run_test_suite`.
  - Check `GET /api/analytics/test-runs` populates run(s).
- Step 3: If failure persists
  - Inspect web logs for `Failed to enqueue app.tasks.test_tasks.run_test_suite: <error>` to capture actual broker exception.
  - Verify web env has `REDIS_URL=redis://red-d39bh4nfte5s73cnatfg:6379/0`.
  - Manually enqueue a trivial task from API (`app.tasks.ai_tasks.cleanup_old_tasks`) to validate broker path.

### Rollback/Safety
- Changes affect only how the API triggers the task (publish via broker) and task registration method; worker already registers test task.
- No database schema changes; low blast radius.

### Acceptance Criteria
- Clicking “Run Tests” returns 202 with a task ID.
- Worker log shows the test task accepted.
- Recent test runs appear in Admin dashboard; statuses transition to completed/failed.

### Notes
- The “Available tasks” shown in the error response are from the web process’s local registry and are not authoritative for the worker. With `send_task`, local registration in the web process is unnecessary;
  only the worker must register the task (it does).
