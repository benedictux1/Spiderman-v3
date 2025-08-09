# telegram_worker.py
import os
import requests
import sqlite3
import time
import asyncio
from telethon import TelegramClient
from datetime import datetime, timedelta
from constants import DEFAULT_DB_NAME

# --- CONFIGURATION (loaded from .env) ---
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
KITH_API_URL = os.getenv('KITH_API_URL', 'http://127.0.0.1:5001')  # Important: Use the local loopback for internal calls
KITH_API_TOKEN = os.getenv('KITH_API_TOKEN', 'dev_token')
SESSION_NAME = 'kith_telegram_session_worker'

# Check for required Telegram API credentials
if not API_ID or not API_HASH:
    print("ERROR: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")
    print("Get these credentials from https://my.telegram.org/apps")
    exit(1)

def get_db_connection():
    """Get database connection with retry logic."""
    max_retries = 5
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(DEFAULT_DB_NAME, timeout=30.0)
            conn.execute('PRAGMA journal_mode=WAL')  # Better for concurrent access
            conn.execute('PRAGMA synchronous=NORMAL')  # Better performance
            conn.execute('PRAGMA temp_store=memory')  # Use memory for temp tables
            conn.execute('PRAGMA busy_timeout=30000')  # 30 second busy timeout
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            
            # Test the connection
            conn.execute('SELECT 1').fetchone()
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

def update_task_status(task_id, status, message="", error="", progress=None):
    """Helper function to update the task status in the database."""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            try:
                # First, verify the task exists
                cursor = conn.execute('SELECT id FROM import_tasks WHERE id = ?', (task_id,))
                if not cursor.fetchone():
                    print(f"Warning: Task {task_id} not found in database")
                    return
                
                # Prepare update parameters
                update_params = [status, message[:1000] if message else "", error[:2000] if error else ""]
                
                if progress is not None:
                    progress = max(0, min(100, int(progress)))  # Clamp between 0-100
                    update_params.append(progress)
                    update_params.append(task_id)
                    
                    conn.execute('''
                        UPDATE import_tasks 
                        SET status = ?, status_message = ?, error_details = ?, progress = ?
                        WHERE id = ?
                    ''', update_params)
                else:
                    update_params.append(task_id)
                    conn.execute('''
                        UPDATE import_tasks 
                        SET status = ?, status_message = ?, error_details = ?
                        WHERE id = ?
                    ''', update_params)
                
                # Set completion timestamp for final states
                if status in ['completed', 'failed']:
                    conn.execute('''
                        UPDATE import_tasks 
                        SET completed_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (task_id,))
                
                conn.commit()
                print(f"[Task {task_id}] Status: {status} ({progress or ''}%) - {message}")
                return  # Success, exit retry loop
                
            finally:
                conn.close()
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error updating task status (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                print(f"Failed to update task status after {max_retries} attempts: {e}")

def run_telegram_import(task_id, identifier, contact_id, days_back):
    """
    Sync wrapper to set up the asyncio event loop and run the async import task.
    This is the entry point called by the subprocess.
    """
    # Get or create an event loop for the current thread
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # 'get_running_loop' fails if no loop is set
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(
            _async_run_telegram_import(task_id, identifier, contact_id, days_back)
        )
    except Exception as e:
        # Catch-all for any unexpected errors during async execution
        update_task_status(task_id, "failed", "A critical error occurred in the async runner.", str(e), progress=100)


async def _async_run_telegram_import(task_id, identifier, contact_id, days_back):
    """
    The main async background job function. Handles connection, fetching, and processing.
    """
    update_task_status(task_id, "connecting", "Initializing import...", progress=5)

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    try:
        # Connect with a timeout to prevent hangs
        update_task_status(task_id, "connecting", "Connecting to Telegram...", progress=10)
        await asyncio.wait_for(client.connect(), timeout=45.0)

        if not await client.is_user_authorized():
            update_task_status(task_id, "failed", "Telegram authentication required.",
                               "Session is not authorized. You may need to run an interactive script once to log in.", progress=100)
            return

        update_task_status(task_id, "fetching", f"Finding contact '{identifier}'...", progress=20)
        entity = await client.get_entity(identifier)

        conn = get_db_connection()
        try:
            cursor = conn.execute('SELECT telegram_last_sync FROM contacts WHERE id = ?', (contact_id,))
            result = cursor.fetchone()
            last_sync_timestamp = result['telegram_last_sync'] if result and result['telegram_last_sync'] else None
        finally:
            conn.close()
        
        if last_sync_timestamp:
            since_date = datetime.fromisoformat(last_sync_timestamp)
            status_msg = f"Fetching new messages since last sync: {since_date.strftime('%Y-%m-%d %H:%M')}..."
        else:
            since_date = datetime.now() - timedelta(days=days_back)
            status_msg = f"Fetching messages from last {days_back} days..."
        update_task_status(task_id, "fetching", status_msg, progress=30)

        transcript = []
        message_count = 0
        # Add a reasonable limit to prevent fetching too many messages
        async for message in client.iter_messages(entity, offset_date=since_date, reverse=True, limit=2000):
            if message.text:
                sender_name = "Me" if message.out else (entity.first_name or entity.username or str(entity.id))
                formatted_message = f"[{message.date.strftime('%Y-%m-%d %H:%M')}] {sender_name}: {message.text}"
                transcript.append(formatted_message)
                message_count += 1
                if message_count % 20 == 0:
                    update_task_status(task_id, "fetching", f"Fetched {message_count} messages...", progress=min(80, 30 + (message_count // 50)))

        if not transcript:
            update_task_status(task_id, "completed", "No new messages found.", progress=100)
            return

        full_transcript = "\n".join(transcript)
        update_task_status(task_id, "processing", f"Sending {message_count} messages for AI analysis...", progress=85)

        headers = {'Authorization': f'Bearer {KITH_API_TOKEN}', 'Content-Type': 'application/json'}
        payload = {'contact_id': contact_id, 'transcript': full_transcript}
        
        response = requests.post(f"{KITH_API_URL}/api/process-transcript", headers=headers, json=payload, timeout=300)

        if response.status_code == 200:
            conn = get_db_connection()
            try:
                # Use ISO format for timezone-aware compatibility
                conn.execute('UPDATE contacts SET telegram_last_sync = ? WHERE id = ?', (datetime.now().isoformat(), contact_id))
                conn.commit()
            finally:
                conn.close()
            update_task_status(task_id, "completed", f"Successfully imported and analyzed {message_count} messages.", progress=100)
        else:
            error_detail = response.text
            try:
                error_detail = response.json().get('error', response.text)
            except:
                pass
            update_task_status(task_id, "failed", f"API processing failed: HTTP {response.status_code}", error_detail, progress=100)

    except asyncio.TimeoutError:
        update_task_status(task_id, "failed", "Connection to Telegram timed out.", "Could not connect to Telegram servers within 45 seconds.", progress=100)
    except ValueError as e:
        update_task_status(task_id, "failed", f"Could not find user '{identifier}'", f"Telegram entity not found: {str(e)}", progress=100)
    except Exception as e:
        update_task_status(task_id, "failed", "An unexpected error occurred during import.", str(e), progress=100)
    finally:
        if client.is_connected():
            await client.disconnect() 