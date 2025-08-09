# Phase 3 Setup Guide

## Overview
Phase 3 adds advanced automation features to the Kith Platform:
- **Telegram Chat Scraper**: Local script to ingest chat history
- **Proactive Notifications**: Email digests with actionable items

## Configuration

### 1. Telegram API Setup
To use the Telegram scraper, you need API credentials:

1. Go to https://my.telegram.org
2. Log in with your phone number
3. Go to "API Development Tools"
4. Create a new application
5. Copy the `api_id` and `api_hash`

Add to your `.env` file:
```
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

### 2. Email Configuration (Optional)
For proactive notifications, configure email settings:

Add to your `.env` file:
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
EMAIL_RECIPIENT=your_email@gmail.com
```

**Note**: For Gmail, use an App Password, not your regular password.

### 3. Kith Platform Configuration
The scraper connects to your local Kith platform:

```
KITH_API_URL=http://localhost:5001
KITH_API_TOKEN=dev_token
```

## Usage

### 1. Start the Kith Platform
```bash
python app.py
```

### 2. Start the Scheduler (Optional)
```bash
python scheduler.py
```

### 3. Run the Telegram Scraper
```bash
python telegram_scraper.py username
```

Example:
```bash
python telegram_scraper.py john_doe --days 30 --contact-id 1
```

### 4. Check Configuration
```bash
python telegram_config.py
```

## Features

### Telegram Scraper
- **Local Execution**: Runs on your machine, credentials never leave
- **Contact Integration**: Links to existing Kith contacts
- **Time Range**: Configurable date range for scraping
- **Auto-Analysis**: Automatically processes and saves to database

### Proactive Notifications
- **Weekly Digests**: Actionable items summary every Monday
- **Event Reminders**: Daily check for upcoming events
- **Email Format**: Both text and HTML email formats
- **Configurable**: Easy to modify schedules and content

## Security Notes
- Telegram credentials stay on your local machine
- Email passwords should be app-specific passwords
- All data processing happens locally
- No external dependencies for core functionality

## Troubleshooting

### Telegram Issues
- Ensure API credentials are correct
- Check that the username exists
- Verify the contact is in your Kith database

### Email Issues
- Use App Passwords for Gmail
- Check firewall settings
- Verify SMTP settings

### Scheduler Issues
- Check scheduler.log for errors
- Ensure database is accessible
- Verify email configuration

## Next Steps
1. Configure Telegram API credentials
2. Set up email notifications (optional)
3. Test with a small chat history
4. Schedule regular scraping
5. Monitor notification emails 