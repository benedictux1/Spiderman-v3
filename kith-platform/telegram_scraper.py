#!/usr/bin/env python3
"""
Kith Platform - Telegram Chat Scraper
Standalone script for ingesting Telegram chat history into the Kith platform.

This script runs locally on the user's machine to ensure Telegram credentials
never leave their personal computer.
"""

import os
import json
import requests
import asyncio
from telethon.sync import TelegramClient
from telethon.tl.types import User
from dotenv import load_dotenv
from datetime import datetime, timedelta
import argparse

load_dotenv()

# --- CONFIGURATION ---
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
KITH_API_URL = os.getenv('KITH_API_URL', 'http://localhost:5001')
KITH_API_TOKEN = os.getenv('KITH_API_TOKEN', 'dev_token')
SESSION_NAME = 'kith_telegram_session'

def get_contacts_from_kith():
    """Fetch contacts from Kith platform."""
    try:
        response = requests.get(f"{KITH_API_URL}/api/contacts")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching contacts: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error connecting to Kith platform: {e}")
        return []

def find_contact_by_username(username, contacts):
    """Find a contact by Telegram username."""
    for contact in contacts:
        # This is a simplified match - in a real implementation,
        # you might store Telegram usernames in the contact data
        if username.lower() in contact['full_name'].lower():
            return contact
    return None

async def scrape_telegram_chat(target_username, days_back=30):
    """Scrape Telegram chat history for a specific user."""
    
    if not API_ID or not API_HASH:
        print("❌ Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in environment")
        print("Get these from https://my.telegram.org")
        return None
    
    try:
        # Connect to Telegram
        async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
            print("✅ Successfully connected to Telegram.")
            
            # Find the user entity
            try:
                entity = await client.get_entity(target_username)
                if not isinstance(entity, User):
                    print(f"❌ Error: '{target_username}' is a channel or group, not a user.")
                    return None
            except ValueError:
                print(f"❌ Error: Could not find user with username '{target_username}'.")
                return None
            
            # Calculate date range
            since_date = datetime.now() - timedelta(days=days_back)
            print(f"📅 Fetching messages since {since_date.strftime('%Y-%m-%d')}...")
            
            # Fetch messages
            transcript = []
            message_count = 0
            
            async for message in client.iter_messages(entity, offset_date=since_date, reverse=True):
                if message.text:
                    sender_name = "Me" if message.out else entity.first_name
                    formatted_message = f"[{message.date.strftime('%Y-%m-%d %H:%M')}] {sender_name}: {message.text}"
                    transcript.append(formatted_message)
                    message_count += 1
                    
                    # Progress indicator
                    if message_count % 10 == 0:
                        print(f"📝 Processed {message_count} messages...")
            
            if not transcript:
                print("ℹ️  No new messages found in the specified time period.")
                return None
            
            print(f"✅ Found {len(transcript)} messages")
            return "\n".join(transcript)
            
    except Exception as e:
        print(f"❌ Error during Telegram scraping: {e}")
        return None

def send_transcript_to_kith(contact_id, transcript):
    """Send the transcript to the Kith platform for analysis."""
    try:
        headers = {
            'Authorization': f'Bearer {KITH_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        payload = {
            'contact_id': contact_id,
            'transcript': transcript
        }
        
        print("🔄 Sending transcript to Kith for analysis...")
        response = requests.post(f"{KITH_API_URL}/api/process-transcript", 
                               headers=headers, json=payload)
        
        if response.status_code == 200:
            print("✅ Successfully sent transcript. Check the Kith web app for analysis.")
            return True
        else:
            print(f"❌ Error sending transcript: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending transcript: {e}")
        return False

def main():
    """Main function for the Telegram scraper."""
    parser = argparse.ArgumentParser(description='Scrape Telegram chat history for Kith platform')
    parser.add_argument('username', help='Telegram username to scrape')
    parser.add_argument('--days', type=int, default=30, help='Number of days to look back (default: 30)')
    parser.add_argument('--contact-id', type=int, help='Kith contact ID (will prompt if not provided)')
    
    args = parser.parse_args()
    
    print("🚀 Kith Telegram Scraper")
    print("=" * 40)
    
    # Get contacts from Kith if contact_id not provided
    if not args.contact_id:
        print("📋 Fetching contacts from Kith platform...")
        contacts = get_contacts_from_kith()
        
        if not contacts:
            print("❌ No contacts found. Please import contacts first.")
            return
        
        print("\nAvailable contacts:")
        for i, contact in enumerate(contacts, 1):
            print(f"{i}. {contact['full_name']} (ID: {contact['id']})")
        
        try:
            choice = int(input("\nSelect contact number: ")) - 1
            if 0 <= choice < len(contacts):
                contact_id = contacts[choice]['id']
                contact_name = contacts[choice]['full_name']
            else:
                print("❌ Invalid selection.")
                return
        except ValueError:
            print("❌ Invalid input.")
            return
    else:
        contact_id = args.contact_id
        contact_name = f"Contact {contact_id}"
    
    print(f"\n🎯 Target: {args.username}")
    print(f"👤 Kith Contact: {contact_name} (ID: {contact_id})")
    print(f"📅 Time period: {args.days} days")
    
    # Confirm before proceeding
    confirm = input("\nProceed with scraping? (y/N): ").lower()
    if confirm != 'y':
        print("❌ Cancelled.")
        return
    
    # Scrape Telegram
    transcript = asyncio.run(scrape_telegram_chat(args.username, args.days))
    
    if transcript:
        # Send to Kith
        success = send_transcript_to_kith(contact_id, transcript)
        if success:
            print("\n🎉 Process completed successfully!")
            print("📊 Check the Kith web app to review the analysis.")
        else:
            print("\n❌ Failed to send transcript to Kith platform.")
    else:
        print("\n❌ No transcript generated.")

if __name__ == "__main__":
    main() 