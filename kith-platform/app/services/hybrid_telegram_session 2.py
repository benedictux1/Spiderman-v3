#!/usr/bin/env python3
"""
Hybrid Telegram Session Management
Works seamlessly both locally and on Render with automatic environment detection.
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import base64

# Configure logging
logger = logging.getLogger(__name__)

class HybridTelegramSession:
    """
    Hybrid Telegram session manager that works both locally and on Render.
    Automatically detects environment and uses appropriate storage backend.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.is_render = self._detect_environment()
        self.encryption_key = self._get_encryption_key()
        self.storage_backend = self._get_storage_backend()
        self.storage = self._init_storage()
        
        logger.info(f"Initialized HybridTelegramSession for user {user_id} - "
                   f"Environment: {'Render' if self.is_render else 'Local'}, "
                   f"Backend: {self.storage_backend}")
    
    def _detect_environment(self) -> bool:
        """Detect if running on Render or locally"""
        return (
            os.getenv('RENDER') == 'true' or 
            os.getenv('RENDER_EXTERNAL_HOSTNAME') is not None or
            os.getenv('TELEGRAM_STORAGE_BACKEND') == 'cloud'
        )
    
    def _get_storage_backend(self) -> str:
        """Get storage backend based on environment"""
        if self.is_render:
            return os.getenv('TELEGRAM_STORAGE_BACKEND', 's3')
        else:
            return 'local'
    
    def _get_encryption_key(self) -> bytes:
        """Get encryption key for session data"""
        key = os.getenv('TELEGRAM_ENCRYPTION_KEY')
        if not key:
            # Generate a key for local development
            key = Fernet.generate_key().decode()
            # Store it for consistency
            os.environ['TELEGRAM_ENCRYPTION_KEY'] = key
            logger.info("Generated new encryption key for local development")
        return key.encode() if isinstance(key, str) else key
    
    def _init_storage(self):
        """Initialize appropriate storage backend"""
        if self.storage_backend == 'local':
            return LocalTelegramStorage(self.user_id)
        elif self.storage_backend == 's3':
            return S3TelegramStorage(self.user_id)
        elif self.storage_backend == 'redis':
            return RedisTelegramStorage(self.user_id)
        else:
            raise ValueError(f"Unsupported storage backend: {self.storage_backend}")
    
    def _encrypt_session(self, session_data: Dict[str, Any]) -> bytes:
        """Encrypt session data"""
        try:
            fernet = Fernet(self.encryption_key)
            json_data = json.dumps(session_data, default=str)
            return fernet.encrypt(json_data.encode())
        except Exception as e:
            logger.error(f"Failed to encrypt session data: {e}")
            raise
    
    def _decrypt_session(self, encrypted_data: bytes) -> Dict[str, Any]:
        """Decrypt session data"""
        try:
            fernet = Fernet(self.encryption_key)
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to decrypt session data: {e}")
            raise
    
    async def store_session(self, session_data: Dict[str, Any]) -> bool:
        """Store session data using appropriate backend"""
        try:
            logger.info(f"Storing session for user {self.user_id}")
            
            # Add metadata
            session_data['_metadata'] = {
                'user_id': self.user_id,
                'stored_at': datetime.now().isoformat(),
                'environment': 'render' if self.is_render else 'local',
                'storage_backend': self.storage_backend
            }
            
            # Encrypt session data
            encrypted_data = self._encrypt_session(session_data)
            
            # Store using appropriate backend
            success = await self.storage.store(encrypted_data)
            
            if success:
                logger.info(f"Successfully stored session for user {self.user_id}")
            else:
                logger.error(f"Failed to store session for user {self.user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to store session: {e}")
            return False
    
    async def restore_session(self) -> Optional[Dict[str, Any]]:
        """Restore session data using appropriate backend"""
        try:
            logger.info(f"Restoring session for user {self.user_id}")
            
            # Load encrypted data
            encrypted_data = await self.storage.load()
            
            if not encrypted_data:
                logger.info(f"No session found for user {self.user_id}")
                return None
            
            # Decrypt session data
            session_data = self._decrypt_session(encrypted_data)
            
            # Validate session metadata
            metadata = session_data.get('_metadata', {})
            if metadata.get('user_id') != self.user_id:
                logger.warning(f"Session user_id mismatch: expected {self.user_id}, got {metadata.get('user_id')}")
                return None
            
            logger.info(f"Successfully restored session for user {self.user_id}")
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to restore session: {e}")
            return None
    
    async def delete_session(self) -> bool:
        """Delete session data"""
        try:
            logger.info(f"Deleting session for user {self.user_id}")
            success = await self.storage.delete()
            
            if success:
                logger.info(f"Successfully deleted session for user {self.user_id}")
            else:
                logger.error(f"Failed to delete session for user {self.user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    async def has_session(self) -> bool:
        """Check if session exists"""
        try:
            return await self.storage.exists()
        except Exception as e:
            logger.error(f"Failed to check session existence: {e}")
            return False
    
    async def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get session metadata without loading full session"""
        try:
            session_data = await self.restore_session()
            if session_data:
                return session_data.get('_metadata', {})
            return None
        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return None


class LocalTelegramStorage:
    """Local file-based storage for development"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.session_dir = Path.home() / '.kith' / 'telegram_sessions'
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.session_dir / f"{user_id}_session.enc"
        self.backup_file = self.session_dir / f"{user_id}_session_backup.enc"
        self.metadata_file = self.session_dir / f"{user_id}_metadata.json"
    
    async def store(self, encrypted_data: bytes) -> bool:
        """Store session locally with backup"""
        try:
            # Create backup of existing session
            if self.session_file.exists():
                self.session_file.rename(self.backup_file)
            
            # Write new session
            with open(self.session_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Write metadata
            metadata = {
                'user_id': self.user_id,
                'stored_at': datetime.now().isoformat(),
                'file_size': len(encrypted_data),
                'backup_exists': self.backup_file.exists()
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Verify write
            if self.session_file.exists() and self.session_file.stat().st_size > 0:
                logger.info(f"Successfully stored local session for user {self.user_id}")
                return True
            else:
                # Restore backup if write failed
                if self.backup_file.exists():
                    self.backup_file.rename(self.session_file)
                    logger.warning(f"Restored backup session for user {self.user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Local storage failed: {e}")
            return False
    
    async def load(self) -> Optional[bytes]:
        """Load session from local storage"""
        try:
            if self.session_file.exists():
                with open(self.session_file, 'rb') as f:
                    data = f.read()
                logger.info(f"Successfully loaded local session for user {self.user_id}")
                return data
            return None
        except Exception as e:
            logger.error(f"Local load failed: {e}")
            return None
    
    async def delete(self) -> bool:
        """Delete local session"""
        try:
            success = True
            if self.session_file.exists():
                self.session_file.unlink()
            if self.backup_file.exists():
                self.backup_file.unlink()
            if self.metadata_file.exists():
                self.metadata_file.unlink()
            
            logger.info(f"Successfully deleted local session for user {self.user_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete local session: {e}")
            return False
    
    async def exists(self) -> bool:
        """Check if local session exists"""
        return self.session_file.exists() and self.session_file.stat().st_size > 0


class S3TelegramStorage:
    """S3-based storage for Render deployment"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.bucket_name = os.getenv('TELEGRAM_SESSION_BUCKET', 'kith-telegram-sessions')
        self.session_key = f"telegram-sessions/{user_id}/session.enc"
        self.backup_key = f"telegram-sessions/{user_id}/session_backup.enc"
        self.metadata_key = f"telegram-sessions/{user_id}/metadata.json"
        
        # Initialize S3 client
        try:
            import boto3
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    async def store(self, encrypted_data: bytes) -> bool:
        """Store session in S3 with backup"""
        try:
            # Create backup
            try:
                self.s3_client.copy_object(
                    Bucket=self.bucket_name,
                    CopySource={'Bucket': self.bucket_name, 'Key': self.session_key},
                    Key=self.backup_key
                )
            except:
                pass  # No existing session to backup
            
            # Store new session
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=self.session_key,
                Body=encrypted_data,
                ServerSideEncryption='AES256'
            )
            
            # Store metadata
            metadata = {
                'user_id': self.user_id,
                'stored_at': datetime.now().isoformat(),
                'size': len(encrypted_data),
                'storage_backend': 's3'
            }
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=self.metadata_key,
                Body=json.dumps(metadata).encode(),
                ServerSideEncryption='AES256'
            )
            
            logger.info(f"Successfully stored S3 session for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"S3 storage failed: {e}")
            return False
    
    async def load(self) -> Optional[bytes]:
        """Load session from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self.session_key
            )
            data = response['Body'].read()
            logger.info(f"Successfully loaded S3 session for user {self.user_id}")
            return data
        except Exception as e:
            logger.error(f"S3 load failed: {e}")
            return None
    
    async def delete(self) -> bool:
        """Delete S3 session"""
        try:
            # Delete session and metadata
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=self.session_key)
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=self.metadata_key)
            
            logger.info(f"Successfully deleted S3 session for user {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete S3 session: {e}")
            return False
    
    async def exists(self) -> bool:
        """Check if S3 session exists"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=self.session_key)
            return True
        except:
            return False


class RedisTelegramStorage:
    """Redis-based storage for Render deployment"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.session_key = f"telegram:session:{user_id}"
        self.backup_key = f"telegram:session_backup:{user_id}"
        self.metadata_key = f"telegram:metadata:{user_id}"
        self.session_ttl = int(os.getenv('TELEGRAM_SESSION_TTL', '2592000'))  # 30 days
        
        # Initialize Redis client
        try:
            import redis
            self.redis_client = redis.from_url(os.getenv('REDIS_URL'))
        except ImportError:
            logger.error("redis not installed. Install with: pip install redis")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise
    
    async def store(self, encrypted_data: bytes) -> bool:
        """Store session in Redis with backup"""
        try:
            # Create backup
            existing = self.redis_client.get(self.session_key)
            if existing:
                self.redis_client.setex(self.backup_key, self.session_ttl, existing)
            
            # Store new session
            self.redis_client.setex(self.session_key, self.session_ttl, encrypted_data)
            
            # Store metadata
            metadata = {
                'user_id': self.user_id,
                'stored_at': datetime.now().isoformat(),
                'size': len(encrypted_data),
                'storage_backend': 'redis',
                'ttl': self.session_ttl
            }
            
            self.redis_client.setex(
                self.metadata_key, 
                self.session_ttl, 
                json.dumps(metadata)
            )
            
            logger.info(f"Successfully stored Redis session for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Redis storage failed: {e}")
            return False
    
    async def load(self) -> Optional[bytes]:
        """Load session from Redis"""
        try:
            data = self.redis_client.get(self.session_key)
            if data:
                logger.info(f"Successfully loaded Redis session for user {self.user_id}")
                return data
            return None
        except Exception as e:
            logger.error(f"Redis load failed: {e}")
            return None
    
    async def delete(self) -> bool:
        """Delete Redis session"""
        try:
            self.redis_client.delete(self.session_key)
            self.redis_client.delete(self.metadata_key)
            
            logger.info(f"Successfully deleted Redis session for user {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Redis session: {e}")
            return False
    
    async def exists(self) -> bool:
        """Check if Redis session exists"""
        try:
            return self.redis_client.exists(self.session_key) > 0
        except:
            return False
