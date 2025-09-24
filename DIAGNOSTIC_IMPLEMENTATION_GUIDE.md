# Diagnostic Framework Implementation Guide

## Quick Start

To immediately start diagnosing your 503 errors and task failures, follow these steps:

### 1. Run the Master Diagnostic Script

```bash
cd /path/to/your/project/kith-platform/scripts
./run_all_diagnostics.sh https://your-web-service-url.onrender.com
```

This will run all diagnostic tools in sequence and provide a comprehensive report.

### 2. Quick Individual Tests

If you need to run specific tests quickly:

```bash
# Test system integration only
./diagnose_system.sh https://your-web-service-url.onrender.com

# Test component isolation only
./isolation_tests.sh

# Analyze recent logs only
./analyze_logs.sh
```

## Implementation Steps

### Phase 1: Add Diagnostic API Endpoints (REQUIRED)

The diagnostic scripts depend on API endpoints that need to be added to your Flask application.

1. **Add the diagnostic blueprint to your Flask app:**

```python
# In your main Flask app file (app.py or __init__.py)
from app.api.diagnostics import diagnostics

app.register_blueprint(diagnostics, url_prefix='/api/diagnostics')
```

2. **Update your health endpoint:**

Make sure you have a basic health endpoint at `/health` that returns service information.

### Phase 2: Set Up Script Permissions

Make sure all scripts are executable:

```bash
chmod +x kith-platform/scripts/*.sh
```

### Phase 3: Configure Environment

Ensure the diagnostic scripts can access Render CLI:

```bash
# Install Render CLI if not already installed
npm install -g @render/cli

# Login to Render
render auth login
```

## File Structure

The diagnostic framework consists of these files:

```
kith-platform/
├── app/
│   └── api/
│       └── diagnostics.py          # Diagnostic API endpoints
├── scripts/
│   ├── run_all_diagnostics.sh      # Master script (run this first)
│   ├── diagnose_system.sh          # System integration tests
│   ├── isolation_tests.sh          # Component isolation tests
│   └── analyze_logs.sh             # Log analysis
└── COMPREHENSIVE_DIAGNOSTIC_FRAMEWORK.md
```

## Usage Examples

### Example 1: First-time Diagnosis

```bash
# Run complete diagnostic suite
./run_all_diagnostics.sh https://kith-platform.onrender.com

# The script will:
# 1. Test individual components (Redis, DB, Worker)
# 2. Test system integration (API endpoints, task dispatch)
# 3. Analyze historical logs for patterns
# 4. Provide actionable recommendations
```

### Example 2: Quick Redis Check

```bash
# Test only Redis connectivity
curl -X POST https://your-service.onrender.com/api/diagnostics/redis-test
```

### Example 3: Monitor After Fixes

```bash
# After fixing issues, monitor in real-time
render logs -s kith-platform -f &
render logs -s Spiderman-v3-1 -f &

# Then test actual functionality
curl -X POST https://your-service.onrender.com/api/analytics/test-runs \
  -H "Content-Type: application/json" \
  -d '{"markers": ["unit"], "parallel": false}'
```

## Expected Results

### Normal Operation
- All diagnostic scripts exit with code 0
- Health endpoints return 200 status
- Redis and database connections successful
- Worker responds to ping within 5 seconds
- Task dispatch returns 202 with task_id

### Common Issues and Solutions

#### Issue: Redis Connection Failed
```
❌ Redis connectivity test FAILED
Response: {"status": "error", "error": "REDIS_URL environment variable not set"}
```

**Solution:**
```bash
render env set -s kith-platform REDIS_URL=your-redis-url
render deploy -s kith-platform
```

#### Issue: Worker Not Responding
```
❌ Worker ping test FAILED
Response: {"status": "error", "error": "No workers responding to ping"}
```

**Solution:**
```bash
render services list  # Check if worker service is running
render logs -s Spiderman-v3-1 --tail 100  # Check worker logs
render restart -s Spiderman-v3-1  # Restart worker if needed
```

#### Issue: Task Not Registered
```
❌ Task execution test FAILED
Response: {"error": "task_not_found", "detail": "Test runner task not registered"}
```

**Solution:**
1. Check worker logs for task registration:
   ```bash
   render logs -s Spiderman-v3-1 | grep -i "register\|run_test_suite"
   ```

2. Verify task imports in worker:
   ```bash
   render logs -s Spiderman-v3-1 | grep -i "include.*tasks"
   ```

3. Restart worker to reload task modules:
   ```bash
   render restart -s Spiderman-v3-1
   ```

## Monitoring Setup

### Real-time Monitoring
```bash
# Monitor both services simultaneously
tmux new-session -d -s monitoring \
  "render logs -s kith-platform -f" \; \
  split-window -h "render logs -s Spiderman-v3-1 -f"

# Attach to monitoring session
tmux attach -t monitoring
```

### Automated Health Checks
Set up a cron job or monitoring service to regularly check system health:

```bash
# Example cron job (runs every 5 minutes)
*/5 * * * * /path/to/diagnose_system.sh https://your-service.onrender.com > /dev/null || echo "System health check failed" | mail admin@yourcompany.com
```

## Integration with CI/CD

Add diagnostic checks to your deployment pipeline:

```yaml
# Example GitHub Actions step
- name: Run Health Check
  run: |
    cd kith-platform/scripts
    ./diagnose_system.sh ${{ secrets.WEB_SERVICE_URL }}
  continue-on-error: true
```

## Troubleshooting the Diagnostic Framework

### Scripts Don't Run
- Check file permissions: `ls -la scripts/`
- Make executable: `chmod +x scripts/*.sh`
- Check shebang line: `head -1 scripts/diagnose_system.sh`

### API Endpoints Not Found
- Verify diagnostic blueprint is registered in Flask app
- Check if service is deployed with latest code
- Test endpoint directly: `curl https://your-service/api/diagnostics/redis-test`

### Render CLI Issues
- Check authentication: `render auth whoami`
- Verify service names: `render services list`
- Update CLI: `npm update -g @render/cli`

## Advanced Usage

### Custom Diagnostic Tests
Add your own diagnostic tests by:

1. Creating a new function in `diagnostics.py`
2. Adding the endpoint to the diagnostic script
3. Including it in the master diagnostic script

### Integration with Monitoring Services
The diagnostic endpoints can be integrated with:
- Datadog
- New Relic
- Prometheus + Grafana
- Custom monitoring solutions

### Load Testing Integration
Use the diagnostic endpoints to monitor system health during load testing:

```bash
# Run diagnostics before, during, and after load tests
./diagnose_system.sh > before_load_test.txt
# ... run load test ...
./diagnose_system.sh > after_load_test.txt
diff before_load_test.txt after_load_test.txt
```

This comprehensive diagnostic framework will help you identify and resolve the root causes of your 503 errors and task failures systematically.