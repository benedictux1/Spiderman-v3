#!/usr/bin/env python3
"""
Enhanced Telegram Integration with Hybrid Session Management
Provides secure, persistent Telegram sync that works both locally and on Render.
"""

import os
import json
import asyncio
import logging
import time
import fcntl
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from telethon import TelegramClient
from telethon.tl.types import User, Dialog
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

from .hybrid_telegram_session import HybridTelegramSession

# Configure logging
logger = logging.getLogger(__name__)

class EnhancedTelegramIntegration:
    """
    Enhanced Telegram integration with hybrid session management.
    Automatically handles authentication, session persistence, and sync operations.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.session_manager = HybridTelegramSession(user_id)
        self.client = None
        
        if not self.api_id or not self.api_hash:
            raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set")
    
    async def connect(self) -> bool:
        """
        Connect to Telegram with automatic session restoration.
        Returns True if successful, False otherwise.
        """
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to Telegram for user {self.user_id} (attempt {attempt + 1}/{max_retries})")
                
                # Clean up any lingering database connections
                if attempt > 0:
                    import gc
                    gc.collect()
                    await asyncio.sleep(1)
                
                # Try to restore existing session
                session_data = await self.session_manager.restore_session()
                
                if session_data:
                    logger.info(f"Restoring existing session for user {self.user_id}")
                    try:
                        # Preferred: if we stored a Telethon session file name, use it directly
                        saved_session_name = session_data.get('session_name')
                        if saved_session_name:
                            self.client = TelegramClient(saved_session_name, self.api_id, self.api_hash)
                        else:
                            # Backward-compatible: attempt manual fields restoration if present
                            session_name = f"kith_telegram_{self.user_id}_{int(datetime.now().timestamp())}"
                            self.client = TelegramClient(session_name, self.api_id, self.api_hash)
                            if 'dc_id' in session_data:
                                self.client.session.dc_id = session_data['dc_id']
                            if 'server_address' in session_data:
                                self.client.session.server_address = session_data['server_address']
                            if 'port' in session_data:
                                self.client.session.port = session_data['port']
                            if 'auth_key' in session_data:
                                self.client.session.auth_key = session_data['auth_key']
                        
                        # Non-interactive connect; do not trigger prompts
                        await self.client.connect()
                        
                        # Verify session is still valid
                        if await self._verify_session():
                            logger.info(f"Successfully restored session for user {self.user_id}")
                            return True
                        else:
                            logger.warning(f"Restored session is invalid for user {self.user_id}")
                            await self.client.disconnect()
                            self.client = None
                    except Exception as e:
                        logger.warning(f"Failed to restore session: {e}")
                        if self.client:
                            await self.client.disconnect()
                            self.client = None
                
                # Fallback: Try to use the working session file directly
                logger.info(f"Trying fallback session file for user {self.user_id}")
                try:
                    # Use the working session file that we know exists
                    fallback_session_name = "kith_telegram_session"
                    
                    # Add a small delay to prevent race conditions
                    await asyncio.sleep(0.5)
                    
                    self.client = TelegramClient(fallback_session_name, self.api_id, self.api_hash)
                    await self.client.connect()
                    
                    if await self._verify_session():
                        logger.info(f"Successfully connected using fallback session for user {self.user_id}")
                        return True
                    else:
                        logger.warning(f"Fallback session is invalid for user {self.user_id}")
                        await self.client.disconnect()
                        self.client = None
                except Exception as e:
                    logger.warning(f"Failed to use fallback session: {e}")
                    if self.client:
                        await self.client.disconnect()
                        self.client = None
                
                # If no valid session, need to authenticate
                logger.info(f"Starting new authentication for user {self.user_id}")
                return await self._authenticate_new_session()
                
            except Exception as e:
                error_msg = str(e).lower()
                if 'database is locked' in error_msg and attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    logger.error(f"Failed to connect to Telegram: {e}")
                    return False
        
        return False
    
    async def _verify_session(self) -> bool:
        """Verify that the current session is valid"""
        try:
            if not self.client:
                return False
            
            # Try to get current user info
            me = await self.client.get_me()
            return me is not None
        except Exception as e:
            logger.warning(f"Session verification failed: {e}")
            return False
    
    async def _authenticate_new_session(self) -> bool:
        """Authenticate and create new session - requires phone/OTP flow"""
        # Don't try to authenticate interactively - this should be done via phone/OTP endpoints
        logger.warning(f"No session found for user {self.user_id}. User must authenticate via phone/OTP flow.")
        return False
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        try:
            if self.client:
                await self.client.disconnect()
                self.client = None
                logger.info(f"Disconnected from Telegram for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    async def get_contacts(self) -> List[Dict[str, Any]]:
        """Get Telegram contacts"""
        if not self.client:
            if not await self.connect():
                return []
        
        try:
            contacts = []
            async for dialog in self.client.iter_dialogs():
                if isinstance(dialog.entity, User) and not dialog.entity.bot:
                    contact = {
                        'id': dialog.entity.id,
                        'first_name': dialog.entity.first_name or '',
                        'last_name': dialog.entity.last_name or '',
                        'username': dialog.entity.username or '',
                        'phone': dialog.entity.phone or '',
                        'is_verified': dialog.entity.verified or False,
                        'is_premium': dialog.entity.premium or False,
                        'last_seen': dialog.entity.status.__class__.__name__ if dialog.entity.status else 'Unknown'
                    }
                    contacts.append(contact)
            
            logger.info(f"Retrieved {len(contacts)} contacts for user {self.user_id}")
            return contacts
            
        except Exception as e:
            logger.error(f"Failed to get contacts: {e}")
            return []
    
    async def get_conversations(self, contact_id: Optional[int] = None, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get conversations from Telegram"""
        if not self.client:
            if not await self.connect():
                return []
        
        try:
            conversations = []
            since_date = datetime.now() - timedelta(days=days_back)
            
            async for dialog in self.client.iter_dialogs():
                if isinstance(dialog.entity, User):
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
                    message_count = 0
                    async for message in self.client.iter_messages(
                        dialog.entity, 
                        offset_date=since_date, 
                        reverse=True
                    ):
                        if message.text:
                            msg_data = {
                                'id': message.id,
                                'date': message.date.isoformat(),
                                'sender': 'Me' if message.out else conversation['contact_name'],
                                'text': message.text,
                                'outgoing': message.out
                            }
                            conversation['messages'].append(msg_data)
                            message_count += 1
                            
                            # Limit messages per conversation to prevent memory issues
                            if message_count >= 1000:
                                break
                    
                    if conversation['messages']:
                        conversations.append(conversation)
            
            logger.info(f"Retrieved {len(conversations)} conversations for user {self.user_id}")
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to get conversations: {e}")
            return []
    
    async def sync_contact_history(self, contact_identifier: str, days_back: int = 30) -> Optional[Dict[str, Any]]:
        """Sync chat history for a specific contact"""
        if not self.client:
            if not await self.connect():
                return None
        
        try:
            ident_clean = (contact_identifier or '').strip()
            logger.info(f"[SyncContact] Resolving identifier: {ident_clean}")
            # Resolve the entity by username or phone; fall back to dialog scan
            try:
                # Try raw
                entity = await self.client.get_entity(ident_clean)
                if not isinstance(entity, User):
                    entity = None
                # Try with leading @ for usernames
                if entity is None and ident_clean and not ident_clean.startswith('+') and not ident_clean.isdigit():
                    entity = await self.client.get_entity('@' + ident_clean)
            except Exception:
                entity = None
                # Fallback: scan dialogs to match username/phone case-insensitively
                async for dialog in self.client.iter_dialogs():
                    if isinstance(dialog.entity, User):
                        uname = (dialog.entity.username or '').lower()
                        phone = (dialog.entity.phone or '').lower()
                        first = (dialog.entity.first_name or '').lower()
                        last = (dialog.entity.last_name or '').lower()
                        display = (f"{first} {last}".strip())
                        ident = ident_clean.replace('@','').lower()
                        if ident and (ident == uname or ident == phone):
                            entity = dialog.entity
                            break
                        # Also allow contains match on display name
                        if ident and ident in display:
                            entity = dialog.entity
                            break
            if not isinstance(entity, User):
                logger.warning(f"[SyncContact] Could not resolve entity for {ident_clean}")
                return None

            # Build conversation directly from messages for this entity
            since_date = datetime.now() - timedelta(days=days_back)
            conversation = {
                'contact_id': entity.id,
                'contact_name': f"{entity.first_name or ''} {entity.last_name or ''}".strip(),
                'username': entity.username or '',
                'messages': []
            }

            # First attempt: bounded by days_back
            message_count = 0
            async for message in self.client.iter_messages(entity, offset_date=since_date, reverse=True):
                if message.text:
                    conversation['messages'].append({
                        'id': message.id,
                        'date': message.date.isoformat(),
                        'sender': 'Me' if message.out else conversation['contact_name'],
                        'text': message.text,
                        'outgoing': message.out
                    })
                    message_count += 1
                    if message_count >= 1000:
                        break

            # Fallback: if no messages found in the last N days, fetch deeper history regardless of date
            if not conversation['messages']:
                async for message in self.client.iter_messages(entity, limit=2000, reverse=True):
                    if message.text:
                        conversation['messages'].append({
                            'id': message.id,
                            'date': message.date.isoformat(),
                            'sender': 'Me' if message.out else conversation['contact_name'],
                            'text': message.text,
                            'outgoing': message.out
                        })
                        if len(conversation['messages']) >= 2000:
                            break

            if conversation['messages']:
                logger.info(f"Synced {len(conversation['messages'])} messages for contact {contact_identifier}")
                return conversation

            logger.info(f"No messages found for {contact_identifier}. entity_id={getattr(entity,'id',None)} username={getattr(entity,'username',None)} phone={getattr(entity,'phone',None)}")
            return None
                
        except Exception as e:
            logger.error(f"Failed to sync contact history: {e}")
            return None
    
    async def get_session_status(self) -> Dict[str, Any]:
        """Get current session status"""
        try:
            session_info = await self.session_manager.get_session_info()
            
            status = {
                'user_id': self.user_id,
                'has_session': await self.session_manager.has_session(),
                'is_connected': self.client is not None,
                'session_info': session_info,
                'environment': 'render' if self.session_manager.is_render else 'local',
                'storage_backend': self.session_manager.storage_backend
            }
            
            if self.client:
                try:
                    me = await self.client.get_me()
                    status['telegram_user'] = {
                        'id': me.id,
                        'first_name': me.first_name,
                        'username': me.username,
                        'phone': me.phone
                    }
                except:
                    status['telegram_user'] = None
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get session status: {e}")
            return {
                'user_id': self.user_id,
                'has_session': False,
                'is_connected': False,
                'error': str(e)
            }
    
    async def delete_session(self) -> bool:
        """Delete current session"""
        try:
            # Disconnect if connected
            await self.disconnect()
            
            # Delete session data
            success = await self.session_manager.delete_session()
            
            if success:
                logger.info(f"Successfully deleted session for user {self.user_id}")
            else:
                logger.error(f"Failed to delete session for user {self.user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()


class TelegramSyncManager:
    """
    High-level manager for Telegram sync operations.
    Handles background sync, conflict resolution, and user notifications.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.integration = EnhancedTelegramIntegration(user_id)
        self.last_sync = None
        self.sync_in_progress = False
    
    async def start_background_sync(self, days_back: int = 30) -> Dict[str, Any]:
        """Start background sync process"""
        if self.sync_in_progress:
            return {'success': False, 'message': 'Sync already in progress'}
        
        try:
            self.sync_in_progress = True
            logger.info(f"Starting background sync for user {self.user_id}")
            
            # Connect to Telegram
            if not await self.integration.connect():
                return {'success': False, 'message': 'Failed to connect to Telegram'}
            
            # Get contacts and conversations
            contacts = await self.integration.get_contacts()
            conversations = await self.integration.get_conversations(days_back=days_back)
            
            # Process and store data
            result = await self._process_sync_data(contacts, conversations)
            
            self.last_sync = datetime.now()
            self.sync_in_progress = False
            
            logger.info(f"Background sync completed for user {self.user_id}")
            return {
                'success': True,
                'message': 'Sync completed successfully',
                'contacts_count': len(contacts),
                'conversations_count': len(conversations),
                'last_sync': self.last_sync.isoformat()
            }
            
        except Exception as e:
            self.sync_in_progress = False
            logger.error(f"Background sync failed: {e}")
            return {'success': False, 'message': f'Sync failed: {str(e)}'}
    
    async def _process_sync_data(self, contacts: List[Dict], conversations: List[Dict]) -> Dict[str, Any]:
        """Process and store synced data"""
        try:
            # Here you would integrate with your existing data storage
            # For now, just return the counts
            return {
                'contacts_processed': len(contacts),
                'conversations_processed': len(conversations)
            }
        except Exception as e:
            logger.error(f"Failed to process sync data: {e}")
            raise
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        session_status = await self.integration.get_session_status()
        
        return {
            **session_status,
            'sync_in_progress': self.sync_in_progress,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None
        }
