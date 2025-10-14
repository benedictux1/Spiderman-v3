#!/usr/bin/env python3
"""
Telegram Configuration
Handles configuration for both local and Render deployment.
"""

import os
from pathlib import Path
from cryptography.fernet import Fernet

class TelegramConfig:
    """Configuration manager for Telegram integration"""
    
    @staticmethod
    def get_config():
        """Get configuration based on environment"""
        is_render = (
            os.getenv('RENDER') == 'true' or 
            os.getenv('RENDER_EXTERNAL_HOSTNAME') is not None or
            os.getenv('TELEGRAM_STORAGE_BACKEND') == 'cloud'
        )
        
        if is_render:
            return {
                'environment': 'render',
                'storage_backend': os.getenv('TELEGRAM_STORAGE_BACKEND', 's3'),
                'encryption_key': os.getenv('TELEGRAM_ENCRYPTION_KEY'),
                'aws_region': os.getenv('AWS_REGION', 'us-east-1'),
                'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
                'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
                'session_bucket': os.getenv('TELEGRAM_SESSION_BUCKET', 'kith-telegram-sessions'),
                'redis_url': os.getenv('REDIS_URL'),
                'session_ttl': int(os.getenv('TELEGRAM_SESSION_TTL', '2592000')),  # 30 days
                'api_id': os.getenv('TELEGRAM_API_ID'),
                'api_hash': os.getenv('TELEGRAM_API_HASH'),
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
                'use_bot_token': os.getenv('TELEGRAM_USE_BOT_TOKEN', 'false').lower() == 'true'
            }
        else:
            # Local development configuration
            session_dir = Path.home() / '.kith' / 'telegram_sessions'
            session_dir.mkdir(parents=True, exist_ok=True)
            
            return {
                'environment': 'local',
                'storage_backend': 'local',
                'encryption_key': os.getenv('TELEGRAM_ENCRYPTION_KEY', Fernet.generate_key().decode()),
                'session_dir': str(session_dir),
                'session_ttl': 86400 * 30,  # 30 days
                'api_id': os.getenv('TELEGRAM_API_ID'),
                'api_hash': os.getenv('TELEGRAM_API_HASH'),
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
                'use_bot_token': os.getenv('TELEGRAM_USE_BOT_TOKEN', 'false').lower() == 'true'
            }
    
    @staticmethod
    def validate_config(config):
        """Validate configuration"""
        required_fields = ['api_id', 'api_hash']
        
        for field in required_fields:
            if not config.get(field):
                raise ValueError(f"Missing required configuration: {field}")
        
        if config['environment'] == 'render':
            if config['storage_backend'] == 's3':
                s3_required = ['aws_access_key_id', 'aws_secret_access_key', 'session_bucket']
                for field in s3_required:
                    if not config.get(field):
                        raise ValueError(f"Missing required S3 configuration: {field}")
            elif config['storage_backend'] == 'redis':
                if not config.get('redis_url'):
                    raise ValueError("Missing required Redis configuration: redis_url")
        
        return True
    
    @staticmethod
    def get_environment_info():
        """Get environment information"""
        return {
            'is_render': (
                os.getenv('RENDER') == 'true' or 
                os.getenv('RENDER_EXTERNAL_HOSTNAME') is not None
            ),
            'render_external_hostname': os.getenv('RENDER_EXTERNAL_HOSTNAME'),
            'render_service_id': os.getenv('RENDER_SERVICE_ID'),
            'render_service_name': os.getenv('RENDER_SERVICE_NAME'),
            'python_version': os.sys.version,
            'working_directory': os.getcwd()
        }
