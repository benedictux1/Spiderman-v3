# Local Development Guide

## Prerequisites
- Python 3.11
- Redis (optional for Celery): \

## Quick Start
\\🚀 Kith Platform Local Development Server
==================================================
📁 Working directory: /Users/benedictleong/Library/Mobile Documents/com~apple~CloudDocs/2. Archive/2. Pet Projects /Spiderman-v3-main/kith-platform
🗄️  Database: sqlite:////Users/benedictleong/Library/Mobile Documents/com~apple~CloudDocs/2. Archive/2. Pet Projects /Spiderman-v3-main/kith-platform/local_kith_platform.db
🔑 Admin credentials: admin / admin123
==================================================
🔧 Setting up database...
2025-10-14 15:19:34 - app - INFO - Structured logging initialized
2025-10-14 15:19:34 - app.utils.database - INFO - 🔧 DEBUG: Database URL resolved: sqlite:////Users/benedictleong/Library/Mobile Docu...
2025-10-14 15:19:36 - app.utils.database - INFO - 🔧 DEBUG: Database URL resolved: sqlite:////Users/benedictleong/Library/Mobile Docu...
2025-10-14 15:19:36 - app.utils.database - INFO - 🔧 DEBUG: Creating database engine...
2025-10-14 15:19:36 - app.utils.database - INFO - 🔧 DEBUG: Original URL: sqlite:////Users/benedictleong/Library/Mobile Documents/com~apple~CloudDocs/2. Archive/2. Pet Projects /Spiderman-v3-main/kith-platform/local_kith_platform.db
2025-10-14 15:19:36 - app.utils.database - INFO - 🔧 DEBUG: Creating engine with URL: sqlite:////Users/benedictleong/Library/Mobile Docu...
2025-10-14 15:19:36 - app.utils.database - INFO - 🔧 DEBUG: Testing database connection...
2025-10-14 15:19:36 - app.utils.database - INFO - 🔧 DEBUG: Connection test successful, result: (1,)
2025-10-14 15:19:36 - app.utils.database - INFO - ✅ Database connection successful
2025-10-14 15:19:36 - app.utils.database - INFO - 🔧 DEBUG: Creating/verifying database tables...
2025-10-14 15:19:36 - app.utils.database - INFO - ✅ Database tables created/verified
✅ Database tables created/verified
2025-10-14 15:19:36 - app.utils.database - INFO - 🔧 DEBUG: Getting database session...
2025-10-14 15:19:36 - app.utils.database - INFO - 🔧 DEBUG: Engine already exists, skipping creation
2025-10-14 15:19:36 - app.utils.database - INFO - 🔧 DEBUG: Session created: 4546562752
✅ Admin user already exists
2025-10-14 15:19:36 - app.utils.database - INFO - 🔧 DEBUG: Committing session...
2025-10-14 15:19:36 - app.utils.database - INFO - ✅ Session committed successfully
2025-10-14 15:19:36 - app.utils.database - INFO - 🔧 DEBUG: Closing session...
2025-10-14 15:19:36 - app.utils.database - INFO - ✅ Session closed
✅ Database setup complete!

🚀 Starting Flask development server...
📍 Server URL: http://localhost:8000
🔧 Press Ctrl+C to stop
==================================================
 * Serving Flask app 'app'
 * Debug mode: off\
- App: http://localhost:8000
- Admin: admin / admin123

## Environment
- Uses SQLite at \
- Set \ if you want Celery tasks queued locally

## Notes
- Legacy \ archived as \. The app now runs via factory in \.
- Celery worker: \