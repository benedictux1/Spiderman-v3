from datetime import datetime
from typing import Dict, List, Any, Optional
from app.models.note import RawNote, SynthesizedEntry
from app.models.contact import Contact
from app.services.ai_service import AIService
from app.utils.database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class NoteService:
    def __init__(self, db_manager: DatabaseManager, ai_service: AIService):
        self.db_manager = db_manager
        self.ai_service = ai_service
    
    def process_note(self, contact_id: int, content: str, user_id: int) -> Dict[str, Any]:
        """Process a raw note with AI analysis"""
        with self.db_manager.get_session() as session:
            # Verify contact ownership
            contact = self._get_user_contact(session, contact_id, user_id)
            if not contact:
                raise ValueError("Contact not found")
            
            # Save raw note
            raw_note = RawNote(
                contact_id=contact_id,
                content=content.strip(),
                created_at=datetime.utcnow()
            )
            session.add(raw_note)
            session.flush()
            
            # Process with AI
            try:
                analysis_result = self.ai_service.analyze_note(
                    content=content,
                    contact_name=contact.full_name
                )
                
                # Save synthesized entries
                synthesis_results = []
                for category, data in analysis_result.categories.items():
                    if data.content and len(data.content.strip()) > 10:
                        entry = SynthesizedEntry(
                            contact_id=contact_id,
                            category=category,
                            content=data.content,
                            confidence_score=data.confidence,
                            created_at=datetime.utcnow()
                        )
                        session.add(entry)
                        synthesis_results.append({
                            'category': category,
                            'content': data.content,
                            'confidence': data.confidence
                        })
                
                return {
                    'success': True,
                    'raw_note_id': raw_note.id,
                    'synthesis': synthesis_results,
                    'contact_name': contact.full_name
                }
                
            except Exception as ai_error:
                logger.error(f"AI analysis failed: {ai_error}")
                # Still save the raw note even if AI analysis fails
                return {
                    'success': True,
                    'raw_note_id': raw_note.id,
                    'synthesis': [],
                    'ai_error': str(ai_error),
                    'contact_name': contact.full_name
                }
    
    def get_raw_notes(self, contact_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get raw notes for a contact"""
        with self.db_manager.get_session() as session:
            contact = self._get_user_contact(session, contact_id, user_id)
            if not contact:
                raise ValueError("Contact not found")
            
            notes = session.query(RawNote).filter(
                RawNote.contact_id == contact_id
            ).order_by(RawNote.created_at.desc()).all()
            
            return [
                {
                    'id': note.id,
                    'content': note.content,
                    'created_at': note.created_at.isoformat(),
                    'metadata_tags': note.metadata_tags
                }
                for note in notes
            ]
    
    def _get_user_contact(self, session, contact_id: int, user_id: int) -> Optional[Contact]:
        """Get a contact that belongs to the user"""
        return session.query(Contact).filter(
            Contact.id == contact_id,
            Contact.user_id == user_id
        ).first()
