import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from app.services.note_service import NoteService
from models import Contact, RawNote, SynthesizedEntry

@pytest.mark.unit
class TestNoteService:
    
    def test_process_note_success(self, db_session, sample_contact, mock_ai_service):
        """Test successful note processing"""
        # Setup
        note_service = NoteService(Mock(), mock_ai_service)
        note_service.db_manager = Mock()
        note_service.db_manager.get_session.return_value.__enter__.return_value = db_session
        
        # Test data
        content = "This is a test note about John Doe. He likes pizza and works at Google."
        user_id = sample_contact.user_id
        
        # Execute
        result = note_service.process_note(sample_contact.id, content, user_id)
        
        # Verify
        assert result['success'] is True
        assert 'raw_note_id' in result
        assert 'synthesis' in result
        assert 'contact_name' in result
        assert len(result['synthesis']) > 0
        
        # Verify raw note was created
        raw_note = db_session.query(RawNote).filter_by(id=result['raw_note_id']).first()
        assert raw_note is not None
        assert raw_note.content == content
        assert raw_note.contact_id == sample_contact.id
    
    def test_process_note_contact_not_found(self, db_session, mock_ai_service):
        """Test note processing with non-existent contact"""
        note_service = NoteService(Mock(), mock_ai_service)
        note_service.db_manager = Mock()
        note_service.db_manager.get_session.return_value.__enter__.return_value = db_session
        
        with pytest.raises(ValueError, match="Contact not found"):
            note_service.process_note(99999, "test content", 1)
    
    def test_process_note_ai_failure(self, db_session, sample_contact):
        """Test note processing when AI analysis fails"""
        # Mock AI service to raise exception
        mock_ai_service = Mock()
        mock_ai_service.analyze_note.side_effect = Exception("AI service unavailable")
        
        note_service = NoteService(Mock(), mock_ai_service)
        note_service.db_manager = Mock()
        note_service.db_manager.get_session.return_value.__enter__.return_value = db_session
        
        content = "Test content"
        user_id = sample_contact.user_id
        
        result = note_service.process_note(sample_contact.id, content, user_id)
        
        # Should still succeed but with AI error
        assert result['success'] is True
        assert 'ai_error' in result
        assert result['ai_error'] == "AI service unavailable"
        assert result['synthesis'] == []
        
        # Raw note should still be saved
        assert 'raw_note_id' in result
    
    def test_get_raw_notes_success(self, db_session, sample_contact, sample_note):
        """Test successful retrieval of raw notes"""
        note_service = NoteService(Mock(), Mock())
        note_service.db_manager = Mock()
        note_service.db_manager.get_session.return_value.__enter__.return_value = db_session
        
        notes = note_service.get_raw_notes(sample_contact.id, sample_contact.user_id)
        
        assert len(notes) >= 1
        assert notes[0]['id'] == sample_note.id
        assert notes[0]['content'] == sample_note.content
        assert 'created_at' in notes[0]
        assert 'metadata_tags' in notes[0]
    
    def test_get_raw_notes_contact_not_found(self, db_session):
        """Test raw notes retrieval with non-existent contact"""
        note_service = NoteService(Mock(), Mock())
        note_service.db_manager = Mock()
        note_service.db_manager.get_session.return_value.__enter__.return_value = db_session
        
        with pytest.raises(ValueError, match="Contact not found"):
            note_service.get_raw_notes(99999, 1)
    
    def test_get_raw_notes_wrong_user(self, db_session, sample_contact, sample_note):
        """Test raw notes retrieval with wrong user"""
        note_service = NoteService(Mock(), Mock())
        note_service.db_manager = Mock()
        note_service.db_manager.get_session.return_value.__enter__.return_value = db_session
        
        with pytest.raises(ValueError, match="Contact not found"):
            note_service.get_raw_notes(sample_contact.id, 99999)  # Wrong user ID
    
    def test_process_note_with_synthesis_entries(self, db_session, sample_contact, mock_ai_service):
        """Test note processing creates synthesis entries"""
        note_service = NoteService(Mock(), mock_ai_service)
        note_service.db_manager = Mock()
        note_service.db_manager.get_session.return_value.__enter__.return_value = db_session
        
        content = "John works at Google and likes pizza"
        user_id = sample_contact.user_id
        
        result = note_service.process_note(sample_contact.id, content, user_id)
        
        # Check that synthesis entries were created
        synthesis_entries = db_session.query(SynthesizedEntry).filter_by(
            contact_id=sample_contact.id
        ).all()
        
        assert len(synthesis_entries) > 0
        assert len(result['synthesis']) == len(synthesis_entries)
        
        # Verify synthesis entry content
        for entry in synthesis_entries:
            assert entry.contact_id == sample_contact.id
            assert entry.category in ['personal_info', 'preferences']
            assert entry.content is not None
            assert entry.confidence_score is not None
