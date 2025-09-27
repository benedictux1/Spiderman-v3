from typing import List, Optional, Dict, Any
from app.models import Contact
from app.utils.database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class ContactService:
    """Service for managing contacts"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_contacts_by_user(self, user_id: int) -> List[Contact]:
        """Get all contacts for a user"""
        try:
            with self.db_manager.get_session() as session:
                contacts = session.query(Contact).filter(Contact.user_id == user_id).all()
                logger.info(f"Retrieved {len(contacts)} contacts for user {user_id}")
                # Expunge contacts to avoid DetachedInstanceError
                for contact in contacts:
                    session.expunge(contact)
                return contacts
        except Exception as e:
            logger.error(f"Error retrieving contacts for user {user_id}: {e}")
            return []
    
    def get_contact_by_id(self, contact_id: int) -> Optional[Contact]:
        """Get a single contact by ID"""
        try:
            with self.db_manager.get_session() as session:
                contact = session.query(Contact).filter(Contact.id == contact_id).first()
                if contact:
                    logger.debug(f"Retrieved contact {contact_id}: {contact.full_name}")
                else:
                    logger.warning(f"Contact {contact_id} not found")
                return contact
        except Exception as e:
            logger.error(f"Error retrieving contact {contact_id}: {e}")
            return None
    
    def create_contact(self, user_id: int, **data) -> Optional[Contact]:
        """Create a new contact"""
        try:
            # Extract and validate required fields
            full_name = data.get('full_name')
            if not full_name:
                logger.error("Cannot create contact: full_name is required")
                return None
                
            with self.db_manager.get_session() as session:
                # Create contact with provided data
                contact_data = {
                    'user_id': user_id,
                    'full_name': full_name.strip(),
                    'tier': data.get('tier', 2),  # Default to tier 2
                    'telegram_id': data.get('telegram_id'),
                    'telegram_username': data.get('telegram_username'),
                    'is_verified': data.get('is_verified', False),
                    'is_premium': data.get('is_premium', False),
                    'vector_collection_id': data.get('vector_collection_id')
                }
                
                # Remove None values
                contact_data = {k: v for k, v in contact_data.items() if v is not None}
                
                contact = Contact(**contact_data)
                session.add(contact)
                session.flush()  # Get ID without committing transaction
                session.refresh(contact)
                
                logger.info(f"Created contact {contact.id}: {contact.full_name} for user {user_id}")
                # Convert to dict before session closes to avoid DetachedInstanceError
                contact_dict = contact.to_dict()
                session.expunge(contact)  # Detach from session
                return contact
                
        except Exception as e:
            logger.error(f"Error creating contact for user {user_id}: {e}")
            return None
    
    def update_contact(self, contact_id: int, **data) -> Optional[Contact]:
        """Update an existing contact"""
        try:
            with self.db_manager.get_session() as session:
                contact = session.query(Contact).filter(Contact.id == contact_id).first()
                if not contact:
                    logger.warning(f"Cannot update: contact {contact_id} not found")
                    return None
                
                # Update allowed fields
                updatable_fields = [
                    'full_name', 'tier', 'telegram_id', 'telegram_username',
                    'is_verified', 'is_premium', 'vector_collection_id'
                ]
                
                updated_fields = []
                for key, value in data.items():
                    if key in updatable_fields and hasattr(contact, key):
                        old_value = getattr(contact, key)
                        if old_value != value:
                            setattr(contact, key, value)
                            updated_fields.append(f"{key}: {old_value} -> {value}")
                
                if updated_fields:
                    session.flush()
                    session.refresh(contact)
                    logger.info(f"Updated contact {contact_id}: {', '.join(updated_fields)}")
                else:
                    logger.debug(f"No changes made to contact {contact_id}")
                
                return contact
                
        except Exception as e:
            logger.error(f"Error updating contact {contact_id}: {e}")
            return None
    
    def delete_contact(self, contact_id: int) -> bool:
        """Delete a contact"""
        try:
            with self.db_manager.get_session() as session:
                contact = session.query(Contact).filter(Contact.id == contact_id).first()
                if not contact:
                    logger.warning(f"Cannot delete: contact {contact_id} not found")
                    return False
                
                contact_name = contact.full_name
                session.delete(contact)
                logger.info(f"Deleted contact {contact_id}: {contact_name}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting contact {contact_id}: {e}")
            return False
    
    def get_contacts_by_tier(self, user_id: int, tier: int) -> List[Contact]:
        """Get contacts filtered by tier"""
        try:
            with self.db_manager.get_session() as session:
                contacts = session.query(Contact).filter(
                    Contact.user_id == user_id,
                    Contact.tier == tier
                ).all()
                logger.debug(f"Retrieved {len(contacts)} tier-{tier} contacts for user {user_id}")
                return contacts
        except Exception as e:
            logger.error(f"Error retrieving tier-{tier} contacts for user {user_id}: {e}")
            return []
    
    def search_contacts(self, user_id: int, search_term: str) -> List[Contact]:
        """Search contacts by name"""
        try:
            if not search_term or not search_term.strip():
                return []
                
            search_pattern = f"%{search_term.strip()}%"
            with self.db_manager.get_session() as session:
                contacts = session.query(Contact).filter(
                    Contact.user_id == user_id,
                    Contact.full_name.ilike(search_pattern)
                ).all()
                logger.debug(f"Found {len(contacts)} contacts matching '{search_term}' for user {user_id}")
                return contacts
        except Exception as e:
            logger.error(f"Error searching contacts for user {user_id}: {e}")
            return []
