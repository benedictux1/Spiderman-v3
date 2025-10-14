from typing import List, Dict, Any, Optional, Tuple
from app.models import Contact, RawNote, SynthesizedEntry, Tag
from app.utils.database import DatabaseManager
from sqlalchemy import or_, and_, func
import logging
import re

logger = logging.getLogger(__name__)

class SearchService:
    """Service for search functionality"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def search(self, query: str, user_id: int, scope: str = 'all', limit: int = 50) -> Dict[str, Any]:
        """Perform search across contacts and notes"""
        try:
            if not query or len(query.strip()) < 2:
                return {
                    'success': True,
                    'contacts': [],
                    'notes': [],
                    'query': query,
                    'total_results': 0
                }
            
            query = query.strip()
            results = {
                'success': True,
                'contacts': [],
                'notes': [],
                'query': query,
                'total_results': 0
            }
            
            with self.db_manager.get_session() as session:
                # Search contacts if scope is 'all' or 'contacts'
                if scope in ['all', 'contacts']:
                    contacts = self._search_contacts(session, query, user_id, limit)
                    results['contacts'] = contacts
                
                # Search notes if scope is 'all' or 'notes'
                if scope in ['all', 'notes']:
                    notes = self._search_notes(session, query, user_id, limit)
                    results['notes'] = notes
                
                # Calculate total results
                results['total_results'] = len(results['contacts']) + len(results['notes'])
                
                logger.info(f"Search for '{query}' returned {results['total_results']} results")
                return results
                
        except Exception as e:
            logger.error(f"Error performing search: {e}")
            return {
                'success': False,
                'error': 'Search failed',
                'contacts': [],
                'notes': [],
                'query': query,
                'total_results': 0
            }
    
    def _search_contacts(self, session, query: str, user_id: int, limit: int) -> List[Dict[str, Any]]:
        """Search contacts"""
        try:
            # Create search conditions
            search_conditions = [
                Contact.user_id == user_id,
                or_(
                    Contact.full_name.ilike(f'%{query}%'),
                    Contact.telegram_username.ilike(f'%{query}%'),
                    Contact.telegram_handle.ilike(f'%{query}%'),
                    Contact.telegram_phone.ilike(f'%{query}%')
                )
            ]
            
            # Search contacts
            contacts = session.query(Contact).filter(
                and_(*search_conditions)
            ).limit(limit).all()
            
            # Format results
            results = []
            for contact in contacts:
                result = contact.to_dict()
                
                # Add search highlighting
                result['search_highlights'] = self._highlight_search_terms(
                    contact.full_name, query
                )
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching contacts: {e}")
            return []
    
    def _search_notes(self, session, query: str, user_id: int, limit: int) -> List[Dict[str, Any]]:
        """Search notes"""
        try:
            # Search raw notes through contact relationship
            notes = session.query(RawNote).join(Contact).filter(
                Contact.user_id == user_id,
                RawNote.content.ilike(f'%{query}%')
            ).limit(limit).all()
            
            # Format results
            results = []
            for note in notes:
                # Find search term position
                content_lower = note.content.lower()
                query_lower = query.lower()
                start_pos = content_lower.find(query_lower)
                
                # Create snippet
                snippet_start = max(0, start_pos - 50)
                snippet_end = min(len(note.content), start_pos + len(query) + 50)
                snippet = note.content[snippet_start:snippet_end]
                
                # Add ellipsis if needed
                if snippet_start > 0:
                    snippet = '...' + snippet
                if snippet_end < len(note.content):
                    snippet = snippet + '...'
                
                result = {
                    'id': note.id,
                    'content': note.content,
                    'snippet': snippet,
                    'offsets': {
                        'start': start_pos if start_pos >= 0 else 0,
                        'end': start_pos + len(query) if start_pos >= 0 else 0
                    },
                    'contact_name': note.contact.full_name if note.contact else 'Unknown',
                    'contact_id': note.contact_id,
                    'created_at': note.created_at.isoformat() if note.created_at else None,
                    'search_highlights': self._highlight_search_terms(snippet, query)
                }
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching notes: {e}")
            return []
    
    def _highlight_search_terms(self, text: str, query: str) -> List[Dict[str, Any]]:
        """Find and highlight search terms in text"""
        try:
            if not text or not query:
                return []
            
            highlights = []
            text_lower = text.lower()
            query_lower = query.lower()
            
            # Find all occurrences
            start = 0
            while True:
                pos = text_lower.find(query_lower, start)
                if pos == -1:
                    break
                
                highlights.append({
                    'start': pos,
                    'end': pos + len(query)
                })
                start = pos + 1
            
            return highlights
            
        except Exception as e:
            logger.error(f"Error highlighting search terms: {e}")
            return []
    
    def search_by_tag(self, tag_name: str, user_id: int) -> List[Dict[str, Any]]:
        """Search contacts by tag name"""
        try:
            with self.db_manager.get_session() as session:
                # Find tag
                tag = session.query(Tag).filter(
                    Tag.user_id == user_id,
                    Tag.name.ilike(f'%{tag_name}%')
                ).first()
                
                if not tag:
                    return []
                
                # Get contacts with this tag
                contacts = session.query(Contact).join(Contact.tags).filter(
                    Tag.id == tag.id,
                    Contact.user_id == user_id
                ).all()
                
                return [contact.to_dict() for contact in contacts]
                
        except Exception as e:
            logger.error(f"Error searching by tag: {e}")
            return []
    
    def get_search_suggestions(self, query: str, user_id: int, limit: int = 10) -> List[str]:
        """Get search suggestions based on query"""
        try:
            if not query or len(query.strip()) < 2:
                return []
            
            query = query.strip()
            suggestions = []
            
            with self.db_manager.get_session() as session:
                # Get contact name suggestions
                contacts = session.query(Contact.full_name).filter(
                    Contact.user_id == user_id,
                    Contact.full_name.ilike(f'%{query}%')
                ).limit(limit // 2).all()
                
                for contact in contacts:
                    suggestions.append(contact.full_name)
                
                # Get tag suggestions
                tags = session.query(Tag.name).filter(
                    Tag.user_id == user_id,
                    Tag.name.ilike(f'%{query}%')
                ).limit(limit // 2).all()
                
                for tag in tags:
                    suggestions.append(f"#{tag.name}")
                
                # Remove duplicates and limit
                suggestions = list(set(suggestions))[:limit]
                
                return suggestions
                
        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return []
    
    def get_recent_searches(self, user_id: int, limit: int = 10) -> List[str]:
        """Get recent search queries (placeholder - would need search history table)"""
        # This would require a search_history table to implement properly
        # For now, return empty list
        return []
    
    def save_search_query(self, query: str, user_id: int) -> bool:
        """Save search query to history (placeholder - would need search history table)"""
        # This would require a search_history table to implement properly
        # For now, just log the search
        logger.info(f"User {user_id} searched for: {query}")
        return True
