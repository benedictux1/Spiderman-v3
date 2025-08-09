#!/usr/bin/env python3
"""
Direct Telegram Import Script
Simple standalone script to import conversations by username/handle.
Bypasses Flask threading issues by running directly.
"""

import os
import sys
import asyncio
import sqlite3
import requests
from datetime import datetime, timedelta
from telethon.sync import TelegramClient
from telethon.tl.types import User
import re
import time
from constants import DEFAULT_DB_NAME
import uuid

# Environment setup
os.environ['TELEGRAM_API_ID'] = "24248143"
os.environ['TELEGRAM_API_HASH'] = "aed278a9da4963068b761ffac3068f0" if False else "aed278a9da4963068b761ffac306f8f0"

class DirectTelegramImport:
    def __init__(self):
        self.api_id = "24248143"
        self.api_hash = "aed278a9da4963068b761ffac306f8f0"
        # Use shared session file so existing auth is reused; avoid re-prompting
        self.session_name = os.getenv('TELEGRAM_SESSION_NAME', 'kith_telegram_session')
        self.kith_url = 'http://localhost:5001'
        self.client = None
    
    def normalize_handle(self, value):
        """Normalize username/handle for matching."""
        if not value:
            return ''
        value = str(value).strip().lower()
        value = value.lstrip('@')
        return re.sub(r'[^a-z0-9]', '', value)
    
    async def connect(self):
        """Connect to Telegram with shared session file (no cleanup)."""
        try:
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            # If already authorized, this will not prompt
            await self.client.start()
            print("✅ Connected to Telegram")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    async def find_conversations(self, identifier, days_back=30):
        """Find conversations matching the identifier."""
        print(f"🔍 Searching for conversations with '{identifier}' (last {days_back} days)...")
        
        normalized_id = self.normalize_handle(identifier)
        matching_conversations = []
        since_date = datetime.now() - timedelta(days=days_back)
        
        try:
            async for dialog in self.client.iter_dialogs():
                if dialog.entity and isinstance(dialog.entity, User):
                    # Get user details
                    contact_name = f"{dialog.entity.first_name or ''} {dialog.entity.last_name or ''}".strip()
                    username = dialog.entity.username or ''
                    contact_id = str(dialog.entity.id)
                    
                    # Normalize for matching
                    n_name = self.normalize_handle(contact_name)
                    n_user = self.normalize_handle(username)
                    n_id = self.normalize_handle(contact_id)
                    
                    # Check if this user matches our identifier
                    if (normalized_id in n_name or 
                        normalized_id in n_user or 
                        normalized_id == n_id):
                        
                        print(f"📱 Found match: {contact_name} (@{username}) - ID: {contact_id}")
                        
                        # Get messages for this conversation
                        messages = []
                        async for message in self.client.iter_messages(dialog.entity, offset_date=since_date, reverse=True):
                            if message.text:
                                msg_data = {
                                    'id': message.id,
                                    'date': message.date.isoformat(),
                                    'sender': 'Me' if message.out else contact_name,
                                    'text': message.text,
                                    'outgoing': message.out
                                }
                                messages.append(msg_data)
                        
                        if messages:
                            conversation = {
                                'contact_id': dialog.entity.id,
                                'contact_name': contact_name,
                                'username': username,
                                'messages': messages
                            }
                            matching_conversations.append(conversation)
                            print(f"✅ Found {len(messages)} messages with {contact_name}")
            
            return matching_conversations
            
        except Exception as e:
            print(f"❌ Error searching conversations: {e}")
            return []
    
    def get_db_connection(self):
        """Get database connection with retry logic."""
        max_retries = 5
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(DEFAULT_DB_NAME, timeout=30.0)
                conn.execute('PRAGMA journal_mode=WAL')  # Better concurrency
                conn.execute('PRAGMA synchronous=NORMAL')  # Better performance
                conn.execute('PRAGMA temp_store=memory')  # Use memory for temp tables
                conn.execute('PRAGMA busy_timeout=30000')  # 30 second busy timeout
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                
                # Ensure tables exist
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS contacts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        full_name TEXT NOT NULL,
                        tier INTEGER DEFAULT 2,
                        telegram_id TEXT,
                        telegram_username TEXT,
                        telegram_phone TEXT,
                        is_verified BOOLEAN DEFAULT FALSE,
                        is_premium BOOLEAN DEFAULT FALSE,
                        telegram_last_sync TIMESTAMP,
                        created_at TEXT,
                        updated_at TEXT,
                        user_id INTEGER DEFAULT 1,
                        vector_collection_id TEXT
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS synthesized_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        contact_id INTEGER,
                        category TEXT NOT NULL,
                        content TEXT NOT NULL,
                        confidence_score REAL,
                        created_at TEXT,
                        FOREIGN KEY (contact_id) REFERENCES contacts (id)
                    )
                ''')
                
                conn.commit()
                return conn
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e).lower() and attempt < max_retries - 1:
                    print(f"Database locked, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                print(f"Database connection error, retrying... (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_delay)
                retry_delay *= 2
    
    def find_or_create_contact(self, conversation):
        """Find existing contact or create new one."""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Try to find existing contact by telegram_id or username
            cursor.execute("""
                SELECT id FROM contacts 
                WHERE (telegram_id = ? AND telegram_id IS NOT NULL) OR (telegram_username = ? AND telegram_username IS NOT NULL)
            """, (conversation['contact_id'], conversation['username']))
            
            result = cursor.fetchone()
            if result:
                contact_id = result[0]
                print(f"📋 Found existing contact: {conversation['contact_name']} (ID: {contact_id})")
                conn.close()
                return contact_id
            
            # Detect available columns on contacts
            cursor.execute("PRAGMA table_info(contacts)")
            contact_columns = [row[1] for row in cursor.fetchall()]
            values = {}
            # Required logical fields
            values['full_name'] = conversation['contact_name'] or f"Telegram User {conversation['contact_id']}"
            values['tier'] = 2
            if 'telegram_id' in contact_columns:
                values['telegram_id'] = conversation['contact_id']
            if 'telegram_username' in contact_columns:
                values['telegram_username'] = conversation['username']
            if 'created_at' in contact_columns:
                values['created_at'] = datetime.now().isoformat()
            if 'updated_at' in contact_columns:
                values['updated_at'] = datetime.now().isoformat()
            if 'user_id' in contact_columns:
                values['user_id'] = 1
            if 'vector_collection_id' in contact_columns:
                values['vector_collection_id'] = f"contact_{uuid.uuid4().hex[:8]}"
            
            # Build dynamic insert
            cols = list(values.keys())
            placeholders = ", ".join(["?" for _ in cols])
            col_list = ", ".join(cols)
            sql = f"INSERT INTO contacts ({col_list}) VALUES ({placeholders})"
            cursor.execute(sql, tuple(values[c] for c in cols))
            
            contact_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"✅ Created new contact: {conversation['contact_name']} (ID: {contact_id})")
            return contact_id
            
        except Exception as e:
            print(f"❌ Error with contact: {e}")
            return None
    
    def save_conversation(self, conversation, contact_id):
        """Save conversation messages to database."""
        try:
            # Format as transcript
            transcript_lines = []
            for message in conversation['messages']:
                timestamp = datetime.fromisoformat(message['date']).strftime('%Y-%m-%d %H:%M')
                sender = message['sender']
                text = message['text']
                transcript_lines.append(f"[{timestamp}] {sender}: {text}")
            
            transcript = "\n".join(transcript_lines)
            
            # Send to Kith API for AI processing
            response = requests.post(
                f"{self.kith_url}/api/process-transcript",
                json={
                    'contact_id': contact_id,
                    'transcript': transcript
                },
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                print(f"✅ Successfully processed conversation for {conversation['contact_name']}")
                return True
            else:
                print(f"❌ Failed to process conversation: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error saving conversation: {e}")
            return False
    
    async def import_by_identifier(self, identifier, days_back=30):
        """Main import function."""
        print(f"🚀 Starting import for '{identifier}'...")
        
        # Connect to Telegram
        if not await self.connect():
            return False
        
        try:
            # Find matching conversations
            conversations = await self.find_conversations(identifier, days_back)
            
            if not conversations:
                print(f"❌ No conversations found for '{identifier}'")
                print("💡 Try:")
                print("   - Different spelling or username")
                print("   - Increase days back (current: {})".format(days_back))
                print("   - Check if you have messages with this person")
                return False
            
            print(f"📊 Found {len(conversations)} matching conversation(s)")
            
            # Process each conversation
            success_count = 0
            for conversation in conversations:
                print(f"\n📝 Processing: {conversation['contact_name']} ({len(conversation['messages'])} messages)")
                
                # Find or create contact in Kith
                contact_id = self.find_or_create_contact(conversation)
                if not contact_id:
                    print(f"❌ Failed to handle contact for {conversation['contact_name']}")
                    continue
                
                # Save conversation
                if self.save_conversation(conversation, contact_id):
                    success_count += 1
                else:
                    print(f"❌ Failed to save conversation for {conversation['contact_name']}")
            
            print(f"\n🎉 Import complete! Successfully imported {success_count}/{len(conversations)} conversations")
            return success_count > 0
            
        finally:
            # Cleanup
            if self.client:
                try:
                    await self.client.disconnect()
                    print("🔌 Disconnected from Telegram")
                except Exception as e:
                    print(f"Warning during Telegram disconnect: {e}")
            # Note: Do NOT delete session files; we want to reuse authentication

async def main():
    """Interactive main function."""
    print("=" * 60)
    print("🔥 DIRECT TELEGRAM IMPORT TOOL")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # Command line usage
        identifier = sys.argv[1]
        days_back = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    else:
        # Interactive usage
        print("\n📱 Enter the person's details to import their conversation:")
        identifier = input("Username/Handle (e.g., @username or just username): ").strip()
        
        if not identifier:
            print("❌ No identifier provided!")
            return
        
        days_input = input("Days back to search (default 30): ").strip()
        days_back = int(days_input) if days_input.isdigit() else 30
    
    print(f"\n🎯 Searching for: '{identifier}'")
    print(f"📅 Time range: Last {days_back} days")
    print("-" * 40)
    
    # Run import
    importer = DirectTelegramImport()
    success = await importer.import_by_identifier(identifier, days_back)
    
    if success:
        print("\n✅ Import successful! Check your Kith platform for the imported conversation.")
    else:
        print("\n❌ Import failed or no conversations found.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Import cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc() 