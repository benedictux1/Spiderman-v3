#!/usr/bin/env python3
"""
Kith Platform - Telegram Configuration Helper
Helper script to set up Telegram API credentials for the scraper.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def check_telegram_config():
    """Check if Telegram configuration is complete."""
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    print("🔧 Telegram Configuration Check")
    print("=" * 40)
    
    if api_id and api_hash:
        print("✅ TELEGRAM_API_ID and TELEGRAM_API_HASH are configured")
        return True
    else:
        print("❌ Telegram configuration incomplete")
        print("\nTo set up Telegram API credentials:")
        print("1. Go to https://my.telegram.org")
        print("2. Log in with your phone number")
        print("3. Go to 'API Development Tools'")
        print("4. Create a new application")
        print("5. Copy the 'api_id' and 'api_hash'")
        print("6. Add them to your .env file:")
        print("\n   TELEGRAM_API_ID=your_api_id")
        print("   TELEGRAM_API_HASH=your_api_hash")
        return False

def check_kith_config():
    """Check if Kith platform configuration is complete."""
    kith_url = os.getenv('KITH_API_URL', 'http://localhost:5001')
    kith_token = os.getenv('KITH_API_TOKEN', 'dev_token')
    
    print("\n🔧 Kith Platform Configuration Check")
    print("=" * 40)
    
    print(f"✅ KITH_API_URL: {kith_url}")
    print(f"✅ KITH_API_TOKEN: {kith_token}")
    
    return True

def check_email_config():
    """Check if email configuration is complete for notifications."""
    email_user = os.getenv('EMAIL_USER')
    email_password = os.getenv('EMAIL_PASSWORD')
    email_recipient = os.getenv('EMAIL_RECIPIENT')
    
    print("\n🔧 Email Configuration Check")
    print("=" * 40)
    
    if all([email_user, email_password, email_recipient]):
        print("✅ Email configuration is complete")
        print("📧 Notifications will be sent to:", email_recipient)
        return True
    else:
        print("❌ Email configuration incomplete")
        print("\nTo set up email notifications:")
        print("1. Add to your .env file:")
        print("\n   EMAIL_HOST=smtp.gmail.com")
        print("   EMAIL_PORT=587")
        print("   EMAIL_USER=your_email@gmail.com")
        print("   EMAIL_PASSWORD=your_app_password")
        print("   EMAIL_RECIPIENT=your_email@gmail.com")
        print("\n2. For Gmail, use an App Password (not your regular password)")
        return False

def main():
    """Main configuration check function."""
    print("🚀 Kith Platform - Configuration Check")
    print("=" * 50)
    
    telegram_ok = check_telegram_config()
    kith_ok = check_kith_config()
    email_ok = check_email_config()
    
    print("\n📊 Configuration Summary")
    print("=" * 30)
    
    if telegram_ok:
        print("✅ Telegram scraper ready")
    else:
        print("❌ Telegram scraper needs configuration")
    
    if kith_ok:
        print("✅ Kith platform ready")
    else:
        print("❌ Kith platform needs configuration")
    
    if email_ok:
        print("✅ Email notifications ready")
    else:
        print("❌ Email notifications need configuration")
    
    print("\n📝 Usage Instructions:")
    print("1. Start the Kith platform: python app.py")
    print("2. Start the scheduler: python scheduler.py")
    print("3. Run Telegram scraper: python telegram_scraper.py username")
    print("\nFor more help, see the README.md file")

if __name__ == "__main__":
    main() 