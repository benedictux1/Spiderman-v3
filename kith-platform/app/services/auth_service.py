from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.database import DatabaseManager
from models import User
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
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.username == username).first()
                if user and check_password_hash(user.password_hash, password):
                    # Detach the user from the session to avoid DetachedInstanceError
                    session.expunge(user)
                    return user
                return None
        except Exception as e:
            logger.error(f"Error authenticating user {username}: {e}")
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
