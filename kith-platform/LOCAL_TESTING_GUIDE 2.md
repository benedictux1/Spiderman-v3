# Local Testing Guide for Enhanced Telegram System

## Prerequisites

1. **Telegram API Credentials** - You'll need these from https://my.telegram.org
2. **Python Environment** - Make sure you're in the kith-platform directory
3. **Dependencies** - Install required packages

## Step 1: Get Telegram API Credentials

1. Go to https://my.telegram.org
2. Log in with your phone number
3. Go to "API Development Tools"
4. Create a new application
5. Copy the `api_id` and `api_hash`

## Step 2: Set Up Environment Variables

Create a `.env` file in the kith-platform directory:

```bash
# Telegram API Credentials
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here

# Optional: Bot token (if using bot authentication)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_USE_BOT_TOKEN=false

# Optional: Custom session name
TELEGRAM_SESSION_NAME=kith_telegram_session

# Optional: Encryption key (will be auto-generated if not set)
# TELEGRAM_ENCRYPTION_KEY=your_encryption_key_here
```

## Step 3: Install Dependencies

```bash
# Install required packages
pip install cryptography boto3 redis

# Or install from requirements.txt
pip install -r requirements.txt
```

## Step 4: Test the System

### Option A: Run the Test Suite
```bash
python3 test_enhanced_telegram.py
```

### Option B: Test Individual Components

#### Test Configuration
```python
from config.telegram_config import TelegramConfig

config = TelegramConfig.get_config()
print("Configuration:", config)

# Validate configuration
try:
    TelegramConfig.validate_config(config)
    print("✅ Configuration is valid")
except Exception as e:
    print("❌ Configuration error:", e)
```

#### Test Session Management
```python
import asyncio
from app.services.hybrid_telegram_session import HybridTelegramSession

async def test_session():
    session = HybridTelegramSession("test_user")
    
    # Test session storage
    test_data = {"user_id": "test_user", "api_id": "12345"}
    success = await session.store_session(test_data)
    print(f"Storage result: {success}")
    
    # Test session restoration
    restored = await session.restore_session()
    print(f"Restored data: {restored}")
    
    # Clean up
    await session.delete_session()

asyncio.run(test_session())
```

#### Test Enhanced Integration
```python
import asyncio
from app.services.enhanced_telegram_integration import EnhancedTelegramIntegration

async def test_integration():
    integration = EnhancedTelegramIntegration("test_user")
    
    # Test connection
    connected = await integration.connect()
    print(f"Connected: {connected}")
    
    if connected:
        # Test getting contacts
        contacts = await integration.get_contacts()
        print(f"Contacts: {len(contacts)}")
        
        # Test getting conversations
        conversations = await integration.get_conversations(days_back=7)
        print(f"Conversations: {len(conversations)}")
        
        # Disconnect
        await integration.disconnect()

asyncio.run(test_integration())
```

## Step 5: Test with Flask App

### Start the Flask Application
```bash
python app.py
```

### Test API Endpoints

#### Check Status
```bash
curl http://localhost:5001/api/telegram/enhanced/status
```

#### Connect to Telegram
```bash
curl -X POST http://localhost:5001/api/telegram/enhanced/connect
```

#### Get Contacts
```bash
curl http://localhost:5001/api/telegram/enhanced/contacts
```

#### Get Conversations
```bash
curl http://localhost:5001/api/telegram/enhanced/conversations
```

#### Sync All History
```bash
curl -X POST http://localhost:5001/api/telegram/enhanced/sync-all \
  -H "Content-Type: application/json" \
  -d '{"days_back": 30}'
```

## Step 6: Test Migration System

```python
import asyncio
from app.services.telegram_migration import TelegramSessionMigrator

async def test_migration():
    migrator = TelegramSessionMigrator("test_user")
    
    # Check migration status
    status = await migrator.get_migration_status()
    print(f"Migration status: {status}")
    
    # Test local to cloud migration (will fail without cloud setup)
    try:
        result = await migrator.migrate_to_cloud()
        print(f"Migration result: {result}")
    except Exception as e:
        print(f"Migration failed (expected): {e}")

asyncio.run(test_migration())
```

## Step 7: Test UI Components

### Add to Your HTML Template
```html
<!-- Add this to your settings page -->
<div id="telegram-enhanced-section">
    <h3>Enhanced Telegram Integration</h3>
    
    <div id="telegram-status-enhanced"></div>
    <div id="telegram-environment-info"></div>
    <div id="telegram-user-info"></div>
    <div id="telegram-sync-status"></div>
    
    <div id="telegram-message-enhanced"></div>
    
    <button id="telegram-connect-enhanced">Connect</button>
    <button id="telegram-disconnect-enhanced">Disconnect</button>
    <button id="telegram-sync-all-enhanced">Sync All</button>
    <button id="telegram-sync-contact-enhanced">Sync Contact</button>
    
    <button id="telegram-migrate-to-cloud">Migrate to Cloud</button>
    <button id="telegram-migrate-to-local">Migrate to Local</button>
    <button id="telegram-sync-storages">Sync Storages</button>
</div>

<script src="/static/js/telegram-enhanced.js"></script>
```

## Troubleshooting

### Common Issues

1. **"TELEGRAM_API_ID and TELEGRAM_API_HASH must be set"**
   - Make sure your `.env` file has the correct credentials
   - Check that the `.env` file is in the kith-platform directory

2. **"Failed to connect to Telegram"**
   - Verify your API credentials are correct
   - Check your internet connection
   - Make sure you're not already logged in from another device

3. **"Session not found"**
   - This is normal for first-time setup
   - The system will create a new session when you connect

4. **Import errors**
   - Make sure you're in the kith-platform directory
   - Install missing dependencies: `pip install cryptography boto3 redis`

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Session Files

Local sessions are stored in:
```bash
ls -la ~/.kith/telegram_sessions/
```

## Expected Results

### Successful Test Output
```
✅ Configuration System: PASSED
✅ Hybrid Session Management: PASSED
✅ Migration System: PASSED
⚠️ Enhanced Integration: FAILED (expected without API credentials)
```

### After Setting Up API Credentials
```
✅ Configuration System: PASSED
✅ Hybrid Session Management: PASSED
✅ Enhanced Integration: PASSED
✅ Migration System: PASSED
```

## Next Steps

1. **Test locally** with your credentials
2. **Verify session persistence** by restarting the app
3. **Test migration** when ready to deploy to Render
4. **Monitor logs** for any issues

## Support

If you encounter issues:
1. Check the logs in `kith_platform.log`
2. Verify your API credentials
3. Test individual components
4. Check the documentation in `ENHANCED_TELEGRAM_SYSTEM.md`
