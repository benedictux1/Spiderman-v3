# telegram_worker.py
import os
import requests
import sqlite3
import time
import asyncio
import logging
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import UserNotParticipantError
from datetime import datetime, timedelta
from constants import DEFAULT_DB_NAME

# --- LOGGING SETUP ---
LOG_FILE = os.path.join(os.path.dirname(__file__), 'kith_platform.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# --- CONFIGURATION (env or encrypted) ---
KITH_API_URL = os.getenv('KITH_API_URL', 'http://127.0.0.1:5001')  # Important: Use the local loopback for internal calls
KITH_API_TOKEN = os.getenv('KITH_API_TOKEN', 'dev_token')
SESSION_NAME = os.getenv('TELEGRAM_SESSION_NAME', 'kith_telegram_session')

def _load_api_credentials():
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    if api_id and api_hash:
        return api_id, api_hash
    try:
        from secure_credentials import load_telegram_credentials
        api_id, api_hash = load_telegram_credentials()
    except Exception:
        api_id, api_hash = None, None
    return api_id, api_hash

API_ID, API_HASH = _load_api_credentials()
# Always use absolute path for the Telethon session to avoid cwd inconsistencies
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_PATH = os.path.join(BASE_DIR, SESSION_NAME)

# Check for required Telegram API credentials
if not API_ID or not API_HASH:
    logging.error("Missing Telegram API credentials. Save them in the app (encrypted) or set env vars.")
    # We don't exit immediately; downstream code will surface a clearer error when connecting

def get_db_connection():
    """Get database connection with retry logic."""
    max_retries = 5
    retry_delay = 1
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_DB_NAME)
    
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_path, timeout=30.0)
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute('PRAGMA journal_mode=WAL')  # Better for concurrent access
            conn.execute('PRAGMA synchronous=NORMAL')  # Better performance
            conn.execute('PRAGMA temp_store=memory')  # Use memory for temp tables
            conn.execute('PRAGMA busy_timeout=5000')  # 5 second busy timeout
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            
            # Test the connection
            conn.execute('SELECT 1').fetchone()
            logging.info("Database connection successful.")
            return conn
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e).lower() and attempt < max_retries - 1:
                logging.warning(f"Database locked, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logging.error(f"Final attempt to connect to database failed: {e}", exc_info=True)
                raise
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"Final attempt to connect to database failed: {e}", exc_info=True)
                raise e
            logging.warning(f"Database connection error, retrying... (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(retry_delay)
            retry_delay *= 2

def update_task_status(task_id, status, message="", error="", progress=None):
    """Helper function to update the task status in the database."""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            if not conn:
                logging.error(f"[Task {task_id}] Could not connect to the database to update status.")
                return
                
            try:
                # First, verify the task exists
                cursor = conn.execute('SELECT id FROM import_tasks WHERE id = ?', (task_id,))
                if not cursor.fetchone():
                    logging.warning(f"Warning: Task {task_id} not found in database for status update.")
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
                logging.info(f"[Task {task_id}] Status: {status} ({progress or ''}%) - {message}")
                return  # Success, exit retry loop
                
            finally:
                conn.close()
                
        except Exception as e:
            if attempt < max_retries - 1:
                logging.error(f"Error updating task status (attempt {attempt + 1}/{max_retries}): {e}", exc_info=True)
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logging.error(f"Failed to update task status after {max_retries} attempts: {e}", exc_info=True)

def run_telegram_import(task_id, identifier, contact_id, days_back):
    """
    Sync wrapper to set up the asyncio event loop and run the async import task.
    This is the entry point called by the subprocess.
    """
    logging.info(f"[Task {task_id}] Starting Telegram import for identifier: '{identifier}', contact_id: {contact_id}, days: {days_back}")
    
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
        logging.info(f"[Task {task_id}] Async import task finished.")
    except Exception as e:
        # Catch-all for any unexpected errors during async execution
        error_msg = f"A critical error occurred in the async runner: {e}"
        logging.error(f"[Task {task_id}] {error_msg}", exc_info=True)
        update_task_status(task_id, "failed", "A critical error occurred during the import process.", f"Error: {e.__class__.__name__} - {str(e)}", progress=100)
    finally:
        if loop.is_running():
            loop.close()
        logging.info(f"[Task {task_id}] Event loop closed.")


async def _async_run_telegram_import(task_id, identifier, contact_id, days_back):
    """
    The main async background job function. Handles connection, fetching, and processing.
    """
    update_task_status(task_id, "connecting", "Initializing import...", progress=5)

    client = None
    try:
        client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
        update_task_status(task_id, "connecting", "Connecting to Telegram...", progress=10)
        
        # Connect with a timeout to prevent hangs
        try:
            await asyncio.wait_for(client.connect(), timeout=45.0)
            logging.info(f"[Task {task_id}] Successfully connected to Telegram.")
        except asyncio.TimeoutError:
            raise ConnectionError("Connection to Telegram timed out after 45 seconds.")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Telegram: {e}")

        if not await client.is_user_authorized():
            logging.error(f"[Task {task_id}] Telegram session is not authorized.")
            update_task_status(task_id, "failed", "Telegram authentication required.",
                               "Session is not authorized. Run an interactive script to log in.", progress=100)
            return

        update_task_status(task_id, "fetching", f"Finding contact '{identifier}'...", progress=20)
        try:
            entity = await client.get_entity(identifier)
            logging.info(f"[Task {task_id}] Found entity for '{identifier}': {entity.id}")
        except ValueError:
             # This error is often thrown for incorrect usernames or non-existent entities.
            raise ValueError(f"Could not find user or channel '{identifier}'. Please check the username/handle.")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred while fetching entity '{identifier}': {e}")


        conn = get_db_connection()
        if not conn:
            raise sqlite3.OperationalError("Could not establish database connection to fetch last sync time.")
            
        try:
            cursor = conn.execute('SELECT telegram_last_sync FROM contacts WHERE id = ?', (contact_id,))
            result = cursor.fetchone()
            last_sync_timestamp = result['telegram_last_sync'] if result and result['telegram_last_sync'] else None
            logging.info(f"[Task {task_id}] Last sync for contact {contact_id} was: {last_sync_timestamp}")
        finally:
            conn.close()
        
        if last_sync_timestamp:
            since_date = datetime.fromisoformat(last_sync_timestamp)
            status_msg = f"Fetching new messages since last sync: {since_date.strftime('%Y-%m-%d %H:%M')}..."
        else:
            since_date = datetime.now() - timedelta(days=int(days_back))
            status_msg = f"Fetching messages from last {days_back} days..."
        update_task_status(task_id, "fetching", status_msg, progress=30)

        transcript = []
        message_count = 0
        total_fetched = 0
        limit = 2000 # Safety limit
        
        update_task_status(task_id, "fetching", "Starting message retrieval...", progress=35)
        
        try:
            # Add a reasonable limit to prevent fetching too many messages
            async for message in client.iter_messages(entity, offset_date=since_date, reverse=True, limit=limit):
                total_fetched += 1
                if message and message.text:
                    sender_name = "Me" if message.out else (entity.first_name or entity.username or str(entity.id))
                    formatted_message = f"[{message.date.strftime('%Y-%m-%d %H:%M')}] {sender_name}: {message.text}"
                    transcript.append(formatted_message)
                    message_count += 1
                    
                    if message_count % 20 == 0:
                        progress = min(80, 35 + int((total_fetched / limit) * 45))
                        update_task_status(task_id, "fetching", f"Fetched {message_count} messages...", progress=progress)

            logging.info(f"[Task {task_id}] Fetched a total of {message_count} messages with text content.")

        except UserNotParticipantError:
            raise PermissionError(f"You are not a participant of the chat with '{identifier}'. Cannot fetch messages.")
        except Exception as e:
            raise RuntimeError(f"An error occurred while fetching messages for '{identifier}': {e}")


        if not transcript:
            update_task_status(task_id, "completed", "No new messages found.", progress=100)
            logging.info(f"[Task {task_id}] No new messages to process for '{identifier}'.")
            return

        full_transcript = "\n".join(transcript)
        update_task_status(task_id, "processing", f"Sending {message_count} messages for AI analysis...", progress=85)
        logging.info(f"[Task {task_id}] Sending {message_count} messages for analysis.")

        try:
            headers = {'Authorization': f'Bearer {KITH_API_TOKEN}', 'Content-Type': 'application/json'}
            payload = {'contact_id': contact_id, 'transcript': full_transcript}
            
            # Enhanced logging for debugging
            logging.info(f"[Task {task_id}] Sending transcript to API. Length: {len(full_transcript)} chars")
            logging.info(f"[Task {task_id}] First 200 chars: {repr(full_transcript[:200])}")
            
            response = requests.post(f"{KITH_API_URL}/api/process-transcript", headers=headers, json=payload, timeout=300)
            response.raise_for_status() # Raise an exception for bad status codes

            logging.info(f"[Task {task_id}] Successfully processed transcript via API.")
        except requests.exceptions.RequestException as e:
            error_details = f"API request failed: {e}. "
            if e.response:
                error_details += f"Status: {e.response.status_code}, Body: {e.response.text}"
            logging.error(f"[Task {task_id}] {error_details}")
            logging.error(f"[Task {task_id}] Failed transcript length: {len(full_transcript)} chars")
            logging.error(f"[Task {task_id}] Failed transcript sample: {repr(full_transcript[:500])}")
            raise ConnectionError(error_details)
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred during API call: {e}")


        conn = get_db_connection()
        if not conn:
            # Log the error but don't fail the entire task, as processing is complete.
            logging.error(f"[Task {task_id}] Could not connect to DB to update last_sync, but import was successful.")
        else:
            try:
                # Use ISO format for timezone-aware compatibility
                conn.execute('UPDATE contacts SET telegram_last_sync = ? WHERE id = ?', (datetime.now().isoformat(), contact_id))
                conn.commit()
                logging.info(f"[Task {task_id}] Successfully updated last_sync for contact {contact_id}.")
            except Exception as e:
                logging.error(f"[Task {task_id}] Failed to update last_sync timestamp for contact {contact_id}: {e}", exc_info=True)
            finally:
                conn.close()
                
        update_task_status(task_id, "completed", f"Successfully imported and analyzed {message_count} messages.", progress=100)

    except (ValueError, PermissionError) as e:
        # User-facing errors (e.g., bad username, not in chat)
        logging.warning(f"[Task {task_id}] Import failed with a user-correctable error: {e}")
        update_task_status(task_id, "failed", str(e), str(e), progress=100)
    except (ConnectionError, sqlite3.OperationalError) as e:
        # System-level errors (e.g., can't connect to Telegram/DB)
        logging.error(f"[Task {task_id}] Import failed due to a connection or database error: {e}", exc_info=True)
        update_task_status(task_id, "failed", "A system error occurred.", str(e), progress=100)
    except Exception as e:
        # All other unexpected errors
        logging.critical(f"[Task {task_id}] An unexpected critical error occurred during import: {e}", exc_info=True)
        update_task_status(task_id, "failed", "An unexpected error occurred.", str(e), progress=100)
    finally:
        if client and client.is_connected():
            await client.disconnect()
            logging.info(f"[Task {task_id}] Disconnected from Telegram.")
        logging.info(f"[Task {task_id}] Import task for '{identifier}' concluded.") 