# Phase 1 — Evidence Ingest

## Timeline of Issues from ISSUES_AND_FIXES_LOG.md

### Major Architectural Issues Identified:
1. **Lines 289-303**: Import-time side effects identified as root cause
2. **Lines 317-328**: Post-refactor deployment cascade failures
3. **Lines 73-84**: Limited test discovery (only 1-2 tests running)

### Recurring Themes:
- **Import-time execution**: Code executing during import rather than runtime
- **Environment drift**: Local vs production dependency mismatches  
- **Test isolation failures**: Production database contamination
- **Deployment cascade failures**: Each fix breaking something else

## Project Test Runner Configuration

### Primary Test Config: `pytest.ini`
- **Test discovery pattern**: `test_*.py` in `testpaths = tests`
- **Coverage targets**: `app` and `config` modules
- **Markers**: unit, integration, slow, auth, database, api, celery

### Admin Dashboard Test Execution: `app/tasks/test_tasks.py`
- **Line 69**: `cmd = ["python", "-m", "pytest", "tests/", "-q", f"--junitxml={junit_path}", "--tb=short"]`
- **Line 112**: `proc = subprocess.run(cmd, cwd=test_dir, env=env, capture_output=True, text=True)`
- **Environment isolation**: Sets `FORCE_SQLITE_FOR_TESTS=1`, `FLASK_ENV=testing`

## Render Configuration: `render.yaml`

### Web Service:
- **Runtime**: Python 3.11.0 (Line 10)
- **Build Command**: `pip install -r requirements.txt` (Line 6)  
- **Start Command**: `gunicorn --workers 2 --bind 0.0.0.0:$PORT wsgi:application` (Line 7)
- **Environment**: `FLASK_ENV=production` (Line 14)

### Worker Service (Celery):
- **Runtime**: Python 3.11.0 (Line 30)
- **Build Command**: `pip install -r requirements.txt` (Line 26)
- **Start Command**: `celery -A app.celery_app.celery_app worker --loglevel=info` (Line 27)
- **Environment**: `FLASK_ENV=production` (Line 34)

## Suspected Areas of Environment Drift

### Version Mismatches:
- **Local Python**: 3.9.6
- **Render Python**: 3.11.0 (configured in render.yaml)

### Missing Dependencies (Local):
- **flask_sqlalchemy**: Missing locally, present in requirements.txt
- **dependency-injector**: Missing locally, added during refactor
- **flask_migrate**: Missing locally, added during refactor

### Import-time Side Effects:
- **`app/utils/dependencies.py` Line 44**: `container = Container()` - instantiated at import
- **`app/__init__.py` Line 9**: Imports container during module load
- **Test discovery**: Pytest imports app code → triggers database connections

## Critical Discovery

**LOCAL TEST COLLECTION FAILS**:
```bash
$ python3 -m pytest --collect-only -q
ImportError while loading conftest
ModuleNotFoundError: No module named 'flask_sqlalchemy'
```

This proves the local environment is **NOT** properly set up, explaining why "tests sometimes pass locally" - they're not actually running the full application stack.
