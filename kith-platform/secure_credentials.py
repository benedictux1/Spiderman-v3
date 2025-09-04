#!/usr/bin/env python3
"""
Secure Credential Manager for Telegram API credentials
Provides encrypted storage and retrieval of sensitive API keys.
"""

import os
import json
import hashlib
import platform
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging

logger = logging.getLogger(__name__)

class SecureCredentialManager:
    """Manages encrypted storage of API credentials."""
    
    def __init__(self, credentials_file='.api_credentials.enc'):
        self.credentials_file = credentials_file
        self.key_file = '.api_key.enc'
        
    def _generate_system_salt(self):
        """Generate a salt based on system characteristics."""
        # Use system info to create a consistent but unique salt
        system_info = f"{platform.node()}-{platform.system()}-{platform.machine()}"
        return hashlib.sha256(system_info.encode()).digest()[:16]
    
    def _get_master_key(self):
        """Get or create the master encryption key."""
        if os.path.exists(self.key_file):
            # Load existing key
            try:
                with open(self.key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Could not load existing key: {e}")
        
        # Generate new key
        key = Fernet.generate_key()
        
        # Save key to file with restricted permissions
        try:
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions (owner read/write only)
            os.chmod(self.key_file, 0o600)
            logger.info("Generated new encryption key")
        except Exception as e:
            logger.error(f"Could not save encryption key: {e}")
            raise
            
        return key
    
    def _derive_key_from_password(self, password: str):
        """Derive encryption key from password using PBKDF2."""
        salt = self._generate_system_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def save_credentials(self, api_id: str, api_hash: str, use_password: bool = False, password: str = None):
        """Save encrypted credentials to file."""
        try:
            # Choose encryption method
            if use_password and password:
                key = self._derive_key_from_password(password)
                logger.info("Using password-based encryption")
            else:
                key = self._get_master_key()
                logger.info("Using system-based encryption")
            
            # Create cipher
            cipher = Fernet(key)
            
            # Prepare credentials data
            credentials = {
                'api_id': api_id,
                'api_hash': api_hash,
                'timestamp': str(int(os.path.getmtime(__file__)) if os.path.exists(__file__) else 0),
                'system': platform.node()
            }
            
            # Encrypt credentials
            credentials_json = json.dumps(credentials)
            encrypted_data = cipher.encrypt(credentials_json.encode())
            
            # Save to file
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            os.chmod(self.credentials_file, 0o600)
            
            logger.info("Credentials saved successfully with encryption")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            return False
    
    def load_credentials(self, password: str = None):
        """Load and decrypt credentials from file."""
        if not os.path.exists(self.credentials_file):
            logger.info("No encrypted credentials file found")
            return None, None
        
        try:
            # Load encrypted data
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Try password-based decryption first if password provided
            if password:
                try:
                    key = self._derive_key_from_password(password)
                    cipher = Fernet(key)
                    decrypted_data = cipher.decrypt(encrypted_data)
                    credentials = json.loads(decrypted_data.decode())
                    logger.info("Credentials decrypted with password")
                    return credentials['api_id'], credentials['api_hash']
                except Exception as e:
                    logger.warning(f"Password decryption failed: {e}")
            
            # Try system-based decryption
            try:
                key = self._get_master_key()
                cipher = Fernet(key)
                decrypted_data = cipher.decrypt(encrypted_data)
                credentials = json.loads(decrypted_data.decode())
                
                # Verify system match for additional security
                if credentials.get('system') != platform.node():
                    logger.warning("System mismatch - credentials may be from different machine")
                
                logger.info("Credentials decrypted with system key")
                return credentials['api_id'], credentials['api_hash']
                
            except Exception as e:
                logger.error(f"System decryption failed: {e}")
                return None, None
                
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return None, None
    
    def delete_credentials(self):
        """Securely delete stored credentials."""
        deleted_files = []
        
        # Delete credentials file
        if os.path.exists(self.credentials_file):
            try:
                os.remove(self.credentials_file)
                deleted_files.append('credentials')
                logger.info("Encrypted credentials file deleted")
            except Exception as e:
                logger.error(f"Failed to delete credentials file: {e}")
        
        # Delete key file
        if os.path.exists(self.key_file):
            try:
                os.remove(self.key_file)
                deleted_files.append('encryption key')
                logger.info("Encryption key file deleted")
            except Exception as e:
                logger.error(f"Failed to delete key file: {e}")
        
        return deleted_files
    
    def credentials_exist(self):
        """Check if encrypted credentials exist."""
        return os.path.exists(self.credentials_file)
    
    def get_credential_info(self):
        """Get info about stored credentials without decrypting."""
        if not self.credentials_exist():
            return None
        
        try:
            stat = os.stat(self.credentials_file)
            return {
                'exists': True,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'size': stat.st_size
            }
        except Exception as e:
            logger.error(f"Failed to get credential info: {e}")
            return None


# Convenience functions for easy integration
_credential_manager = None

def get_credential_manager():
    """Get singleton credential manager instance."""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = SecureCredentialManager()
    return _credential_manager

def save_telegram_credentials(api_id: str, api_hash: str, password: str = None):
    """Save Telegram credentials with encryption."""
    manager = get_credential_manager()
    use_password = password is not None
    return manager.save_credentials(api_id, api_hash, use_password, password)

def load_telegram_credentials(password: str = None):
    """Load Telegram credentials with decryption."""
    manager = get_credential_manager()
    return manager.load_credentials(password)

def delete_telegram_credentials():
    """Delete all Telegram credential files."""
    manager = get_credential_manager()
    return manager.delete_credentials()

def telegram_credentials_exist():
    """Check if encrypted Telegram credentials exist."""
    manager = get_credential_manager()
    return manager.credentials_exist()


if __name__ == "__main__":
    # Test the credential manager
    logging.basicConfig(level=logging.INFO)
    
    manager = SecureCredentialManager()
    
    # Test save and load
    print("Testing credential encryption...")
    success = manager.save_credentials("123456", "test_hash_123456789")
    print(f"Save result: {success}")
    
    if success:
        api_id, api_hash = manager.load_credentials()
        print(f"Loaded: API ID = {api_id}, API Hash = {api_hash}")
        
        # Test deletion
        deleted = manager.delete_credentials()
        print(f"Deleted files: {deleted}")

# OpenAI API Key Management Functions
def save_openai_api_key(api_key, model=None, password=None):
    """Save OpenAI API key with optional model preference."""
    try:
        manager = SecureCredentialManager('.openai_credentials.enc')
        
        # Use the existing save_credentials method (api_key as first param, model as second)
        success = manager.save_credentials(api_key, model or 'gpt-4-turbo', password)
        if success:
            logger.info("🔐 OpenAI API key saved with encryption")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to save OpenAI API key: {e}")
        return False

def load_openai_api_key():
    """Load encrypted OpenAI API key and model."""
    try:
        manager = SecureCredentialManager('.openai_credentials.enc')
        api_key, model = manager.load_credentials()
        if api_key and model:
            logger.info("🔐 OpenAI credentials decrypted successfully")
            return api_key, model
        return None, None
    except Exception as e:
        logger.error(f"Failed to load OpenAI API key: {e}")
        return None, None

def delete_openai_api_key():
    """Delete encrypted OpenAI API key."""
    try:
        manager = SecureCredentialManager('.openai_credentials.enc')
        success = manager.delete_credentials()
        if success:
            logger.info("🔐 OpenAI API key deleted")
        return success
    except Exception as e:
        logger.error(f"Failed to delete OpenAI API key: {e}")
        return False
