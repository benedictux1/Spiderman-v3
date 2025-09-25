from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.database import DatabaseManager
from app.models import User
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID for Flask-Login"""
        try:
            db_manager = DatabaseManager()
            with db_manager.get_session() as session:
                user = session.get(User, user_id)
                if user:
                    # Detach the user from the session to avoid DetachedInstanceError
                    session.expunge(user)
                return user
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password"""
        logger.info(f"🔧 DEBUG: Authenticating user: {username}")
        try:
            with self.db_manager.get_session() as session:
                logger.info(f"🔧 DEBUG: Database session created for auth")
                user = session.query(User).filter(User.username == username).first()
                logger.info(f"🔧 DEBUG: User query result: {user.username if user else 'None'}")
                
                if user:
                    logger.info(f"🔧 DEBUG: User found: {user.username} (ID: {user.id})")
                    logger.info(f"🔧 DEBUG: Checking password hash...")
                    password_valid = check_password_hash(user.password_hash, password)
                    logger.info(f"🔧 DEBUG: Password valid: {password_valid}")
                    
                    if password_valid:
                        # Detach the user from the session to avoid DetachedInstanceError
                        session.expunge(user)
                        logger.info(f"✅ User authenticated successfully: {user.username}")
                        return user
                    else:
                        logger.warning(f"❌ Invalid password for user: {username}")
                else:
                    logger.warning(f"❌ User not found: {username}")
                return None
        except Exception as e:
            logger.error(f"❌ Error authenticating user {username}: {e}")
            logger.error(f"🔧 DEBUG: Error type: {type(e).__name__}")
            logger.error(f"🔧 DEBUG: Error details: {str(e)}")
            logger.error("🔧 DEBUG: Full traceback:", exc_info=True)
            return None
    
    def create_user(self, username: str, password: str, role: str = 'user') -> Optional[User]:
        """Create a new user"""
        try:
            with self.db_manager.get_session() as session:
                # Check if user already exists
                existing_user = session.query(User).filter(User.username == username).first()
                if existing_user:
                    return None
                
                # Create new user
                user = User(
                    username=username,
                    password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
                    password_plaintext=password,  # Store for admin viewing
                    role=role
                )
                session.add(user)
                session.flush()
                # Detach the user from the session to avoid DetachedInstanceError
                session.expunge(user)
                return user
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}")
            return None
    
    def update_user_password(self, user_id: int, new_password: str) -> bool:
        """Update user password"""
        try:
            with self.db_manager.get_session() as session:
                user = session.get(User, user_id)
                if user:
                    user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
                    user.password_plaintext = new_password
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating password for user {user_id}: {e}")
            return False
