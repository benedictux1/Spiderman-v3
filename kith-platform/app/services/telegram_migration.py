#!/usr/bin/env python3
"""
Telegram Session Migration System
Handles migration between local and cloud storage backends.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from .hybrid_telegram_session import HybridTelegramSession, LocalTelegramStorage, S3TelegramStorage, RedisTelegramStorage

logger = logging.getLogger(__name__)

class TelegramSessionMigrator:
    """
    Handles migration of Telegram sessions between different storage backends.
    Supports migration from local to cloud and vice versa.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.is_render = self._detect_environment()
        
    def _detect_environment(self) -> bool:
        """Detect if running on Render or locally"""
        return (
            os.getenv('RENDER') == 'true' or 
            os.getenv('RENDER_EXTERNAL_HOSTNAME') is not None or
            os.getenv('TELEGRAM_STORAGE_BACKEND') == 'cloud'
        )
    
    async def migrate_to_cloud(self) -> Dict[str, Any]:
        """
        Migrate local sessions to cloud storage.
        Returns migration status and details.
        """
        try:
            logger.info(f"Starting migration to cloud for user {self.user_id}")
            
            # Initialize storage backends
            local_storage = LocalTelegramStorage(self.user_id)
            cloud_storage = self._get_cloud_storage()
            
            # Check if local session exists
            if not await local_storage.exists():
                return {
                    'success': False,
                    'message': 'No local session found to migrate',
                    'migration_type': 'local_to_cloud'
                }
            
            # Load local session
            local_data = await local_storage.load()
            if not local_data:
                return {
                    'success': False,
                    'message': 'Failed to load local session data',
                    'migration_type': 'local_to_cloud'
                }
            
            # Store in cloud
            cloud_success = await cloud_storage.store(local_data)
            if not cloud_success:
                return {
                    'success': False,
                    'message': 'Failed to store session in cloud',
                    'migration_type': 'local_to_cloud'
                }
            
            # Verify cloud storage
            cloud_data = await cloud_storage.load()
            if not cloud_data or cloud_data != local_data:
                return {
                    'success': False,
                    'message': 'Cloud storage verification failed',
                    'migration_type': 'local_to_cloud'
                }
            
            # Keep local as backup
            logger.info(f"Successfully migrated session to cloud for user {self.user_id}")
            
            return {
                'success': True,
                'message': 'Successfully migrated session to cloud',
                'migration_type': 'local_to_cloud',
                'cloud_backend': cloud_storage.__class__.__name__,
                'migrated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Migration to cloud failed: {e}")
            return {
                'success': False,
                'message': f'Migration failed: {str(e)}',
                'migration_type': 'local_to_cloud'
            }
    
    async def migrate_to_local(self) -> Dict[str, Any]:
        """
        Migrate cloud sessions to local storage.
        Returns migration status and details.
        """
        try:
            logger.info(f"Starting migration to local for user {self.user_id}")
            
            # Initialize storage backends
            local_storage = LocalTelegramStorage(self.user_id)
            cloud_storage = self._get_cloud_storage()
            
            # Check if cloud session exists
            if not await cloud_storage.exists():
                return {
                    'success': False,
                    'message': 'No cloud session found to migrate',
                    'migration_type': 'cloud_to_local'
                }
            
            # Load cloud session
            cloud_data = await cloud_storage.load()
            if not cloud_data:
                return {
                    'success': False,
                    'message': 'Failed to load cloud session data',
                    'migration_type': 'cloud_to_local'
                }
            
            # Store locally
            local_success = await local_storage.store(cloud_data)
            if not local_success:
                return {
                    'success': False,
                    'message': 'Failed to store session locally',
                    'migration_type': 'cloud_to_local'
                }
            
            # Verify local storage
            local_data = await local_storage.load()
            if not local_data or local_data != cloud_data:
                return {
                    'success': False,
                    'message': 'Local storage verification failed',
                    'migration_type': 'cloud_to_local'
                }
            
            logger.info(f"Successfully migrated session to local for user {self.user_id}")
            
            return {
                'success': True,
                'message': 'Successfully migrated session to local',
                'migration_type': 'cloud_to_local',
                'cloud_backend': cloud_storage.__class__.__name__,
                'migrated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Migration to local failed: {e}")
            return {
                'success': False,
                'message': f'Migration failed: {str(e)}',
                'migration_type': 'cloud_to_local'
            }
    
    async def sync_between_storages(self) -> Dict[str, Any]:
        """
        Sync session data between local and cloud storage.
        Uses the newer session as the source of truth.
        """
        try:
            logger.info(f"Starting sync between storages for user {self.user_id}")
            
            # Initialize storage backends
            local_storage = LocalTelegramStorage(self.user_id)
            cloud_storage = self._get_cloud_storage()
            
            # Check what exists
            local_exists = await local_storage.exists()
            cloud_exists = await cloud_storage.exists()
            
            if not local_exists and not cloud_exists:
                return {
                    'success': True,
                    'message': 'No sessions found in either storage',
                    'sync_type': 'between_storages'
                }
            
            if local_exists and not cloud_exists:
                # Upload local to cloud
                local_data = await local_storage.load()
                cloud_success = await cloud_storage.store(local_data)
                
                return {
                    'success': cloud_success,
                    'message': 'Synced local session to cloud' if cloud_success else 'Failed to sync to cloud',
                    'sync_type': 'local_to_cloud',
                    'synced_at': datetime.now().isoformat()
                }
            
            if cloud_exists and not local_exists:
                # Download cloud to local
                cloud_data = await cloud_storage.load()
                local_success = await local_storage.store(cloud_data)
                
                return {
                    'success': local_success,
                    'message': 'Synced cloud session to local' if local_success else 'Failed to sync to local',
                    'sync_type': 'cloud_to_local',
                    'synced_at': datetime.now().isoformat()
                }
            
            # Both exist - compare and sync
            local_data = await local_storage.load()
            cloud_data = await cloud_storage.load()
            
            if local_data == cloud_data:
                return {
                    'success': True,
                    'message': 'Sessions are already in sync',
                    'sync_type': 'already_synced'
                }
            
            # Use cloud as source of truth (newer)
            local_success = await local_storage.store(cloud_data)
            
            return {
                'success': local_success,
                'message': 'Synced cloud session to local' if local_success else 'Failed to sync from cloud',
                'sync_type': 'cloud_to_local',
                'synced_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sync between storages failed: {e}")
            return {
                'success': False,
                'message': f'Sync failed: {str(e)}',
                'sync_type': 'between_storages'
            }
    
    def _get_cloud_storage(self):
        """Get appropriate cloud storage backend"""
        backend = os.getenv('TELEGRAM_STORAGE_BACKEND', 's3')
        
        if backend == 's3':
            return S3TelegramStorage(self.user_id)
        elif backend == 'redis':
            return RedisTelegramStorage(self.user_id)
        else:
            raise ValueError(f"Unsupported cloud storage backend: {backend}")
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status for all storage backends"""
        try:
            # Initialize storage backends
            local_storage = LocalTelegramStorage(self.user_id)
            cloud_storage = self._get_cloud_storage()
            
            # Check existence
            local_exists = await local_storage.exists()
            cloud_exists = await cloud_storage.exists()
            
            # Get metadata if available
            local_info = None
            cloud_info = None
            
            if local_exists:
                try:
                    # Try to get local session info
                    local_data = await local_storage.load()
                    if local_data:
                        # This would need to be decrypted to get metadata
                        local_info = {'exists': True, 'size': len(local_data)}
                except:
                    pass
            
            if cloud_exists:
                try:
                    # Try to get cloud session info
                    cloud_data = await cloud_storage.load()
                    if cloud_data:
                        cloud_info = {'exists': True, 'size': len(cloud_data)}
                except:
                    pass
            
            return {
                'user_id': self.user_id,
                'environment': 'render' if self.is_render else 'local',
                'local_storage': {
                    'exists': local_exists,
                    'info': local_info
                },
                'cloud_storage': {
                    'exists': cloud_exists,
                    'backend': cloud_storage.__class__.__name__,
                    'info': cloud_info
                },
                'needs_migration': local_exists != cloud_exists,
                'checked_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {
                'user_id': self.user_id,
                'error': str(e),
                'checked_at': datetime.now().isoformat()
            }
    
    async def cleanup_old_sessions(self, keep_cloud: bool = True) -> Dict[str, Any]:
        """
        Clean up old session files.
        By default, keeps cloud sessions and removes local ones.
        """
        try:
            logger.info(f"Starting cleanup for user {self.user_id}")
            
            local_storage = LocalTelegramStorage(self.user_id)
            cloud_storage = self._get_cloud_storage()
            
            cleanup_results = {
                'local_cleaned': False,
                'cloud_cleaned': False,
                'cleanup_type': 'old_sessions'
            }
            
            if keep_cloud:
                # Keep cloud, clean local
                if await local_storage.exists():
                    cleanup_results['local_cleaned'] = await local_storage.delete()
            else:
                # Keep local, clean cloud
                if await cloud_storage.exists():
                    cleanup_results['cloud_cleaned'] = await cloud_storage.delete()
            
            logger.info(f"Cleanup completed for user {self.user_id}")
            return {
                'success': True,
                'message': 'Cleanup completed',
                **cleanup_results,
                'cleaned_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {
                'success': False,
                'message': f'Cleanup failed: {str(e)}',
                'cleanup_type': 'old_sessions'
            }
