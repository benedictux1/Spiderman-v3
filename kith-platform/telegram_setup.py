#!/usr/bin/env python3
"""
One-time Telegram authentication setup
This script helps you authenticate with Telegram using your phone number
"""

import os
import asyncio
from telethon.sync import TelegramClient
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_NAME = 'kith_telegram_session'

async def setup_telegram_auth():
    """Set up Telegram authentication with phone number"""
    
    print("=== Telegram Authentication Setup ===")
    print("This is a one-time setup to authenticate your Telegram account.")
    print("You will need to:")
    print("1. Enter your phone number")
    print("2. Enter the verification code sent to your Telegram app")
    print("3. Optionally enter your 2FA password if enabled")
    print()
    
    client = None
    try:
        print(f"Creating session: {SESSION_NAME}")
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        
        print("Connecting to Telegram...")
        await client.start()
        
        print("Testing connection...")
        me = await client.get_me()
        print(f"✅ Successfully authenticated as: {me.first_name} {me.last_name or ''} (@{me.username or 'no_username'})")
        print(f"   Phone: {me.phone}")
        print(f"   User ID: {me.id}")
        
        # Test basic functionality
        print("\nTesting basic functionality...")
        dialogs = await client.get_dialogs(limit=5)
        print(f"✅ Successfully retrieved {len(dialogs)} conversations")
        
        print("\n🎉 Setup complete! The application can now import Telegram conversations.")
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
        
    finally:
        if client:
            await client.disconnect()

def main():
    if not API_ID or not API_HASH:
        print("❌ ERROR: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")
        print("Get these credentials from https://my.telegram.org/apps")
        return False
        
    try:
        return asyncio.run(setup_telegram_auth())
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        return False
    except Exception as e:
        print(f"❌ Setup failed with error: {e}")
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\nYou can now use the Telegram import feature in the web application!")
    else:
        print("\nPlease run this setup again to authenticate with Telegram.")