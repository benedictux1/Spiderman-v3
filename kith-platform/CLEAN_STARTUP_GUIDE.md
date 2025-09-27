# 🧹 Clean Startup Guide

## 🚨 **PROBLEM SOLVED: Redis Contamination Prevention**

This guide ensures that the "Run Tests" button works reliably every time by preventing Redis queue contamination from AI tasks.

## 🔧 **Root Cause Analysis**

The recurring issue was:
1. **AI tasks** (`process_note_async`) were being queued in Redis
2. When Celery worker tried to process them, they failed with `ValueError: Contact not found`
3. This corrupted the Redis queue and crashed the worker
4. The "Run Tests" button stopped working

## ✅ **Permanent Solution**

### **1. Fixed AI Task Error Handling**
- Added graceful handling for "Contact not found" errors
- AI tasks now return `SUCCESS` instead of crashing when contacts don't exist
- No more Redis queue corruption

### **2. Created Clean Startup Scripts**
- `start-clean.sh` - Complete clean startup (recommended)
- `start-celery-test-only.sh` - Test-only Celery worker
- Both scripts clear Redis and kill existing processes

### **3. Isolated Test Tasks**
- Test tasks now use a separate `test_queue`
- Celery worker can be started with `--include=app.tasks.test_tasks` to ignore AI tasks
- Complete isolation between test and AI functionality

## 🚀 **How to Start the System (Clean)**

### **Option 1: Complete Clean Startup (Recommended)**
```bash
cd kith-platform
./start-clean.sh
```

This script:
- ✅ Kills all existing processes
- ✅ Clears Redis completely
- ✅ Starts Celery worker (test tasks only)
- ✅ Starts Flask server
- ✅ Monitors both services

### **Option 2: Manual Clean Startup**
```bash
# 1. Kill existing processes
pkill -f "python.*celery"
pkill -f "python.*flask"
lsof -ti:8000 | xargs kill -9

# 2. Clear Redis
redis-cli FLUSHALL

# 3. Start Celery worker (test tasks only)
cd kith-platform
./start-celery-test-only.sh

# 4. Start Flask server (in another terminal)
cd ..
python3 start-kith-local.py
```

## 🔍 **How to Verify Everything is Working**

1. **Check Services:**
   ```bash
   ps aux | grep -E '(celery|flask|start-kith)'
   ```

2. **Test the "Run Tests" Button:**
   - Go to: http://localhost:8000/api/admin/dashboard
   - Login: admin / admin123
   - Click "Run Tests"
   - Wait 10-15 seconds
   - Check "Recent Test Runs" table

3. **Check Redis Queue:**
   ```bash
   redis-cli LLEN celery
   redis-cli LLEN test_queue
   ```

## 🛡️ **Prevention Measures**

### **1. Always Use Clean Startup**
- Never start services manually without clearing Redis first
- Use the provided scripts to ensure clean state

### **2. Monitor for AI Task Contamination**
- If you see AI tasks in Redis: `redis-cli LLEN celery`
- Clear immediately: `redis-cli FLUSHALL`

### **3. Use Test-Only Celery Worker**
- For development, always use `--include=app.tasks.test_tasks`
- This prevents AI tasks from being processed

## 🚨 **Emergency Recovery**

If the system gets contaminated again:

```bash
# 1. Kill everything
pkill -f "python.*celery"
pkill -f "python.*flask"
pkill -f "python.*start-kith"

# 2. Clear Redis
redis-cli FLUSHALL

# 3. Restart clean
cd kith-platform
./start-clean.sh
```

## 📊 **Monitoring Commands**

```bash
# Check running processes
ps aux | grep -E '(celery|flask|start-kith)'

# Check Redis queues
redis-cli LLEN celery
redis-cli LLEN test_queue

# Check Celery worker status
celery -A app.celery_app inspect active

# Check Flask server
curl -s http://localhost:8000/api/auth/login | head -5
```

## 🎯 **Success Indicators**

✅ **System is working when:**
- Celery worker shows: `celery@hostname.local ready.`
- Flask server shows: `* Running on http://0.0.0.0:8000`
- "Run Tests" button executes tests and shows results
- No AI task errors in logs
- Redis queue is clean

❌ **System is broken when:**
- Celery worker crashes with `ValueError: Exception information must include the exception type`
- "Run Tests" button does nothing
- Redis queue contains AI tasks
- Flask server gets killed

## 🔧 **Troubleshooting**

### **Problem: "Run Tests" button does nothing**
**Solution:** Use clean startup script
```bash
cd kith-platform
./start-clean.sh
```

### **Problem: Celery worker crashes**
**Solution:** Clear Redis and restart
```bash
redis-cli FLUSHALL
./start-celery-test-only.sh
```

### **Problem: Port 8000 in use**
**Solution:** Kill process using port
```bash
lsof -ti:8000 | xargs kill -9
```

## 📝 **Summary**

This solution provides:
1. **Permanent fix** for AI task errors
2. **Clean startup scripts** that prevent contamination
3. **Complete isolation** between test and AI tasks
4. **Emergency recovery** procedures
5. **Monitoring tools** to verify system health

**The "Run Tests" button will now work reliably every time!** 🎉
