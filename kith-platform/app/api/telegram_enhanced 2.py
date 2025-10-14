#!/usr/bin/env python3
"""
Enhanced Telegram API Endpoints
Provides secure, persistent Telegram sync functionality.
"""

# CRITICAL: Redirect stdin and patch input() BEFORE importing Telethon
import sys
import os

# Redirect stdin to devnull globally for this module
_original_stdin = sys.stdin
sys.stdin = open(os.devnull, 'r')

# Also monkey-patch input() as backup
import builtins
_original_input = builtins.input
_input_blocked = False

def _patched_input(prompt=''):
    if _input_blocked:
        raise EOFError("Interactive input blocked in API context")
    return _original_input(prompt)

builtins.input = _patched_input

import os
import json
import asyncio
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from functools import wraps

from ..services.enhanced_telegram_integration import EnhancedTelegramIntegration, TelegramSyncManager
from ..services.hybrid_telegram_session import HybridTelegramSession
from ..services.telegram_migration import TelegramSessionMigrator

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
telegram_enhanced_bp = Blueprint('telegram_enhanced', __name__, url_prefix='/api/telegram/enhanced')

# Import Telethon for authentication endpoints
try:
    from telethon import TelegramClient
    from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
    _TELETHON_AVAILABLE = True
except Exception:
    _TELETHON_AVAILABLE = False

# Pending auth sessions (in-memory for simplicity)
PENDING_TG_AUTH = {}

def async_route(f):
    """Decorator to handle async functions in Flask routes"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

def get_user_id():
    """Get user ID from request context or session"""
    # This would integrate with your existing auth system
    # For now, return a default user ID
    return request.headers.get('X-User-ID', 'default_user')

@telegram_enhanced_bp.route('/status', methods=['GET'])
@async_route
async def get_enhanced_status():
    """Get enhanced Telegram integration status"""
    try:
        user_id = get_user_id()
        integration = EnhancedTelegramIntegration(user_id)
        
        status = await integration.get_session_status()
        
        return jsonify({
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get enhanced status: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to get status: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@telegram_enhanced_bp.route('/connect', methods=['POST'])
@async_route
async def connect_enhanced():
    """Connect to Telegram with enhanced session management"""
    try:
        user_id = get_user_id()
        integration = EnhancedTelegramIntegration(user_id)
        
        success = await integration.connect()
        
        if success:
            status = await integration.get_session_status()
            return jsonify({
                'success': True,
                'message': 'Successfully connected to Telegram',
                'status': status,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to connect to Telegram',
                'timestamp': datetime.now().isoformat()
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return jsonify({
            'success': False,
            'message': f'Connection failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@telegram_enhanced_bp.route('/disconnect', methods=['POST'])
@async_route
async def disconnect_enhanced():
    """Disconnect from Telegram"""
    try:
        user_id = get_user_id()
        integration = EnhancedTelegramIntegration(user_id)
        
        await integration.disconnect()
        
        return jsonify({
            'success': True,
            'message': 'Successfully disconnected from Telegram',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to disconnect: {e}")
        return jsonify({
            'success': False,
            'message': f'Disconnect failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@telegram_enhanced_bp.route('/contacts', methods=['GET'])
@async_route
async def get_enhanced_contacts():
    """Get Telegram contacts with enhanced session management"""
    try:
        user_id = get_user_id()
        integration = EnhancedTelegramIntegration(user_id)
        
        contacts = await integration.get_contacts()
        
        return jsonify({
            'success': True,
            'contacts': contacts,
            'count': len(contacts),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get contacts: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to get contacts: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@telegram_enhanced_bp.route('/conversations', methods=['GET'])
@async_route
async def get_enhanced_conversations():
    """Get Telegram conversations with enhanced session management"""
    try:
        user_id = get_user_id()
        integration = EnhancedTelegramIntegration(user_id)
        
        # Get parameters
        contact_id = request.args.get('contact_id', type=int)
        days_back = request.args.get('days_back', 30, type=int)
        
        conversations = await integration.get_conversations(contact_id, days_back)
        
        return jsonify({
            'success': True,
            'conversations': conversations,
            'count': len(conversations),
            'parameters': {
                'contact_id': contact_id,
                'days_back': days_back
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to get conversations: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@telegram_enhanced_bp.route('/sync-contact', methods=['POST'])
@async_route
async def sync_contact_history():
    """Sync chat history for a specific contact"""
    try:
        user_id = get_user_id()
        integration = EnhancedTelegramIntegration(user_id)
        
        data = request.get_json()
        contact_identifier = data.get('contact_identifier')
        days_back = data.get('days_back', 30)
        
        if not contact_identifier:
            return jsonify({
                'success': False,
                'message': 'contact_identifier is required',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Auto-reconnect if needed
        if not await integration.connect():
            return jsonify({
                'success': False,
                'message': 'Failed to connect to Telegram. Please check your connection.',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        conversation = await integration.sync_contact_history(contact_identifier, days_back)
        
        if conversation:
            message_count = len(conversation.get('messages', []))
            return jsonify({
                'success': True,
                'conversation': conversation,
                'message_count': message_count,
                'message': f'Successfully synced {message_count} messages' if message_count > 0 else 'Contact found but no messages in the specified time period',
                'timestamp': datetime.now().isoformat()
            })
        else:
            # Contact not found is still success but with 0 messages
            return jsonify({
                'success': True,
                'message_count': 0,
                'message': f'Contact "{contact_identifier}" not found or has no accessible messages. Try using their username (without @) or phone number with country code.',
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Failed to sync contact history: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to sync contact history: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@telegram_enhanced_bp.route('/sync-all', methods=['POST'])
@async_route
async def sync_all_history():
    """Sync all chat history with enhanced session management"""
    try:
        user_id = get_user_id()
        sync_manager = TelegramSyncManager(user_id)
        
        data = request.get_json() or {}
        days_back = data.get('days_back', 30)
        
        result = await sync_manager.start_background_sync(days_back)
        
        return jsonify({
            **result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to sync all history: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to sync all history: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@telegram_enhanced_bp.route('/sync-status', methods=['GET'])
@async_route
async def get_sync_status():
    """Get current sync status"""
    try:
        user_id = get_user_id()
        sync_manager = TelegramSyncManager(user_id)
        
        status = await sync_manager.get_sync_status()
        
        return jsonify({
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to get sync status: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@telegram_enhanced_bp.route('/delete-session', methods=['DELETE'])
@async_route
async def delete_enhanced_session():
    """Delete current Telegram session"""
    try:
        user_id = get_user_id()
        integration = EnhancedTelegramIntegration(user_id)
        
        success = await integration.delete_session()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Successfully deleted session',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to delete session',
                'timestamp': datetime.now().isoformat()
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to delete session: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

# Migration endpoints
@telegram_enhanced_bp.route('/migration/status', methods=['GET'])
@async_route
async def get_migration_status():
    """Get migration status between storage backends"""
    try:
        user_id = get_user_id()
        migrator = TelegramSessionMigrator(user_id)
        
        status = await migrator.get_migration_status()
        
        return jsonify({
            'success': True,
            'migration_status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get migration status: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to get migration status: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@telegram_enhanced_bp.route('/migration/to-cloud', methods=['POST'])
@async_route
async def migrate_to_cloud():
    """Migrate session from local to cloud storage"""
    try:
        user_id = get_user_id()
        migrator = TelegramSessionMigrator(user_id)
        
        result = await migrator.migrate_to_cloud()
        
        return jsonify({
            **result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to migrate to cloud: {e}")
        return jsonify({
            'success': False,
            'message': f'Migration failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@telegram_enhanced_bp.route('/migration/to-local', methods=['POST'])
@async_route
async def migrate_to_local():
    """Migrate session from cloud to local storage"""
    try:
        user_id = get_user_id()
        migrator = TelegramSessionMigrator(user_id)
        
        result = await migrator.migrate_to_local()
        
        return jsonify({
            **result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to migrate to local: {e}")
        return jsonify({
            'success': False,
            'message': f'Migration failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@telegram_enhanced_bp.route('/migration/sync', methods=['POST'])
@async_route
async def sync_storages():
    """Sync between local and cloud storage"""
    try:
        user_id = get_user_id()
        migrator = TelegramSessionMigrator(user_id)
        
        result = await migrator.sync_between_storages()
        
        return jsonify({
            **result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to sync storages: {e}")
        return jsonify({
            'success': False,
            'message': f'Sync failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

# ============================================================================
# Phone/OTP/2FA Authentication Endpoints
# ============================================================================

def _load_api_credentials():
    """Load API ID/Hash from encrypted store or env."""
    api_id = None
    api_hash = None
    try:
        from secure_credentials import load_telegram_credentials
        api_id, api_hash = load_telegram_credentials()
    except Exception:
        pass
    if not api_id or not api_hash:
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
    return api_id, api_hash

# Note: These endpoints are registered at the app level in __init__.py
# to maintain backward compatibility at /api/telegram/auth/
def telegram_auth_start():
    """Begin Telegram auth by sending a login code to the phone number."""
    if not _TELETHON_AVAILABLE:
        return jsonify({'success': False, 'message': 'Telethon library not installed'}), 500
    data = request.get_json() or {}
    phone = (data.get('phone') or '').strip()
    if not phone:
        return jsonify({'success': False, 'message': 'Phone number is required.'}), 400

    api_id, api_hash = _load_api_credentials()
    if not api_id or not api_hash:
        return jsonify({'success': False, 'message': 'API credentials not configured.'}), 400

    # Enable input blocking for this request
    global _input_blocked
    _input_blocked = True
    
    try:
        # Use a unique session name for auth to avoid database locks
        import time
        session_name = f"kith_telegram_auth_{int(time.time())}"
        
        async def _send_code():
            # Create client - use MemorySession to avoid any session storage
            from telethon.sessions import MemorySession
            client = TelegramClient(MemorySession(), api_id, api_hash)
            try:
                # Connect directly without checking if connected
                await client.connect()
                # Send code directly - this should work without authorization
                sent = await client.send_code_request(phone)
                phone_code_hash_result = sent.phone_code_hash
                
                # Save the session for later verification
                string_session = client.session.save() if hasattr(client.session, 'save') else ''
                
                await client.disconnect()
                return (phone_code_hash_result, string_session)
            except Exception as e:
                try:
                    if client.is_connected():
                        await client.disconnect()
                except:
                    pass
                raise e
        
        # Use a fresh event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            phone_code_hash, string_session = loop.run_until_complete(_send_code())
        finally:
            loop.close()
        
        PENDING_TG_AUTH[phone] = {
            'session_name': session_name, 
            'phone_code_hash': phone_code_hash,
            'string_session': string_session
        }
        return jsonify({'success': True, 'message': 'Code sent. Check your Telegram app/SMS and enter the code.'})
    except Exception as e:
        import traceback
        logger.error(f"Failed to send code: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Failed to send code: {str(e)}'}), 500
    finally:
        # Disable input blocking
        _input_blocked = False

def telegram_auth_verify():
    """Verify the login code and finalize login (or request password)."""
    if not _TELETHON_AVAILABLE:
        return jsonify({'success': False, 'message': 'Telethon library not installed'}), 500
    data = request.get_json() or {}
    phone = (data.get('phone') or '').strip()
    code = (data.get('code') or '').strip()
    if not phone or not code:
        return jsonify({'success': False, 'message': 'Phone and code are required.'}), 400

    api_id, api_hash = _load_api_credentials()
    if not api_id or not api_hash:
        return jsonify({'success': False, 'message': 'API credentials not configured.'}), 400

    # Enable input blocking
    global _input_blocked
    _input_blocked = True
    
    try:
        from telethon.sessions import StringSession
        session_name = PENDING_TG_AUTH.get(phone, {}).get('session_name') or os.getenv('TELEGRAM_SESSION_NAME', 'kith_telegram_session')
        phone_code_hash = PENDING_TG_AUTH.get(phone, {}).get('phone_code_hash')
        string_session = PENDING_TG_AUTH.get(phone, {}).get('string_session', '')
        
        async def _verify():
            # Use StringSession to avoid file prompts
            client = TelegramClient(StringSession(string_session), api_id, api_hash)
            result = None
            try:
                if not client.is_connected():
                    await client.connect()
                await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
                
                # Save updated session
                updated_session = client.session.save()
                result = ('OK', updated_session)
                await client.disconnect()
            except SessionPasswordNeededError:
                # Save session for password step
                updated_session = client.session.save()
                result = ('PASSWORD_NEEDED', updated_session)
            except PhoneCodeInvalidError:
                result = ('INVALID_CODE', string_session)
                await client.disconnect()
            except Exception as e:
                result = (f'ERROR:{str(e)}', string_session)
                try:
                    await client.disconnect()
                except:
                    pass
            return result
        
        status, updated_session = asyncio.run(_verify())
        
        # Update session in pending auth
        PENDING_TG_AUTH[phone]['string_session'] = updated_session
        
        if status == 'PASSWORD_NEEDED':
            # Store that we need password (don't clear PENDING_TG_AUTH yet)
            return jsonify({'success': False, 'password_required': True, 'message': 'Two-step verification enabled. Please provide your password.'})
        if status == 'INVALID_CODE':
            return jsonify({'success': False, 'message': 'Invalid code. Please try again.'}), 400
        if status.startswith('ERROR:'):
            return jsonify({'success': False, 'message': status[6:]}), 400
        
        # Success - persist session for this user
        try:
            user_id = get_user_id()
            session_mgr = HybridTelegramSession(user_id)
            # For Telethon, the session is stored in a .session file named by session_name automatically.
            # Our Hybrid manager persists an encrypted snapshot; we record the session_name reference.
            awaitable = session_mgr.store_session({'session_name': session_name})
            try:
                asyncio.run(awaitable)
            except RuntimeError:
                # In case of event loop issues, fallback to simple flag
                pass
        except Exception as _:
            # Non-fatal; continue
            pass
        
        # Success - clean up temp auth map
        PENDING_TG_AUTH.pop(phone, None)
        return jsonify({'success': True, 'message': 'Telegram authenticated successfully.'})
    except Exception as e:
        logger.error(f"Failed to verify code: {e}")
        return jsonify({'success': False, 'message': f'Failed to verify code: {str(e)}'}), 500
    finally:
        _input_blocked = False

def telegram_auth_password():
    """Provide 2FA password to complete login."""
    if not _TELETHON_AVAILABLE:
        return jsonify({'success': False, 'message': 'Telethon library not installed'}), 500
    data = request.get_json() or {}
    phone = (data.get('phone') or '').strip()
    password = (data.get('password') or '').strip()
    if not phone or not password:
        return jsonify({'success': False, 'message': 'Phone and password are required.'}), 400

    api_id, api_hash = _load_api_credentials()
    if not api_id or not api_hash:
        return jsonify({'success': False, 'message': 'API credentials not configured.'}), 400

    try:
        session_name = PENDING_TG_AUTH.get(phone, {}).get('session_name') or os.getenv('TELEGRAM_SESSION_NAME', 'kith_telegram_session')
        
        async def _password():
            # Use the SAME session that was used during code verification
            client = TelegramClient(session_name, api_id, api_hash)
            is_authorized = False
            try:
                await client.connect()
                
                # Check if already authorized (from previous step)
                if not await client.is_user_authorized():
                    # Complete the 2FA authentication
                    try:
                        await client.sign_in(password=password)
                    except Exception as e:
                        logger.error(f"Password sign-in error: {e}")
                        await client.disconnect()
                        raise
                
                # Verify we're now authorized
                is_authorized = await client.is_user_authorized()
                await client.disconnect()
            except Exception as e:
                try:
                    await client.disconnect()
                except:
                    pass
                raise e
            
            return is_authorized
        
        success = asyncio.run(_password())
        
        if success:
            # Persist session reference for this user
            try:
                user_id = get_user_id()
                session_mgr = HybridTelegramSession(user_id)
                awaitable = session_mgr.store_session({'session_name': session_name})
                try:
                    asyncio.run(awaitable)
                except RuntimeError:
                    pass
            except Exception:
                pass
            
            PENDING_TG_AUTH.pop(phone, None)
            return jsonify({'success': True, 'message': 'Telegram authenticated successfully with 2FA password.'})
        else:
            return jsonify({'success': False, 'message': 'Authentication failed - please try again from the start.'}), 400
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to complete 2FA authentication: {error_msg}")
        
        # Check for specific errors
        if 'PASSWORD_HASH_INVALID' in error_msg or 'password' in error_msg.lower():
            return jsonify({'success': False, 'message': 'Incorrect 2FA password. Please try again.'}), 400
        else:
            return jsonify({'success': False, 'message': f'Authentication failed: {error_msg}'}), 500

def telegram_auth_cancel():
    """Cancel an in-progress login and clean up."""
    data = request.get_json() or {}
    phone = (data.get('phone') or '').strip()
    if phone and phone in PENDING_TG_AUTH:
        PENDING_TG_AUTH.pop(phone, None)
    return jsonify({'success': True})
