#!/usr/bin/env python3
"""
Kith Platform - Telegram Integration Module
Comprehensive Telegram integration for importing contacts and conversations.
"""

import os
import json
import asyncio
import requests
from datetime import datetime, timedelta
from telethon.sync import TelegramClient
from telethon.tl.types import User
from dotenv import load_dotenv
import logging
import re
import threading
import time
from flask import jsonify, request
from constants import DEFAULT_API_URL, DEFAULT_API_TOKEN, Telegram

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global lock to ensure only one Telethon client session operates at a time in this process
TELEGRAM_CLIENT_LOCK = threading.Lock()

class TelegramIntegration:
    def __init__(self):
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.use_bot_token = os.getenv('TELEGRAM_USE_BOT_TOKEN', 'false').lower() == 'true'
        self.kith_url = os.getenv('KITH_API_URL', 'http://localhost:5001')
        self.kith_token = os.getenv('KITH_API_TOKEN', 'dev_token')
        # Allow overriding the session file name, default to a stable name
        self.session_name = os.getenv('TELEGRAM_SESSION_NAME', 'kith_telegram_session')
        self.client = None
        
        if not self.api_id or not self.api_hash:
            logger.error("❌ Missing Telegram API credentials")
            logger.error("Please set TELEGRAM_API_ID and TELEGRAM_API_HASH in your .env file")
            logger.error("Get these credentials from https://my.telegram.org/apps")
            raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in environment")
    
    async def connect(self):
        """Connect to Telegram API using phone number or bot token with locking and fallback session."""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                with TELEGRAM_CLIENT_LOCK:
                    # Clean up any existing client
                    if self.client:
                        try:
                            await self.client.disconnect()
                        except:
                            pass
                    
                    session_name = self.session_name
                    if attempt > 0:
                        # Use fallback session names on retry
                        session_name = f"{self.session_name}_retry_{attempt}_{int(datetime.now().timestamp())}"
                    
                    self.client = TelegramClient(session_name, self.api_id, self.api_hash)
                    
                    if self.use_bot_token:
                        await self.client.start(bot_token=self.bot_token)
                        logger.info("✅ Successfully connected to Telegram using bot token")
                    else:
                        await self.client.start()
                        logger.info("✅ Successfully connected to Telegram using phone authentication")
                return True
                
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                
                # Clean up failed client
                if self.client:
                    try:
                        await self.client.disconnect()
                    except:
                        pass
                    self.client = None
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying connection in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"❌ Failed to connect to Telegram after {max_retries} attempts: {e}")
                    return False
        
        return False
    
    async def disconnect(self):
        """Disconnect from Telegram API."""
        if self.client:
            try:
                await self.client.disconnect()
                logger.info("✅ Disconnected from Telegram")
            except Exception as e:
                logger.warning(f"Warning during disconnect: {e}")
            finally:
                self.client = None
    
    async def get_contacts(self):
        """Get all contacts from Telegram."""
        if not self.client:
            await self.connect()
        
        try:
            contacts = []
            async for dialog in self.client.iter_dialogs():
                if dialog.entity and isinstance(dialog.entity, User):
                    contact = {
                        'id': dialog.entity.id,
                        'first_name': dialog.entity.first_name or '',
                        'last_name': dialog.entity.last_name or '',
                        'username': dialog.entity.username or '',
                        'phone': getattr(dialog.entity, 'phone', '') or '',
                        'full_name': f"{dialog.entity.first_name or ''} {dialog.entity.last_name or ''}".strip(),
                        'is_contact': dialog.entity.contact,
                        'mutual_contact': dialog.entity.mutual_contact,
                        'verified': dialog.entity.verified,
                        'bot': dialog.entity.bot,
                        'deleted': dialog.entity.deleted,
                        'scam': dialog.entity.scam,
                        'fake': dialog.entity.fake,
                        'premium': getattr(dialog.entity, 'premium', False),
                        'access_hash': dialog.entity.access_hash
                    }
                    contacts.append(contact)
            
            logger.info(f"✅ Found {len(contacts)} contacts from Telegram")
            return contacts
            
        except Exception as e:
            logger.error(f"❌ Error getting contacts: {e}")
            return []
    
    async def get_conversations(self, contact_id=None, days_back=30):
        """Get conversations from Telegram."""
        if not self.client:
            await self.connect()
        
        try:
            conversations = []
            since_date = datetime.now() - timedelta(days=days_back)
            
            async for dialog in self.client.iter_dialogs():
                if dialog.entity and isinstance(dialog.entity, User):
                    # If contact_id is specified, only get conversations for that contact
                    if contact_id and dialog.entity.id != contact_id:
                        continue
                    
                    conversation = {
                        'contact_id': dialog.entity.id,
                        'contact_name': f"{dialog.entity.first_name or ''} {dialog.entity.last_name or ''}".strip(),
                        'username': dialog.entity.username or '',
                        'messages': []
                    }
                    
                    # Get messages for this contact
                    async for message in self.client.iter_messages(dialog.entity, offset_date=since_date, reverse=True):
                        if message.text:
                            msg_data = {
                                'id': message.id,
                                'date': message.date.isoformat(),
                                'sender': 'Me' if message.out else conversation['contact_name'],
                                'text': message.text,
                                'outgoing': message.out
                            }
                            conversation['messages'].append(msg_data)
                    
                    if conversation['messages']:
                        conversations.append(conversation)
            
            logger.info(f"✅ Found {len(conversations)} conversations with messages")
            return conversations
            
        except Exception as e:
            logger.error(f"❌ Error getting conversations: {e}")
            return []
    
    def import_contacts_to_kith(self, contacts):
        """Import Telegram contacts to Kith platform."""
        imported_count = 0
        skipped_count = 0
        
        for contact in contacts:
            try:
                # Skip bots and deleted accounts
                if contact['bot'] or contact['deleted']:
                    continue
                
                # Create contact data
                contact_data = {
                    'full_name': contact['full_name'] or contact['username'] or f"Telegram User {contact['id']}",
                    'tier': 2,  # Default to tier 2, user can change later
                    'telegram_id': contact['id'],
                    'telegram_username': contact['username'],
                    'telegram_phone': contact['phone'],
                    'is_verified': contact['verified'],
                    'is_premium': contact['premium']
                }
                
                # Send to Kith API
                response = requests.post(
                    f"{self.kith_url}/api/contacts",
                    json=contact_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 201:
                    imported_count += 1
                    logger.info(f"✅ Imported: {contact_data['full_name']}")
                elif response.status_code == 409:
                    skipped_count += 1
                    logger.info(f"⏭️  Skipped (already exists): {contact_data['full_name']}")
                else:
                    logger.error(f"❌ Failed to import {contact_data['full_name']}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error importing contact {contact.get('full_name', 'Unknown')}: {e}")
        
        logger.info(f"📊 Import Summary: {imported_count} imported, {skipped_count} skipped")
        return imported_count, skipped_count
    
    def import_conversations_to_kith(self, conversations):
        """Import Telegram conversations to Kith platform."""
        imported_count = 0
        
        for conversation in conversations:
            try:
                # Find the contact in Kith
                contact_response = requests.get(f"{self.kith_url}/api/contacts")
                if contact_response.status_code != 200:
                    logger.error("❌ Failed to get contacts from Kith")
                    continue
                
                contacts = contact_response.json()
                contact_id = None
                
                # Try to find contact by Telegram ID or username
                for contact in contacts:
                    if (contact.get('telegram_id') == conversation['contact_id'] or 
                        contact.get('telegram_username') == conversation['username']):
                        contact_id = contact['id']
                        break
                
                if not contact_id:
                    logger.warning(f"⚠️  Contact not found in Kith: {conversation['contact_name']}")
                    continue
                
                # Format conversation as transcript
                transcript_lines = []
                for message in conversation['messages']:
                    timestamp = datetime.fromisoformat(message['date']).strftime('%Y-%m-%d %H:%M')
                    sender = message['sender']
                    text = message['text']
                    transcript_lines.append(f"[{timestamp}] {sender}: {text}")
                
                transcript = "\n".join(transcript_lines)
                
                # Send to Kith API for processing
                response = requests.post(
                    f"{self.kith_url}/api/process-transcript",
                    json={
                        'contact_id': contact_id,
                        'transcript': transcript
                    },
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {self.kith_token}'
                    }
                )
                
                if response.status_code == 200:
                    imported_count += 1
                    logger.info(f"✅ Imported conversation for: {conversation['contact_name']} ({len(conversation['messages'])} messages)")
                else:
                    logger.error(f"❌ Failed to import conversation for {conversation['contact_name']}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error importing conversation for {conversation['contact_name']}: {e}")
        
        logger.info(f"📊 Conversation Import Summary: {imported_count} conversations imported")
        return imported_count
    
    async def full_import(self, days_back=30):
        """Perform full import of contacts and conversations."""
        try:
            # Connect to Telegram
            if not await self.connect():
                return False
            
            # Import contacts
            logger.info("🔄 Starting contact import...")
            contacts = await self.get_contacts()
            imported_contacts, skipped_contacts = self.import_contacts_to_kith(contacts)
            
            # Import conversations
            logger.info("🔄 Starting conversation import...")
            conversations = await self.get_conversations(days_back=days_back)
            imported_conversations = self.import_conversations_to_kith(conversations)
            
            # Summary
            logger.info("📊 Import Summary:")
            logger.info(f"   Contacts: {imported_contacts} imported, {skipped_contacts} skipped")
            logger.info(f"   Conversations: {imported_conversations} imported")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during full import: {e}")
            return False
        finally:
            await self.disconnect()

# API endpoints for the Flask app
def setup_telegram_routes(app):
    """Setup Telegram integration routes for the Flask app."""
    
    @app.route('/api/telegram/status', methods=['GET'])
    def telegram_status():
        """Check Telegram integration status."""
        from flask import jsonify
        import os
        
        # Simple test - just check if API credentials are set
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        if not api_id or not api_hash:
            return jsonify({
                'authenticated': False,
                'status': 'not_configured',
                'message': 'Telegram API credentials not configured. Set TELEGRAM_API_ID and TELEGRAM_API_HASH in your .env file.'
            })
        else:
            return jsonify({
                'authenticated': False,
                'status': 'not_authenticated',
                'message': 'Telegram API credentials found, but session not authenticated. Please run: python telegram_setup.py'
            })
    
    @app.route('/api/telegram/contacts-list', methods=['GET'])
    def get_telegram_contacts_list():
        """Get list of available Telegram contacts for selection."""
        try:
            # Run the import in a background thread
            import threading
            import queue
            
            result_queue = queue.Queue()
            
            def get_contacts():
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    integration = TelegramIntegration()
                    loop.run_until_complete(integration.connect())
                    contacts = loop.run_until_complete(integration.get_contacts())
                    loop.run_until_complete(integration.disconnect())
                    loop.close()
                    result_queue.put(('success', contacts))
                except Exception as e:
                    print(f"Error getting contacts list: {e}")
                    result_queue.put(('error', str(e)))
            
            thread = threading.Thread(target=get_contacts)
            thread.daemon = True
            thread.start()
            
            # Wait for result with timeout
            try:
                result_type, result_data = result_queue.get(timeout=30)
                if result_type == 'success':
                    return jsonify({
                        'status': 'success',
                        'message': 'Contacts list retrieved successfully',
                        'contacts': result_data
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': f'Error getting contacts: {result_data}'
                    }), 500
            except queue.Empty:
                return jsonify({
                    'status': 'error',
                    'message': 'Timeout getting contacts list. Please try again.'
                }), 500
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error getting contacts list: {e}'
            }), 500
    
    @app.route('/api/telegram/conversations-list', methods=['GET'])
    def get_telegram_conversations_list():
        """Get list of available Telegram conversations for selection."""
        try:
            # Run the import in a background thread
            import threading
            import queue
            
            result_queue = queue.Queue()
            
            def get_conversations():
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    integration = TelegramIntegration()
                    loop.run_until_complete(integration.connect())
                    conversations = loop.run_until_complete(integration.get_conversations())
                    loop.run_until_complete(integration.disconnect())
                    loop.close()
                    result_queue.put(('success', conversations))
                except Exception as e:
                    print(f"Error getting conversations list: {e}")
                    result_queue.put(('error', str(e)))
            
            thread = threading.Thread(target=get_conversations)
            thread.daemon = True
            thread.start()
            
            # Wait for result with timeout
            try:
                result_type, result_data = result_queue.get(timeout=30)
                if result_type == 'success':
                    return jsonify({
                        'status': 'success',
                        'message': 'Conversations list retrieved successfully',
                        'conversations': result_data
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': f'Error getting conversations: {result_data}'
                    }), 500
            except queue.Empty:
                return jsonify({
                    'status': 'error',
                    'message': 'Timeout getting conversations list. Please try again.'
                }), 500
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error getting conversations list: {e}'
            }), 500
    
    @app.route('/api/telegram/import-contacts', methods=['POST'])
    def import_telegram_contacts():
        """Import selected contacts from Telegram."""
        try:
            data = request.get_json()
            selected_contact_ids = data.get('contact_ids', [])
            
            if not selected_contact_ids:
                return jsonify({
                    'status': 'error',
                    'message': 'No contacts selected for import'
                }), 400
            
            # Run the import in a background thread
            import threading
            def run_import():
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    integration = TelegramIntegration()
                    loop.run_until_complete(integration.connect())
                    all_contacts = loop.run_until_complete(integration.get_contacts())
                    
                    # Filter to only selected contacts
                    selected_contacts = [c for c in all_contacts if c['id'] in selected_contact_ids]
                    integration.import_contacts_to_kith(selected_contacts)
                    
                    loop.run_until_complete(integration.disconnect())
                    loop.close()
                except Exception as e:
                    print(f"Error in background import: {e}")
            
            thread = threading.Thread(target=run_import)
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'status': 'success',
                'message': f'Import started for {len(selected_contact_ids)} selected contacts. Check logs for progress.'
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error starting import: {e}'
            }), 500
    
    @app.route('/api/telegram/import-conversations', methods=['POST'])
    def import_telegram_conversations():
        """Import selected conversations from Telegram."""
        try:
            data = request.get_json()
            selected_conversation_ids = data.get('conversation_ids', [])
            days_back = data.get('days_back', 30)
            
            if not selected_conversation_ids:
                return jsonify({
                    'status': 'error',
                    'message': 'No conversations selected for import'
                }), 400
            
            # Run the import in a background thread
            import threading
            def run_import():
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    integration = TelegramIntegration()
                    loop.run_until_complete(integration.connect())
                    all_conversations = loop.run_until_complete(integration.get_conversations(days_back=days_back))
                    
                    # Filter to only selected conversations
                    selected_conversations = [c for c in all_conversations if c['contact_id'] in selected_conversation_ids]
                    integration.import_conversations_to_kith(selected_conversations)
                    
                    loop.run_until_complete(integration.disconnect())
                    loop.close()
                except Exception as e:
                    print(f"Error in background import: {e}")
            
            thread = threading.Thread(target=run_import)
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'status': 'success',
                'message': f'Import started for {len(selected_conversation_ids)} selected conversations (last {days_back} days). Check logs for progress.'
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error starting import: {e}'
            }), 500
    
    @app.route('/api/telegram/import-by-identifier', methods=['POST'])
    def import_conversations_by_identifier():
        """Import conversations with a specific person by phone number or username."""
        try:
            data = request.get_json()
            identifier = (data.get('identifier', '') or '').strip()
            days_back = data.get('days_back', 30)
            
            if not identifier:
                return jsonify({
                    'status': 'error',
                    'message': 'Please provide a phone number or username'
                }), 400
            
            # Normalization helper
            def normalize_handle(value: str) -> str:
                if value is None:
                    return ''
                # remove leading @, spaces and non-alphanumerics for robust matching
                value = value.strip()
                value = value.lstrip('@')
                return re.sub(r'[^a-z0-9]', '', value.lower())
            
            normalized_identifier = normalize_handle(identifier)
            
            # Run the import in a background thread
            import threading
            import queue
            import time
            
            result_queue = queue.Queue()
            
            def import_by_identifier():
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    max_retries = 3
                    retry_delay = 2
                    
                    for attempt in range(max_retries):
                        try:
                            integration = TelegramIntegration()
                            loop.run_until_complete(integration.connect())
                            
                            # Get all conversations
                            all_conversations = loop.run_until_complete(integration.get_conversations(days_back=days_back))
                            
                            # Filter conversations by identifier (robust matching)
                            matching_conversations = []
                            for conversation in all_conversations:
                                contact_name = conversation.get('contact_name', '') or ''
                                username = conversation.get('username', '') or ''
                                contact_id = str(conversation.get('contact_id', '') or '')
                                
                                n_name = normalize_handle(contact_name)
                                n_user = normalize_handle(username)
                                n_id = normalize_handle(contact_id)
                                
                                if (
                                    normalized_identifier in n_name or
                                    normalized_identifier in n_user or
                                    normalized_identifier == n_id
                                ):
                                    matching_conversations.append(conversation)
                            
                            if matching_conversations:
                                integration.import_conversations_to_kith(matching_conversations)
                                result_queue.put(('success', f'Found and imported {len(matching_conversations)} conversations with {identifier}'))
                            else:
                                result_queue.put(('error', f'No conversations found for {identifier}'))
                            
                            loop.run_until_complete(integration.disconnect())
                            loop.close()
                            break
                        except Exception as e:
                            error_msg = str(e)
                            if 'database is locked' in error_msg.lower() and attempt < max_retries - 1:
                                logger.warning(f"Database locked, retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                                time.sleep(retry_delay)
                                retry_delay *= 2
                                continue
                            else:
                                result_queue.put(('error', error_msg))
                                break
                except Exception as e:
                    result_queue.put(('error', str(e)))
            
            thread = threading.Thread(target=import_by_identifier)
            thread.daemon = True
            thread.start()
            
            # Wait for result with a slightly higher timeout
            try:
                result_type, result_data = result_queue.get(timeout=150)
                if result_type == 'success':
                    return jsonify({
                        'status': 'success',
                        'message': result_data
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': result_data
                    }), 500
            except queue.Empty:
                return jsonify({
                    'status': 'error',
                    'message': 'Timeout importing conversations. Please try again.'
                }), 500
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error importing conversations: {e}'
            }), 500

# Standalone import function
async def run_telegram_import(days_back=30):
    """Run the Telegram import process."""
    integration = TelegramIntegration()
    return await integration.full_import(days_back=days_back)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Import Telegram contacts and conversations to Kith')
    parser.add_argument('--days', type=int, default=30, help='Number of days back to import conversations')
    parser.add_argument('--contacts-only', action='store_true', help='Import only contacts')
    parser.add_argument('--conversations-only', action='store_true', help='Import only conversations')
    
    args = parser.parse_args()
    
    async def main():
        integration = TelegramIntegration()
        
        if args.contacts_only:
            await integration.connect()
            contacts = await integration.get_contacts()
            integration.import_contacts_to_kith(contacts)
            await integration.disconnect()
        elif args.conversations_only:
            await integration.connect()
            conversations = await integration.get_conversations(days_back=args.days)
            integration.import_conversations_to_kith(conversations)
            await integration.disconnect()
        else:
            await integration.full_import(days_back=args.days)
    
    asyncio.run(main()) 