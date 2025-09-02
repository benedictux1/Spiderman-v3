# Telegram Integration for Kith Platform

## Overview

The Telegram integration allows you to import your Telegram contacts and conversations directly into the Kith platform for AI-powered relationship intelligence analysis.

## Features

### 1. Import Contacts
- Import all your Telegram contacts automatically
- Skip bots and deleted accounts
- Preserve Telegram metadata (username, verification status, premium status)
- Automatic duplicate detection

### 2. Import Conversations
- Import chat history from the last 7, 30, 90, or 180 days
- Process conversations through the AI analysis engine
- Extract relationship insights and categorize information
- Store conversations as structured data in the platform

## Setup Instructions

### Step 1: Get Telegram API Credentials

1. Go to https://my.telegram.org
2. Log in with your phone number
3. Go to "API Development Tools"
4. Create a new application
5. Copy the `api_id` and `api_hash`

### Step 2: Configure the Integration

Run the setup script:
```bash
python setup_telegram.py
```

This will:
- Install required dependencies
- Guide you through entering your API credentials
- Update your `.env` file automatically
- Test the configuration

### Step 3: Start the Platform

```bash
python app.py
```

### Step 4: Use the Integration

1. Go to Settings (⚙️ button)
2. Scroll to "Telegram Integration" section
3. Click "Import Contacts" to import your Telegram contacts
4. Click "Import Conversations" to import chat history

## Technical Details

### Architecture

The integration consists of several components:

1. **TelegramIntegration Class** (`telegram_integration.py`)
   - Handles Telegram API communication
   - Manages contact and conversation retrieval
   - Processes data for Kith platform

2. **Flask API Endpoints**
   - `/api/telegram/status` - Check integration status
   - `/api/telegram/import-contacts` - Import contacts
   - `/api/telegram/import-conversations` - Import conversations

3. **Frontend Integration**
   - Settings page with Telegram section
   - Import buttons with status feedback
   - Configuration options

### Data Flow

1. **Contact Import**:
   ```
   Telegram API → TelegramIntegration → Kith API → Database
   ```

2. **Conversation Import**:
   ```
   Telegram API → TelegramIntegration → Kith AI Engine → Database
   ```

### Security

- All Telegram credentials are stored locally in `.env` file
- No credentials are sent to external servers
- Session data is stored locally
- User authentication is handled by Telegram's official API

## Usage Examples

### Import All Contacts
```python
from telegram_integration import TelegramIntegration

integration = TelegramIntegration()
await integration.connect()
contacts = await integration.get_contacts()
integration.import_contacts_to_kith(contacts)
await integration.disconnect()
```

### Import Recent Conversations
```python
integration = TelegramIntegration()
await integration.connect()
conversations = await integration.get_conversations(days_back=30)
integration.import_conversations_to_kith(conversations)
await integration.disconnect()
```

### Full Import
```python
integration = TelegramIntegration()
await integration.full_import(days_back=30)
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
KITH_API_URL=http://localhost:5001
KITH_API_TOKEN=dev_token
```

### Dependencies

The integration requires:
- `telethon==1.34.0` - Telegram client library
- `requests` - HTTP client
- `python-dotenv` - Environment variable management

## Troubleshooting

### Common Issues

1. **"TELEGRAM_API_ID and TELEGRAM_API_HASH must be set"**
   - Run `python setup_telegram.py` to configure credentials

2. **"Failed to connect to Telegram"**
   - Check your API credentials
   - Ensure you have internet connection
   - First-time setup may require phone verification

3. **"No contacts found"**
   - Make sure you have contacts in Telegram
   - Check if you're logged into the correct account

4. **"Import failed"**
   - Check if the Kith platform is running
   - Verify the API endpoints are accessible
   - Check the logs for detailed error messages

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Manual Testing

Test the integration manually:
```bash
# Test the integration class
python -c "from telegram_integration import TelegramIntegration; print('Integration loaded successfully')"

# Test the setup script
python setup_telegram.py
```

## API Reference

### TelegramIntegration Class

#### Methods

- `connect()` - Connect to Telegram API
- `disconnect()` - Disconnect from Telegram API
- `get_contacts()` - Retrieve all contacts
- `get_conversations(days_back=30)` - Retrieve conversations
- `import_contacts_to_kith(contacts)` - Import contacts to Kith
- `import_conversations_to_kith(conversations)` - Import conversations to Kith
- `full_import(days_back=30)` - Perform full import

#### Properties

- `api_id` - Telegram API ID
- `api_hash` - Telegram API Hash
- `kith_url` - Kith platform URL
- `kith_token` - Kith API token

### Flask Endpoints

#### GET `/api/telegram/status`
Check Telegram integration status.

**Response:**
```json
{
  "status": "configured",
  "message": "Telegram integration ready"
}
```

#### POST `/api/telegram/import-contacts`
Import contacts from Telegram.

**Response:**
```json
{
  "status": "success",
  "message": "Contact import started. Check logs for progress."
}
```

#### POST `/api/telegram/import-conversations`
Import conversations from Telegram.

**Request Body:**
```json
{
  "days_back": 30
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Conversation import started (last 30 days). Check logs for progress."
}
```

## Development

### Adding New Features

1. **New Import Types**: Extend the `TelegramIntegration` class
2. **New API Endpoints**: Add routes to `setup_telegram_routes()`
3. **Frontend Features**: Update the settings page HTML/JS

### Testing

Run the test suite:
```bash
python test_telegram_integration.py
```

### Contributing

1. Follow the existing code style
2. Add appropriate error handling
3. Include logging for debugging
4. Update documentation for new features

## License

This integration is part of the Kith Platform and follows the same license terms.

## Support

For issues with the Telegram integration:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Verify your Telegram API credentials
4. Ensure the Kith platform is running correctly 