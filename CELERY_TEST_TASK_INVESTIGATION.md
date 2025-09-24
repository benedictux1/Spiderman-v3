## Celery Test Task – Investigation Report

### Symptom
- Admin Dashboard → “Run Tests” shows:
  - Failed: Test runner task not registered. Please check Celery worker setup.
  - Available tasks (examples): app.tasks.ai_tasks.batch_process_notes, app.tasks.ai_tasks.cleanup_old_tasks, …
  - Test tasks found: (empty)

### Services and Environment
- Background worker (active):
  - Name: Spiderman-v3-1
  - ID: srv-d39pn30dl3ps73ae8i4g
  - Start command: `celery -A app.celery_app.celery_app worker --loglevel=info`
- Web service (serving the Admin UI/API):
  - Name: kith-platform
  - ID: srv-d2rqbhm3jp1c738aom9g
  - Start command: `gunicorn wsgi:app`
- Redis: internal Render Redis. Worker logs show host like `redis://red-d39bh4nfte5s73cnatfg:6379/`

### Relevant Code and Configuration
- Celery app creation and task include list:
```1:50:/Users/benedictleong/Library/Mobile Documents/com~apple~CloudDocs/2. Archive/2. Pet Projects /Spiderman-v3-main/kith-platform/app/celery_app.py
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

- Test runner task definition (registered on `celery_app`):
```1:18:/Users/benedictleong/Library/Mobile Documents/com~apple~CloudDocs/2. Archive/2. Pet Projects /Spiderman-v3-main/kith-platform/app/tasks/test_tasks.py
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
```
```19:29:/Users/benedictleong/Library/Mobile Documents/com~apple~CloudDocs/2. Archive/2. Pet Projects /Spiderman-v3-main/kith-platform/app/tasks/test_tasks.py
@celery_app.task(bind=True, name='app.tasks.test_tasks.run_test_suite')
def run_test_suite(self: Task, markers: Optional[List[str]] = None, parallel: bool = True, triggered_by: str = "admin"):
    # executes pytest, parses JUnit XML, persists TestRun/TestResult
```

- API endpoint that starts the test run (uses send_task):
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

### Evidence Collected
- Local verification (simulating worker import):
  - After forcing Celery to import defaults, registry contains `app.tasks.test_tasks.run_test_suite`.
  - Indicates the module and decorator are correct and discoverable when includes/autodiscover load.
- Render worker logs (latest live deploy):
  - Show `Loaded Celery tasks from app.tasks.test_tasks` and task list includes `. app.tasks.test_tasks.run_test_suite`.
  - Confirms the worker registers the test task and is connected to Redis.
- Web service configuration:
  - Set `REDIS_URL` on `kith-platform` so `send_task` can publish to the broker.
  - Deploy was triggered to apply this variable.
- UI error payload shows “Available tasks” listing only local ai_tasks, and “Test tasks found:” empty. This list comes from the web process’s in-memory Celery registry and is not authoritative for the worker; it can be empty even when send_task succeeds. The error response occurs only when `send_task` raises (i.e., broker or routing issue), not merely because the registry is empty.

### Hypotheses (multiple possible causes)
1) Web service cannot reach Redis broker (missing or incorrect `REDIS_URL`).
   - Likely root cause earlier; addressed by setting `REDIS_URL` on `kith-platform`.
2) Task name mismatch between worker registration and `send_task` name.
   - Worker lists `app.tasks.test_tasks.run_test_suite`; endpoint uses the same name → OK.
3) Worker not running or using different queue.
   - Worker logs show ready and consuming default `celery` queue → OK.
4) Version/env mismatch causing serializer/protocol issues.
   - Both services are Python and Celery 5.x; no serializer errors observed.
5) Different service in use by UI (hitting a suspended web service).
   - Ensure the Admin UI is served by `kith-platform` (active), not the suspended `Spiderman-v3` web.
6) DNS/hostname scope for Redis between services.
   - Using the internal Redis host (as seen in worker logs) should resolve for web too. If not, use Render’s environment-provided internal URL via service linkage.

### Tests Performed / Suggested
- Local imports: confirmed `test_tasks` registers on Celery app when loader imports default modules.
- Worker logs: confirmed registration and queue readiness.
- Action taken: set `REDIS_URL` on web service and redeployed.
- Next verification (post-deploy):
  1. Call `GET https://<web-service>/health` to verify the web service is the active one (kith-platform).
  2. Trigger `POST /api/analytics/test-runs` from the Admin UI or via curl and observe 202 with task_id.
  3. Check worker logs for task acceptance of `app.tasks.test_tasks.run_test_suite`.
  4. Verify recent runs populate via `GET /api/analytics/test-runs`.

### Conclusions
- The worker properly registers the test task.
- The UI error persists when the web service cannot publish to Redis (send_task exception), which previously happened due to missing `REDIS_URL` on the web service.
- After configuring `REDIS_URL` on `kith-platform`, the request should succeed provided the UI is served by that service and deploy has completed.

### Recommended Fix Path
1) Ensure the Admin UI you’re using is the `kith-platform` service (the only active web service).
2) Wait for the latest `kith-platform` deploy to complete and verify `REDIS_URL` is present in its environment.
3) Retry “Run Tests”. You should see a 202 response with a task ID and the run should appear in the dashboard list shortly after.
4) If failure persists:
   - Capture the JSON error returned by `POST /api/analytics/test-runs`.
   - Check `kith-platform` logs for the exact exception message from `send_task`.
   - Confirm worker logs show it is connected and ready.
   - As a fallback diagnostic, test a basic enqueue from web: `celery_app.send_task('app.tasks.ai_tasks.cleanup_old_tasks')` and see if that routes to worker.

### Appendix: Task Registry Snapshots
- Local (forced import): shows `app.tasks.test_tasks.run_test_suite` present.
- Worker (Render logs): shows `. app.tasks.test_tasks.run_test_suite` in [tasks] list.
