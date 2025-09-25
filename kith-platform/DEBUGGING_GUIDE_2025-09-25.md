# Comprehensive Debugging Guide - 2025-09-25

## 🔧 Debugging Features Added

I've added extensive debugging code throughout the application to help identify issues when testing. Here's what to look for:

### 1. Database Connection Debugging
**Location**: `app/utils/database.py`

**Debug Messages to Look For**:
- `🔧 DEBUG: Using SQLite for tests - URL: sqlite:///kith_platform.db`
- `🔧 DEBUG: Environment variables - FORCE_SQLITE_FOR_TESTS: 1, FLASK_ENV: testing`
- `🔧 DEBUG: Creating database engine...`
- `🔧 DEBUG: Testing database connection...`
- `✅ Database connection successful`
- `❌ Database initialization error: [error details]`

**What This Helps With**:
- Database URL resolution issues
- Connection failures
- Environment variable problems
- Driver compatibility issues

### 2. Celery Task Execution Debugging
**Location**: `app/tasks/test_tasks.py`

**Debug Messages to Look For**:
- `🔧 DEBUG: Starting test suite execution...`
- `🔧 DEBUG: Parameters - markers: [list], parallel: [bool], triggered_by: [string]`
- `🔧 DEBUG: Environment variables for pytest:`
- `🔧 DEBUG: Final pytest command: [command]`
- `🔧 DEBUG: Executing pytest...`
- `🔧 DEBUG: Pytest completed with return code: [code]`
- `🔧 DEBUG: stdout preview: [output]`
- `🔧 DEBUG: stderr preview: [errors]`

**What This Helps With**:
- Celery task execution issues
- Pytest command construction
- Environment variable passing
- Test execution failures
- Output capture problems

### 3. Test Fixture Debugging
**Location**: `tests/conftest.py`

**Debug Messages to Look For**:
- `🔧 DEBUG: Overriding container database manager for tests...`
- `🔧 DEBUG: Original manager: [manager]`
- `🔧 DEBUG: Test manager: [manager]`
- `🔧 DEBUG: Creating sample user...`
- `🔧 DEBUG: User factory created user: [username] (ID: [id])`
- `🔧 DEBUG: Creating authenticated user session for: [username]`

**What This Helps With**:
- Database session mismatches
- User creation issues
- Authentication setup problems
- Container override failures

### 4. Authentication Debugging
**Location**: `app/services/auth_service.py` and `app/api/auth.py`

**Debug Messages to Look For**:
- `🔧 DEBUG: Authenticating user: [username]`
- `🔧 DEBUG: Database session created for auth`
- `🔧 DEBUG: User query result: [username or None]`
- `🔧 DEBUG: User found: [username] (ID: [id])`
- `🔧 DEBUG: Checking password hash...`
- `🔧 DEBUG: Password valid: [true/false]`
- `✅ User authenticated successfully: [username]`
- `❌ Invalid password for user: [username]`
- `❌ User not found: [username]`

**What This Helps With**:
- Authentication failures
- Password verification issues
- User lookup problems
- Database session issues in auth

### 5. Contacts API Debugging
**Location**: `app/api/contacts.py`

**Debug Messages to Look For**:
- `🔧 DEBUG: Getting contacts for user: [user_id]`
- `🔧 DEBUG: Request args: [args]`
- `🔧 DEBUG: Query parameters - tier: [tier], search: [search], limit: [limit], page: [page]`
- `🔧 DEBUG: Using container database manager for contacts query...`
- `🔧 DEBUG: Database session created for contacts`
- `🔧 DEBUG: Found [count] contacts`
- `✅ Contacts retrieved successfully: [count] contacts`

**What This Helps With**:
- Contacts API failures
- Database query issues
- Parameter processing problems
- Session management issues

## 🚨 Common Error Patterns to Watch For

### Database Connection Errors
```
❌ Database initialization error: [error]
🔧 DEBUG: Error type: [error_type]
🔧 DEBUG: Engine URL was: [url]
🔧 DEBUG: Original URL was: [url]
```

### Authentication Failures
```
❌ Authentication failed for user: [username]
❌ Invalid password for user: [username]
❌ User not found: [username]
```

### Test Execution Issues
```
🔧 DEBUG: Pytest completed with return code: [non-zero]
🔧 DEBUG: stderr preview: [error_details]
⚠️ Test process returned non-zero exit code but no individual test failures detected
```

### Database Session Issues
```
🔧 DEBUG: Original manager: [manager]
🔧 DEBUG: Test manager: [manager]
🔧 DEBUG: Test manager engine: [engine]
```

## 🔍 How to Use This Debugging

### 1. Run Tests with Debug Output
```bash
FORCE_SQLITE_FOR_TESTS=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -v tests --maxfail=1
```

### 2. Check Logs for Specific Issues
- **Database Issues**: Look for `🔧 DEBUG:` messages in `database.py`
- **Auth Issues**: Look for `🔧 DEBUG:` messages in `auth_service.py` and `auth.py`
- **Test Issues**: Look for `🔧 DEBUG:` messages in `test_tasks.py`
- **API Issues**: Look for `🔧 DEBUG:` messages in `contacts.py`

### 3. Common Debug Patterns

#### If you see this pattern:
```
🔧 DEBUG: Using SQLite for tests - URL: sqlite:///kith_platform.db
🔧 DEBUG: Environment variables - FORCE_SQLITE_FOR_TESTS: 1, FLASK_ENV: testing
✅ Database connection successful
```
**Meaning**: Database is working correctly with SQLite override.

#### If you see this pattern:
```
❌ Database initialization error: No module named 'psycopg'
🔧 DEBUG: Error type: ModuleNotFoundError
🔧 DEBUG: Engine URL was: postgresql+psycopg://...
```
**Meaning**: Code is still trying to use PostgreSQL instead of SQLite.

#### If you see this pattern:
```
🔧 DEBUG: User found: [username] (ID: [id])
🔧 DEBUG: Password valid: False
❌ Invalid password for user: [username]
```
**Meaning**: Password hashing mismatch between test fixture and auth service.

#### If you see this pattern:
```
🔧 DEBUG: Pytest completed with return code: 1
🔧 DEBUG: stderr preview: [error_details]
```
**Meaning**: Pytest execution failed, check the stderr for specific test failures.

## 🛠️ Troubleshooting Steps

### 1. If Database Connection Fails
1. Check environment variables in debug output
2. Verify `FORCE_SQLITE_FOR_TESTS=1` is set
3. Look for PostgreSQL driver import errors
4. Check if `DatabaseManager` is using the right URL

### 2. If Authentication Fails
1. Check if user exists in database
2. Verify password hash comparison
3. Check database session isolation
4. Look for user ID mismatches

### 3. If Tests Fail
1. Check pytest command construction
2. Verify environment variables passed to pytest
3. Look for specific test failure messages
4. Check if database sessions are properly isolated

### 4. If API Endpoints Fail
1. Check if container database manager is overridden
2. Verify database session creation
3. Look for import errors (psycopg, etc.)
4. Check if models are properly imported

## 📊 Success Indicators

### ✅ Good Signs
- `✅ Database connection successful`
- `✅ User authenticated successfully: [username]`
- `✅ Contacts retrieved successfully: [count] contacts`
- `✅ Test results persisted to database`
- `🔧 DEBUG: Pytest completed with return code: 0`

### ❌ Warning Signs
- `❌ Database initialization error`
- `❌ Authentication failed for user`
- `❌ Error getting contacts`
- `🔧 DEBUG: Pytest completed with return code: [non-zero]`
- `⚠️ Test process returned non-zero exit code`

## 🎯 Next Steps After Testing

1. **If all tests pass**: The debugging code can be removed or reduced
2. **If specific tests fail**: Use the debug output to identify the exact issue
3. **If database issues persist**: Check for remaining PostgreSQL dependencies
4. **If auth issues persist**: Verify password hashing and user creation
5. **If API issues persist**: Check for import errors and session management

The debugging code provides comprehensive visibility into the application's behavior, making it much easier to identify and fix issues during testing.
