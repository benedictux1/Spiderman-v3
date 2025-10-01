from typing import List, Optional, Dict, Any
from app.models import Tag, Contact, ContactTag
from app.utils.database import DatabaseManager
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

class TagService:
    """Service for managing tags"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_tags_by_user(self, user_id: int) -> List[Tag]:
        """Get all tags for a user"""
        try:
            with self.db_manager.get_session() as session:
                tags = session.query(Tag).filter(Tag.user_id == user_id).all()
                logger.info(f"Retrieved {len(tags)} tags for user {user_id}")
                # Expunge tags to avoid DetachedInstanceError
                for tag in tags:
                    session.expunge(tag)
                return tags
        except Exception as e:
            logger.error(f"Error retrieving tags for user {user_id}: {e}")
            return []
    
    def get_tag_by_id(self, tag_id: int, user_id: int) -> Optional[Tag]:
        """Get a single tag by ID, ensuring user ownership"""
        try:
            with self.db_manager.get_session() as session:
                tag = session.query(Tag).filter(
                    Tag.id == tag_id,
                    Tag.user_id == user_id
                ).first()
                if tag:
                    logger.debug(f"Retrieved tag {tag_id}: {tag.name}")
                else:
                    logger.warning(f"Tag {tag_id} not found for user {user_id}")
                return tag
        except Exception as e:
            logger.error(f"Error retrieving tag {tag_id}: {e}")
            return None
    
    def create_tag(self, user_id: int, name: str, color: str = '#97C2FC', description: str = None) -> Optional[Tag]:
        """Create a new tag"""
        try:
            with self.db_manager.get_session() as session:
                # Check if tag with same name already exists for user
                existing_tag = session.query(Tag).filter(
                    Tag.user_id == user_id,
                    Tag.name == name
                ).first()
                
                if existing_tag:
                    logger.warning(f"Tag '{name}' already exists for user {user_id}")
                    return None
                
                tag = Tag(
                    user_id=user_id,
                    name=name,
                    color=color,
                    description=description
                )
                
                session.add(tag)
                session.commit()
                session.refresh(tag)
                
                # Convert to dict before session closes to avoid detachment issues
                tag_dict = {
                    'id': tag.id,
                    'user_id': tag.user_id,
                    'name': tag.name,
                    'color': tag.color,
                    'description': tag.description,
                    'created_at': tag.created_at.isoformat() if tag.created_at else None,
                    'updated_at': tag.updated_at.isoformat() if tag.updated_at else None
                }
                
                logger.info(f"Created tag {tag.id}: {tag.name} for user {user_id}")
                return tag_dict
                
        except IntegrityError as e:
            logger.error(f"Integrity error creating tag '{name}' for user {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating tag '{name}' for user {user_id}: {e}")
            return None
    
    def update_tag(self, tag_id: int, user_id: int, **updates) -> Optional[Tag]:
        """Update a tag"""
        try:
            with self.db_manager.get_session() as session:
                tag = session.query(Tag).filter(
                    Tag.id == tag_id,
                    Tag.user_id == user_id
                ).first()
                
                if not tag:
                    logger.warning(f"Tag {tag_id} not found for user {user_id}")
                    return None
                
                # Check for name conflicts if name is being updated
                if 'name' in updates and updates['name'] != tag.name:
                    existing_tag = session.query(Tag).filter(
                        Tag.user_id == user_id,
                        Tag.name == updates['name'],
                        Tag.id != tag_id
                    ).first()
                    
                    if existing_tag:
                        logger.warning(f"Tag '{updates['name']}' already exists for user {user_id}")
                        return None
                
                # Update fields
                for field, value in updates.items():
                    if hasattr(tag, field):
                        setattr(tag, field, value)
                
                session.commit()
                session.refresh(tag)
                
                logger.info(f"Updated tag {tag_id}: {tag.name}")
                return tag
                
        except IntegrityError as e:
            logger.error(f"Integrity error updating tag {tag_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error updating tag {tag_id}: {e}")
            return None
    
    def delete_tag(self, tag_id: int, user_id: int, reassign_to_tag_id: int = None) -> bool:
        """Delete a tag, optionally reassigning contacts to another tag"""
        try:
            with self.db_manager.get_session() as session:
                tag = session.query(Tag).filter(
                    Tag.id == tag_id,
                    Tag.user_id == user_id
                ).first()
                
                if not tag:
                    logger.warning(f"Tag {tag_id} not found for user {user_id}")
                    return False
                
                # Handle reassignment if specified
                if reassign_to_tag_id:
                    reassign_tag = session.query(Tag).filter(
                        Tag.id == reassign_to_tag_id,
                        Tag.user_id == user_id
                    ).first()
                    
                    if not reassign_tag:
                        logger.warning(f"Reassignment tag {reassign_to_tag_id} not found")
                        return False
                    
                    # Reassign contacts
                    contact_tags = session.query(ContactTag).filter(
                        ContactTag.tag_id == tag_id
                    ).all()
                    
                    for contact_tag in contact_tags:
                        # Check if contact already has the reassignment tag
                        existing = session.query(ContactTag).filter(
                            ContactTag.contact_id == contact_tag.contact_id,
                            ContactTag.tag_id == reassign_to_tag_id
                        ).first()
                        
                        if not existing:
                            # Create new association
                            new_contact_tag = ContactTag(
                                contact_id=contact_tag.contact_id,
                                tag_id=reassign_to_tag_id
                            )
                            session.add(new_contact_tag)
                        
                        # Remove old association
                        session.delete(contact_tag)
                    
                    logger.info(f"Reassigned {len(contact_tags)} contacts from tag {tag_id} to {reassign_to_tag_id}")
                
                # Delete the tag
                session.delete(tag)
                session.commit()
                
                logger.info(f"Deleted tag {tag_id}: {tag.name}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting tag {tag_id}: {e}")
            return False
    
    def get_contacts_for_tag(self, tag_id: int, user_id: int) -> List[Contact]:
        """Get all contacts for a specific tag"""
        try:
            with self.db_manager.get_session() as session:
                # Verify tag ownership
                tag = session.query(Tag).filter(
                    Tag.id == tag_id,
                    Tag.user_id == user_id
                ).first()
                
                if not tag:
                    logger.warning(f"Tag {tag_id} not found for user {user_id}")
                    return []
                
                # Get contacts through the many-to-many relationship
                contacts = session.query(Contact).join(ContactTag).filter(
                    ContactTag.tag_id == tag_id,
                    Contact.user_id == user_id
                ).all()
                
                logger.info(f"Retrieved {len(contacts)} contacts for tag {tag_id}")
                return contacts
                
        except Exception as e:
            logger.error(f"Error retrieving contacts for tag {tag_id}: {e}")
            return []
    
    def add_tag_to_contact(self, contact_id: int, tag_id: int, user_id: int) -> bool:
        """Add a tag to a contact"""
        try:
            with self.db_manager.get_session() as session:
                # Verify ownership of both contact and tag
                contact = session.query(Contact).filter(
                    Contact.id == contact_id,
                    Contact.user_id == user_id
                ).first()
                
                tag = session.query(Tag).filter(
                    Tag.id == tag_id,
                    Tag.user_id == user_id
                ).first()
                
                if not contact or not tag:
                    logger.warning(f"Contact {contact_id} or tag {tag_id} not found for user {user_id}")
                    return False
                
                # Check if association already exists
                existing = session.query(ContactTag).filter(
                    ContactTag.contact_id == contact_id,
                    ContactTag.tag_id == tag_id
                ).first()
                
                if existing:
                    logger.info(f"Contact {contact_id} already has tag {tag_id}")
                    return True
                
                # Create association
                contact_tag = ContactTag(
                    contact_id=contact_id,
                    tag_id=tag_id
                )
                session.add(contact_tag)
                session.commit()
                
                logger.info(f"Added tag {tag_id} to contact {contact_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding tag {tag_id} to contact {contact_id}: {e}")
            return False
    
    def remove_tag_from_contact(self, contact_id: int, tag_id: int, user_id: int) -> bool:
        """Remove a tag from a contact"""
        try:
            with self.db_manager.get_session() as session:
                # Verify ownership
                contact_tag = session.query(ContactTag).join(Contact).join(Tag).filter(
                    ContactTag.contact_id == contact_id,
                    ContactTag.tag_id == tag_id,
                    Contact.user_id == user_id,
                    Tag.user_id == user_id
                ).first()
                
                if not contact_tag:
                    logger.warning(f"Contact-tag association not found for contact {contact_id}, tag {tag_id}")
                    return False
                
                session.delete(contact_tag)
                session.commit()
                
                logger.info(f"Removed tag {tag_id} from contact {contact_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error removing tag {tag_id} from contact {contact_id}: {e}")
            return False
