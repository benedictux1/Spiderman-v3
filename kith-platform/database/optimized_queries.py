# database/optimized_queries.py
# Optimized database query methods to replace N+1 queries with efficient joins
# This file goes in the root directory alongside models.py

from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select, and_, or_, func, text
from models import Contact, ContactTag, Tag, SynthesizedEntry, RawNote, User
from config.database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class OptimizedContactQueries:
    """Optimized database queries that eliminate N+1 problems"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_contacts_with_details(self, user_id: int, tier: int = None, search: str = None, limit: int = None):
        """
        Get contacts with all related data in a single optimized query.
        Replaces multiple separate queries with one efficient join.
        
        Args:
            user_id: ID of the user requesting contacts
            tier: Optional tier filter (1, 2, or 3)
            search: Optional search term for name/company/email
            limit: Optional limit on results
            
        Returns:
            List of contact dictionaries with all related data
        """
        with self.db_manager.get_session() as session:
            # Build the base query with eager loading of related data
            query = session.query(Contact).options(
                # Load tags in a single additional query instead of N queries
                selectinload(Contact.contact_tags).selectinload(ContactTag.tag),
                # Load synthesized entries if needed (commented out for performance)
                # selectinload(Contact.synthesized_entries)
            ).filter(Contact.user_id == user_id)
            
            # Apply filters
            if tier:
                query = query.filter(Contact.tier == tier)
            
            if search:
                search_term = f"%{search.strip().lower()}%"
                query = query.filter(
                    or_(
                        func.lower(Contact.full_name).like(search_term),
                        func.lower(Contact.company).like(search_term),
                        func.lower(Contact.email).like(search_term)
                    )
                )
            
            # Apply limit and ordering
            query = query.order_by(Contact.full_name)
            if limit:
                query = query.limit(limit)
            
            contacts = query.all()
            
            # Convert to dictionaries with all related data
            result = []
            for contact in contacts:
                contact_dict = {
                    'id': contact.id,
                    'full_name': contact.full_name,
                    'tier': contact.tier,
                    'email': contact.email,
                    'phone': contact.phone,
                    'company': contact.company,
                    'location': contact.location,
                    'telegram_username': contact.telegram_username,
                    'telegram_id': contact.telegram_id,
                    'created_at': contact.created_at.isoformat() if contact.created_at else None,
                    'updated_at': contact.updated_at.isoformat() if contact.updated_at else None,
                    # Include tags without additional queries
                    'tags': [
                        {
                            'id': ct.tag.id,
                            'name': ct.tag.name,
                            'color': ct.tag.color
                        } for ct in contact.contact_tags
                    ]
                }
                result.append(contact_dict)
            
            logger.info(f"Loaded {len(result)} contacts with all related data in single query")
            return result
    
    def get_contact_profile_complete(self, contact_id: int, user_id: int):
        """
        Get complete contact profile with all details in optimized queries.
        Uses at most 2 database queries instead of potentially dozens.
        """
        with self.db_manager.get_session() as session:
            # Query 1: Get contact with basic related data
            contact = session.query(Contact).options(
                selectinload(Contact.contact_tags).selectinload(ContactTag.tag)
            ).filter(
                and_(Contact.id == contact_id, Contact.user_id == user_id)
            ).first()
            
            if not contact:
                return None
            
            # Query 2: Get all synthesized entries grouped by category
            # This is more efficient than loading them through the relationship
            entries_query = session.query(SynthesizedEntry).filter(
                SynthesizedEntry.contact_id == contact_id
            ).order_by(SynthesizedEntry.category, SynthesizedEntry.created_at.desc())
            
            entries = entries_query.all()
            
            # Group entries by category
            categorized_data = {}
            for entry in entries:
                if entry.category not in categorized_data:
                    categorized_data[entry.category] = []
                categorized_data[entry.category].append({
                    'id': entry.id,
                    'content': entry.content,
                    'confidence_score': entry.confidence_score,
                    'created_at': entry.created_at.isoformat()
                })
            
            # Build complete profile
            profile = {
                'contact': {
                    'id': contact.id,
                    'full_name': contact.full_name,
                    'tier': contact.tier,
                    'email': contact.email,
                    'phone': contact.phone,
                    'company': contact.company,
                    'location': contact.location,
                    'telegram_username': contact.telegram_username,
                    'telegram_id': contact.telegram_id,
                    'created_at': contact.created_at.isoformat() if contact.created_at else None,
                    'updated_at': contact.updated_at.isoformat() if contact.updated_at else None,
                    'tags': [
                        {
                            'id': ct.tag.id,
                            'name': ct.tag.name,
                            'color': ct.tag.color
                        } for ct in contact.contact_tags
                    ]
                },
                'categorized_data': categorized_data,
                'total_entries': len(entries)
            }
            
            logger.info(f"Loaded complete profile for contact {contact_id} with {len(entries)} entries")
            return profile
    
    def get_contacts_by_tier_summary(self, user_id: int):
        """
        Get tier summary statistics in a single optimized query.
        Replaces multiple COUNT queries with one efficient query.
        """
        with self.db_manager.get_session() as session:
            # Single query to get all tier counts
            result = session.query(
                Contact.tier,
                func.count(Contact.id).label('count')
            ).filter(
                Contact.user_id == user_id
            ).group_by(Contact.tier).all()
            
            # Convert to dictionary format
            tier_summary = {1: 0, 2: 0, 3: 0}
            for tier, count in result:
                tier_summary[tier] = count
            
            logger.info(f"Loaded tier summary for user {user_id}: {tier_summary}")
            return tier_summary
    
    def search_contacts_optimized(self, user_id: int, search_term: str, limit: int = 50):
        """
        Optimized search using full-text search with proper indexing.
        Much faster than LIKE queries on large datasets.
        """
        with self.db_manager.get_session() as session:
            # Use full-text search if available, fallback to LIKE
            if search_term.strip():
                # Try full-text search first (requires the GIN index)
                try:
                    query = session.query(Contact).options(
                        selectinload(Contact.contact_tags).selectinload(ContactTag.tag)
                    ).filter(
                        and_(
                            Contact.user_id == user_id,
                            func.to_tsvector('english', Contact.full_name).match(
                                func.plainto_tsquery('english', search_term)
                            )
                        )
                    ).order_by(
                        func.ts_rank(
                            func.to_tsvector('english', Contact.full_name),
                            func.plainto_tsquery('english', search_term)
                        ).desc()
                    ).limit(limit)
                    
                    contacts = query.all()
                    if contacts:
                        logger.info(f"Used full-text search for '{search_term}', found {len(contacts)} results")
                    else:
                        # Fallback to LIKE search
                        search_pattern = f"%{search_term.strip().lower()}%"
                        query = session.query(Contact).options(
                            selectinload(Contact.contact_tags).selectinload(ContactTag.tag)
                        ).filter(
                            and_(
                                Contact.user_id == user_id,
                                or_(
                                    func.lower(Contact.full_name).like(search_pattern),
                                    func.lower(Contact.company).like(search_pattern),
                                    func.lower(Contact.email).like(search_pattern)
                                )
                            )
                        ).order_by(Contact.full_name).limit(limit)
                        
                        contacts = query.all()
                        logger.info(f"Used LIKE search for '{search_term}', found {len(contacts)} results")
                except Exception as e:
                    # Fallback to LIKE search if full-text search fails
                    logger.warning(f"Full-text search failed, using LIKE: {e}")
                    search_pattern = f"%{search_term.strip().lower()}%"
                    query = session.query(Contact).options(
                        selectinload(Contact.contact_tags).selectinload(ContactTag.tag)
                    ).filter(
                        and_(
                            Contact.user_id == user_id,
                            or_(
                                func.lower(Contact.full_name).like(search_pattern),
                                func.lower(Contact.company).like(search_pattern),
                                func.lower(Contact.email).like(search_pattern)
                            )
                        )
                    ).order_by(Contact.full_name).limit(limit)
                    
                    contacts = query.all()
                    logger.info(f"Used LIKE search for '{search_term}', found {len(contacts)} results")
            else:
                # No search term, return recent contacts
                query = session.query(Contact).options(
                    selectinload(Contact.contact_tags).selectinload(ContactTag.tag)
                ).filter(
                    Contact.user_id == user_id
                ).order_by(Contact.updated_at.desc()).limit(limit)
                
                contacts = query.all()
                logger.info(f"No search term, returned {len(contacts)} recent contacts")
            
            # Convert to dictionaries
            result = []
            for contact in contacts:
                contact_dict = {
                    'id': contact.id,
                    'full_name': contact.full_name,
                    'tier': contact.tier,
                    'email': contact.email,
                    'phone': contact.phone,
                    'company': contact.company,
                    'location': contact.location,
                    'telegram_username': contact.telegram_username,
                    'telegram_id': contact.telegram_id,
                    'created_at': contact.created_at.isoformat() if contact.created_at else None,
                    'updated_at': contact.updated_at.isoformat() if contact.updated_at else None,
                    'tags': [
                        {
                            'id': ct.tag.id,
                            'name': ct.tag.name,
                            'color': ct.tag.color
                        } for ct in contact.contact_tags
                    ]
                }
                result.append(contact_dict)
            
            return result
