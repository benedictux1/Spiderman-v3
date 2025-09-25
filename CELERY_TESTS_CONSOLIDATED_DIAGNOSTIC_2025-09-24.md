## Consolidated Diagnostic – Celery “Run Tests” Pipeline (2025-09-24)

### Executive Summary
- The Celery task for running tests is now correctly registered and invoked via the broker. The latest run executed and finished in ~6s, but pytest exited with a non-zero code during test collection, producing zero test results (0/0/0).
- Root cause of the non-zero exit: tests import `DatabaseManager`, which initializes a live database engine from `DATABASE_URL`. In environments lacking either an installed/compatible Postgres driver or a reachable Postgres, import/engine creation fails during collection. Locally, this manifests as `ModuleNotFoundError: No module named 'psycopg'`; in the worker, it likely manifests as a connection failure or similar early exception, yielding no JUnit XML.

### Current Services & Flow
- Background worker: Spiderman-v3-1 (srv-d39pn30dl3ps73ae8i4g) – Celery worker
- Web service: kith-platform (srv-d2rqbhm3jp1c738aom9g) – Admin UI/API
- Redis broker: internal (host similar to `redis://red-d39bh4nfte5s73cnatfg:6379/0`)
- Flow:
  - Admin click → POST /api/analytics/test-runs → API uses `send_task('app.tasks.test_tasks.run_test_suite', ...)` to enqueue
  - Worker receives task, runs pytest (stdout suppressed to JUnit XML), parses results, writes `TestRun`/`TestResult`

### Key Code References
- Celery app configuration and include list
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
        ...
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

- Test runner task (pytest invocation; cwd fixed to repo root)
```47:67:/Users/benedictleong/Library/Mobile Documents/com~apple~CloudDocs/2. Archive/2. Pet Projects /Spiderman-v3-main/kith-platform/app/tasks/test_tasks.py
    with tempfile.TemporaryDirectory() as td:
        junit_path = os.path.join(td, "junit.xml")
        cmd = ["python3", "-m", "pytest", "-q", f"--junitxml={junit_path}"]
        # Disable external plugins for stability
        env = os.environ.copy()
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        if markers:
            expr = " or ".join(markers)
            cmd += ["-m", expr]

        # Run pytest from the worker's repository root (Render sets cwd to /opt/render/project/src/kith-platform)
        proc = subprocess.run(cmd, cwd=os.getcwd(), env=env)
```

- Analytics API endpoint using broker (`send_task`) and surfacing debugging info on failure
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

- Database initialization used by tests (import-time engine creation)
```8:32:/Users/benedictleong/Library/Mobile Documents/com~apple~CloudDocs/2. Archive/2. Pet Projects /Spiderman-v3-main/kith-platform/app/utils/database.py
class DatabaseManager:
    def __init__(self):
        try:
            # Get database URL directly to avoid circular import
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                database_url = 'sqlite:///kith_platform.db'
            # Normalize DB URL to psycopg3 driver
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
            elif database_url.startswith('postgresql://') and '+psycopg' not in database_url:
                database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
            logger.info(f"Initializing database with URL pattern: {database_url[:30]}...")
            from sqlalchemy import create_engine, text
            self.engine = create_engine(database_url, pool_pre_ping=True)
            ...
```

### Worker Log Evidence (latest run)
- Received: `Task app.tasks.test_tasks.run_test_suite[fd3d3440-...] received`
- Completed: `succeeded in 6.18s: {'run_id': 2, 'status': 'failed'}`
- Dashboard showed “Failed 0/0/0 … Test process returned non-zero exit code” → consistent with pytest error during collection before any tests executed.

### Local Reproduction (mirroring task flags)
- Command: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q`
- Observed errors during collection:
  - `ModuleNotFoundError: No module named 'psycopg'` (triggered by tests importing `DatabaseManager`, which tries to connect to Postgres due to `DATABASE_URL`)
- Warnings (non-fatal): unknown pytest marks (`unit`, `api`, `integration`, etc.)

### Deeper Diagnosis – Why zero tests?
- Tests like `quick_test.py` and `test_csv_merge.py` import `DatabaseManager` at module import time.
- `DatabaseManager.__init__` constructs a SQLAlchemy engine immediately using `DATABASE_URL` (Postgres in prod). Without a valid psycopg install or with unreachable DB, import fails before pytest can collect tests.
- Result: pytest exits non-zero early; JUnit XML may be absent or empty; aggregator falls back to setting overall run as failed with zero counts.

### Likely Environment Differences
- Worker has `psycopg[binary]==3.2.3` in requirements; import should succeed on Render, but the engine may still fail if:
  - `DATABASE_URL` points to Postgres that is unreachable (network, credentials, or service readiness), or
  - the database driver variant differs (less likely given `[binary]`), or
  - the tests time out or error on initial connection.
- Locally you hit driver import error because your macOS Python3.9 env lacks `psycopg`.

### Other Observations / Next-Failure Candidates
- Unknown pytest markers indicate `pytest.ini` exists but does not register markers; adds noise but doesn’t cause failure.
- Integration tests may reach out to Telegram/S3/AI services; without env configuration or mocks, they will likely fail or hang later.
- Task timeouts (soft 25m, hard 30m) may be too tight for full integration runs.
- Worker concurrency is 1 (solo); running tests blocks other Celery tasks while active.

### Files Implicated in Failures
- Test modules importing DB at import time (trigger engine creation):
  - ```1:40:/Users/benedictleong/Library/Mobile Documents/com~apple~CloudDocs/2. Archive/2. Pet Projects /Spiderman-v3-main/kith-platform/quick_test.py
from app.utils.database import DatabaseManager
app = create_app(DevelopmentConfig)
db_manager = DatabaseManager()
```
  - ```1:20:/Users/benedictleong/Library/Mobile Documents/com~apple~CloudDocs/2. Archive/2. Pet Projects /Spiderman-v3-main/kith-platform/test_csv_merge.py
from app.utils.database import DatabaseManager
```
- Database manager creating engine unconditionally on init:
  - ```21:31:/Users/benedictleong/Library/Mobile Documents/com~apple~CloudDocs/2. Archive/2. Pet Projects /Spiderman-v3-main/kith-platform/app/utils/database.py
logger.info(f"Initializing database with URL pattern: {database_url[:30]}...")
from sqlalchemy import create_engine, text
self.engine = create_engine(database_url, pool_pre_ping=True)
```

### Validation Steps Completed
- Verified worker task registration, receipt, and completion via logs.
- Confirmed task now launches pytest from the correct working directory (fixed cwd).
- Reproduced local failures aligning with observed “0/0/0” outcome: import-time DB engine creation causing collection errors.

### What’s Most Likely the Root Cause Now
- Test collection fails due to import-time DB engine creation against Postgres (driver/env mismatch locally, likely connectivity in worker). Therefore, no tests run and overall status becomes failed.

### What To Verify Next (without changing code yet)
- On worker:
  - Check Postgres reachability from worker (same `DATABASE_URL` used by app). If the web service can serve endpoints that hit DB, the worker should also reach it.
  - Tail worker logs during test run for `sqlalchemy` or `psycopg` exceptions prior to task completion.
- On web:
  - Confirm `DATABASE_URL` is set for the worker service too (it is per render.yaml), and matches the web’s DB.
- Optional read-only run to narrow scope:
  - Trigger tests with marker selection `-m "unit"` to limit to unit tests that ideally don’t hit DB at import; if unit still imports DB, the same error will occur – that’s useful signal.

### Summary of Findings
- Infrastructure path (Celery, broker, worker) is functioning.
- The immediate blocker has shifted to test collection failures due to DB initialization at import time.
- This occurs in `quick_test.py` and `test_csv_merge.py` (and potentially others) because they create `DatabaseManager()` as a module-level side effect, which attempts to connect to Postgres.

### Appendix – Local Pytest Output (abridged)
- Errors
  - `ModuleNotFoundError: No module named 'psycopg'` (while initializing DB engine)
- Warnings
  - Unknown pytest markers: `unit`, `api`, `integration`, `auth`, `celery`, `database`

### Verification: Run tests/ only (excluding top-level modules)
- Command run:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests`
- High-level outcome:
  - 28 failed, 44 passed, 15 errors, 20 warnings (in ~19s)
  - Persistent psycopg import errors indicate that even under `tests/`, code paths initialize Postgres via `DatabaseManager` (not only the two top-level files).

- Representative failures/errors:
  - Postgres driver missing during DB init (local env):
    - `ModuleNotFoundError: No module named 'psycopg'` originating from `DatabaseManager` engine creation
  - Integration tests returning 302 instead of 200 on protected endpoints (e.g., analytics dashboard), showing auth/redirect behavior in tests is not aligned with expectations
  - Celery task unit tests assume `.func` attribute on tasks (e.g., `process_note_async.func(...)`), which is not present on Celery Task objects, causing `AttributeError`
  - Note service tests show AI mock return shape incompatibility (e.g., `'dict' object has no attribute 'categories'`), indicating serializer/shape mismatch in mocked AI results
  - DatabaseConfig tests expect raw `postgresql://` but code now normalizes to `postgresql+psycopg://`, causing assertion failures

### Sharper Problem Statement (updated)
- There are two intertwined blockers:
  1) Test-time database initialization: Many tests (not only the two top-level modules) lead to import-time or early DB engine creation through `DatabaseManager`, which by default targets Postgres (`DATABASE_URL` or dev defaults). On environments without a configured Postgres driver or connectivity, this fails before or during test execution.
  2) Test suite assumptions diverge from current code:
     - Celery tasks are accessed as if they had a `.func` attribute; Celery Task wrappers don’t expose `.func`.
     - DatabaseConfig expectations assume `postgresql://` prefix, but code normalizes to `postgresql+psycopg://`.
     - Some integration tests expect 200s where the app now redirects unauthenticated users (302) unless authenticated fixtures are used consistently.
     - AIService mocks may not match the current NoteService consumption contract.

### Root Causes in Code
- `app/utils/database.py` – `DatabaseManager.__init__` immediately creates an engine and runs `SELECT 1` based on `DATABASE_URL` or dev/postgres fallback. This occurs in many code paths invoked during tests.
- Test patterns:
  - Celery task tests in `tests/unit/test_celery_tasks.py` use `.func` on Celery Task objects (e.g., `process_note_async.func(...)`, `batch_process_notes.func(...)`, `sync_telegram_contacts.func(...)`) – incompatible with Celery API
  - Integration tests in `tests/integration/test_api_endpoints.py` hit routes that require auth and receive 302 redirects; fixtures may need adjustment or endpoints updated
  - DatabaseConfig tests assume legacy URL formats rather than the normalized `+psycopg` variant
  - NoteService unit tests mock AIService responses with a different shape than the service expects

### Proposed Solutions (3 options)

1) Test-friendly DB mode + lazy DB init (recommended baseline)
- What:
  - Add a test flag (e.g., `FORCE_SQLITE_FOR_TESTS=1` or detect `FLASK_ENV=testing`) that forces `DatabaseManager` to use `sqlite:///kith_platform.db` (or an in-memory sqlite for speed) during tests.
  - Convert `DatabaseManager` to lazy-initialize the engine on first session request, not in `__init__`.
  - Ensure `create_app(TestingConfig)` in tests so app config aligns with test DB.
- Pros:
  - Removes hard dependency on Postgres for the suite; faster, hermetic tests
  - Fixes the import-time failure class, allowing true test execution
  - Minimal infra changes; works locally and on the worker
- Cons:
  - Divergence from prod DB; risks missing Postgres-specific issues
  - Requires small code changes and test fixture adjustments

2) Align tests with current code contracts (unit-test refactors)
- What:
  - Update Celery task tests to call the underlying function or use `apply` / refactor tasks to delegate to pure functions that tests can call
  - Fix DatabaseConfig test expectations to accept normalized `postgresql+psycopg://`
  - Adjust integration test fixtures to authenticate before calling protected endpoints (resolve 302 vs 200)
  - Standardize AIService mock return structure to the shape `NoteService` expects
- Pros:
  - Improves test accuracy; reduces brittleness against framework wrappers
  - Surfaces genuine logic issues after infra blockers are gone
- Cons:
  - Touches multiple tests; moderate refactor effort
  - Best done after DB issue is neutralized so the suite runs

3) Provide full Postgres in test environments
- What:
  - Install `psycopg` locally; run a Postgres container and set `DATABASE_URL` accordingly
  - On Render worker, ensure `DATABASE_URL` points to a reachable Postgres and the network/security allows connections during test runs
- Pros:
  - Highest parity with production; exercises migrations and SQL dialect specifics
- Cons:
  - Heavier, slower tests; more flakiness risk
  - More infra complexity; on Render, long-running test tasks may contend with small worker resources

### Recommendation
- Phase 1 (now): Implement option 1 to ensure the suite runs (force SQLite + lazy init), then immediately apply option 2 to align tests with code (Celery task invocation style, DatabaseConfig expectations, integration auth fixtures, AIService mock shape). This will convert the current import-time/infra failures into actionable test failures.
- Phase 2 (optional): Add a small set of Postgres-backed integration tests (option 3) behind a separate marker (e.g., `postgres`) to validate critical DB behaviors without burdening the core suite.

### Next Steps (execution plan – no code applied yet)
- Add test DB forcing and lazy engine init; wire `TestingConfig` for app bootstrap in tests
- Update Celery task tests to call pure function delegates or use correct Celery APIs
- Fix DatabaseConfig tests to accept normalized URLs
- Harmonize integration test auth flow (ensure client is authenticated where 200 is expected)
- Normalize AIService mock payloads used by NoteService tests

### Evidence Links (from this session)
- Collection-only: 92 tests discovered; two top-level modules fail on import (DB init)
- Running `tests/`: 28 failed, 44 passed, 15 errors – detailed failures include Postgres driver import errors, Celery `.func` attribute assumptions, auth 302s, and AIService mock shape issues
