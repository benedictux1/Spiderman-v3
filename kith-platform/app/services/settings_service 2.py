from typing import Dict, Any, Optional
from app.models import User
from app.utils.database import DatabaseManager
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import json

logger = logging.getLogger(__name__)

class SettingsService:
    """Service for managing user settings and preferences"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user preferences"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return {}
                
                # Default preferences
                default_preferences = {
                    'theme': 'light',
                    'language': 'en',
                    'notifications': True,
                    'email_digest': 'weekly',
                    'timezone': 'UTC',
                    'date_format': 'YYYY-MM-DD',
                    'time_format': '24h'
                }
                
                # Get user preferences from custom_fields or return defaults
                if hasattr(user, 'preferences') and user.preferences:
                    try:
                        user_prefs = json.loads(user.preferences) if isinstance(user.preferences, str) else user.preferences
                        default_preferences.update(user_prefs)
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"Invalid preferences for user {user_id}")
                
                return default_preferences
                
        except Exception as e:
            logger.error(f"Error getting preferences for user {user_id}: {e}")
            return {}
    
    def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                # Validate preferences
                valid_preferences = self._validate_preferences(preferences)
                if not valid_preferences:
                    return False
                
                # Update user preferences
                if hasattr(user, 'preferences'):
                    user.preferences = json.dumps(valid_preferences)
                else:
                    # Store in custom_fields if preferences field doesn't exist
                    if not hasattr(user, 'custom_fields'):
                        user.custom_fields = {}
                    else:
                        user.custom_fields = user.custom_fields or {}
                    
                    user.custom_fields['preferences'] = valid_preferences
                
                session.commit()
                logger.info(f"Updated preferences for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating preferences for user {user_id}: {e}")
            return False
    
    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Get user profile information"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return {}
                
                return {
                    'id': user.id,
                    'username': user.username,
                    'email': getattr(user, 'email', None),
                    'first_name': getattr(user, 'first_name', None),
                    'last_name': getattr(user, 'last_name', None),
                    'role': user.role,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
                
        except Exception as e:
            logger.error(f"Error getting profile for user {user_id}: {e}")
            return {}
    
    def update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> bool:
        """Update user profile"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                # Validate and update allowed fields
                allowed_fields = ['email', 'first_name', 'last_name']
                for field, value in profile_data.items():
                    if field in allowed_fields and hasattr(user, field):
                        setattr(user, field, value)
                
                session.commit()
                logger.info(f"Updated profile for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating profile for user {user_id}: {e}")
            return False
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                # Verify current password
                if not check_password_hash(user.password_hash, current_password):
                    logger.warning(f"Invalid current password for user {user_id}")
                    return False
                
                # Validate new password
                if len(new_password) < 8:
                    logger.warning(f"New password too short for user {user_id}")
                    return False
                
                # Update password
                user.password_hash = generate_password_hash(new_password)
                if hasattr(user, 'password_plaintext'):
                    user.password_plaintext = new_password
                
                session.commit()
                logger.info(f"Changed password for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {e}")
            return False
    
    def get_notification_settings(self, user_id: int) -> Dict[str, Any]:
        """Get notification settings"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return {}
                
                # Default notification settings
                default_notifications = {
                    'email_notifications': True,
                    'push_notifications': False,
                    'digest_frequency': 'weekly',
                    'marketing_emails': False,
                    'system_updates': True,
                    'contact_updates': True
                }
                
                # Get user notification settings
                if hasattr(user, 'notification_settings') and user.notification_settings:
                    try:
                        user_notifications = json.loads(user.notification_settings) if isinstance(user.notification_settings, str) else user.notification_settings
                        default_notifications.update(user_notifications)
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"Invalid notification settings for user {user_id}")
                
                return default_notifications
                
        except Exception as e:
            logger.error(f"Error getting notification settings for user {user_id}: {e}")
            return {}
    
    def update_notification_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """Update notification settings"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                # Validate settings
                valid_settings = self._validate_notification_settings(settings)
                if not valid_settings:
                    return False
                
                # Update notification settings
                if hasattr(user, 'notification_settings'):
                    user.notification_settings = json.dumps(valid_settings)
                else:
                    # Store in custom_fields if notification_settings field doesn't exist
                    if not hasattr(user, 'custom_fields'):
                        user.custom_fields = {}
                    else:
                        user.custom_fields = user.custom_fields or {}
                    
                    user.custom_fields['notification_settings'] = valid_settings
                
                session.commit()
                logger.info(f"Updated notification settings for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating notification settings for user {user_id}: {e}")
            return False
    
    def get_privacy_settings(self, user_id: int) -> Dict[str, Any]:
        """Get privacy settings"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return {}
                
                # Default privacy settings
                default_privacy = {
                    'profile_visibility': 'private',
                    'data_sharing': False,
                    'analytics_tracking': True,
                    'third_party_integrations': False,
                    'data_retention': '1_year',
                    'export_data': True
                }
                
                # Get user privacy settings
                if hasattr(user, 'privacy_settings') and user.privacy_settings:
                    try:
                        user_privacy = json.loads(user.privacy_settings) if isinstance(user.privacy_settings, str) else user.privacy_settings
                        default_privacy.update(user_privacy)
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"Invalid privacy settings for user {user_id}")
                
                return default_privacy
                
        except Exception as e:
            logger.error(f"Error getting privacy settings for user {user_id}: {e}")
            return {}
    
    def update_privacy_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """Update privacy settings"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                # Validate settings
                valid_settings = self._validate_privacy_settings(settings)
                if not valid_settings:
                    return False
                
                # Update privacy settings
                if hasattr(user, 'privacy_settings'):
                    user.privacy_settings = json.dumps(valid_settings)
                else:
                    # Store in custom_fields if privacy_settings field doesn't exist
                    if not hasattr(user, 'custom_fields'):
                        user.custom_fields = {}
                    else:
                        user.custom_fields = user.custom_fields or {}
                    
                    user.custom_fields['privacy_settings'] = valid_settings
                
                session.commit()
                logger.info(f"Updated privacy settings for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating privacy settings for user {user_id}: {e}")
            return False
    
    def delete_user_account(self, user_id: int, password: str) -> bool:
        """Delete user account"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                # Verify password
                if not check_password_hash(user.password_hash, password):
                    logger.warning(f"Invalid password for account deletion for user {user_id}")
                    return False
                
                # Delete user (this will cascade to related records)
                session.delete(user)
                session.commit()
                
                logger.info(f"Deleted account for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting account for user {user_id}: {e}")
            return False
    
    def _validate_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user preferences"""
        valid_preferences = {}
        
        # Theme validation
        if 'theme' in preferences:
            theme = preferences['theme']
            if theme in ['light', 'dark', 'auto']:
                valid_preferences['theme'] = theme
        
        # Language validation
        if 'language' in preferences:
            language = preferences['language']
            if language in ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko']:
                valid_preferences['language'] = language
        
        # Boolean validations
        for field in ['notifications', 'email_digest']:
            if field in preferences:
                if isinstance(preferences[field], bool):
                    valid_preferences[field] = preferences[field]
        
        # Email digest validation
        if 'email_digest' in preferences:
            digest = preferences['email_digest']
            if digest in ['never', 'daily', 'weekly', 'monthly']:
                valid_preferences['email_digest'] = digest
        
        return valid_preferences
    
    def _validate_notification_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate notification settings"""
        valid_settings = {}
        
        # Boolean validations
        for field in ['email_notifications', 'push_notifications', 'marketing_emails', 'system_updates', 'contact_updates']:
            if field in settings:
                if isinstance(settings[field], bool):
                    valid_settings[field] = settings[field]
        
        # Digest frequency validation
        if 'digest_frequency' in settings:
            frequency = settings['digest_frequency']
            if frequency in ['never', 'daily', 'weekly', 'monthly']:
                valid_settings['digest_frequency'] = frequency
        
        return valid_settings
    
    def _validate_privacy_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate privacy settings"""
        valid_settings = {}
        
        # Profile visibility validation
        if 'profile_visibility' in settings:
            visibility = settings['profile_visibility']
            if visibility in ['public', 'private', 'friends']:
                valid_settings['profile_visibility'] = visibility
        
        # Boolean validations
        for field in ['data_sharing', 'analytics_tracking', 'third_party_integrations', 'export_data']:
            if field in settings:
                if isinstance(settings[field], bool):
                    valid_settings[field] = settings[field]
        
        # Data retention validation
        if 'data_retention' in settings:
            retention = settings['data_retention']
            if retention in ['1_month', '3_months', '6_months', '1_year', '2_years', 'forever']:
                valid_settings['data_retention'] = retention
        
        return valid_settings
