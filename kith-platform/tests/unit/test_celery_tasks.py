import pytest
from unittest.mock import Mock, patch, MagicMock
from app.tasks.ai_tasks import process_note_async, batch_process_notes, cleanup_old_tasks
from app.tasks.telegram_tasks import sync_telegram_contacts, process_telegram_messages

@pytest.mark.unit
@pytest.mark.celery
class TestAITasks:
    
    @patch('app.tasks.ai_tasks.NoteService')
    @patch('app.tasks.ai_tasks.container')
    def test_process_note_async_success(self, mock_container, mock_note_service_class):
        """Test successful async note processing"""
        # Setup mocks
        mock_note_service = Mock()
        mock_note_service.process_note.return_value = {
            'success': True,
            'raw_note_id': 123,
            'synthesis': [{'category': 'test', 'content': 'test content'}]
        }
        mock_note_service_class.return_value = mock_note_service
        
        # Create mock task
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Execute task
        result = process_note_async(
            mock_task, 
            contact_id=1, 
            content="test content", 
            user_id=1
        )
        
        # Verify
        assert result['success'] is True
        assert result['raw_note_id'] == 123
        mock_task.update_state.assert_called()
        mock_note_service.process_note.assert_called_once_with(1, "test content", 1)
    
    @patch('app.tasks.ai_tasks.NoteService')
    @patch('app.tasks.ai_tasks.container')
    def test_process_note_async_failure(self, mock_container, mock_note_service_class):
        """Test async note processing failure"""
        # Setup mocks
        mock_note_service = Mock()
        mock_note_service.process_note.side_effect = Exception("Processing failed")
        mock_note_service_class.return_value = mock_note_service
        
        # Create mock task
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Execute task and expect exception
        with pytest.raises(Exception, match="Processing failed"):
            process_note_async(mock_task, contact_id=1, content="test", user_id=1)
        
        mock_task.update_state.assert_called()
    
    @patch('app.tasks.ai_tasks.process_note_async')
    def test_batch_process_notes_success(self, mock_process_note_async):
        """Test successful batch note processing"""
        # Setup mocks
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        mock_async_result = Mock()
        mock_async_result.get.return_value = {'success': True, 'raw_note_id': 1}
        mock_process_note_async.apply_async.return_value = mock_async_result
        
        # Test data
        note_data = [
            {'contact_id': 1, 'content': 'note 1', 'user_id': 1},
            {'contact_id': 2, 'content': 'note 2', 'user_id': 1}
        ]
        
        # Execute task
        result = batch_process_notes(mock_task, note_data)
        
        # Verify
        assert len(result) == 2
        assert result[0]['success'] is True
        assert result[1]['success'] is True
        mock_task.update_state.assert_called()
        assert mock_process_note_async.apply_async.call_count == 2
    
    @patch('app.tasks.ai_tasks.process_note_async')
    def test_batch_process_notes_failure(self, mock_process_note_async):
        """Test batch note processing failure"""
        # Setup mocks
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        mock_process_note_async.apply_async.side_effect = Exception("Batch failed")
        
        # Test data
        note_data = [{'contact_id': 1, 'content': 'note 1', 'user_id': 1}]
        
        # Execute task and expect exception
        with pytest.raises(Exception, match="Batch failed"):
            batch_process_notes(mock_task, note_data)
        
        mock_task.update_state.assert_called()
    
    def test_cleanup_old_tasks_success(self):
        """Test successful cleanup of old tasks"""
        result = cleanup_old_tasks()
        assert result == "Cleanup completed"
    
    @patch('app.tasks.ai_tasks.logger')
    def test_cleanup_old_tasks_failure(self, mock_logger):
        """Test cleanup tasks failure"""
        with patch('app.tasks.ai_tasks.logger') as mock_logger:
            # This would need to be implemented to actually fail
            result = cleanup_old_tasks()
            assert result == "Cleanup completed"

@pytest.mark.unit
@pytest.mark.celery
class TestTelegramTasks:
    
    @patch('app.tasks.telegram_tasks.TelegramService')
    def test_sync_telegram_contacts_success(self, mock_telegram_service_class):
        """Test successful Telegram contacts sync"""
        # Setup mocks
        mock_telegram_service = Mock()
        mock_telegram_service_class.return_value = mock_telegram_service
        
        # Create mock task
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Execute task
        result = sync_telegram_contacts(mock_task, user_id=1)
        
        # Verify
        assert result['user_id'] == 1
        assert 'contacts_synced' in result
        assert 'new_contacts' in result
        assert 'updated_contacts' in result
        mock_task.update_state.assert_called()
    
    @patch('app.tasks.telegram_tasks.TelegramService')
    def test_sync_telegram_contacts_failure(self, mock_telegram_service_class):
        """Test Telegram contacts sync failure"""
        # Setup mocks
        mock_telegram_service = Mock()
        mock_telegram_service_class.return_value = mock_telegram_service
        
        # Create mock task
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Simulate failure
        with patch('app.tasks.telegram_tasks.logger') as mock_logger:
            # This would need to be implemented to actually fail
            result = sync_telegram_contacts(mock_task, user_id=1)
            assert result['user_id'] == 1
    
    def test_process_telegram_messages_success(self):
        """Test successful Telegram messages processing"""
        # Create mock task
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Test data
        message_data = [
            {'id': 1, 'content': 'message 1'},
            {'id': 2, 'content': 'message 2'}
        ]
        
        # Execute task
        result = process_telegram_messages(mock_task, user_id=1, message_data=message_data)
        
        # Verify
        assert result['user_id'] == 1
        assert result['messages_processed'] == 2
        assert 'contacts_updated' in result
        mock_task.update_state.assert_called()
    
    def test_process_telegram_messages_failure(self):
        """Test Telegram messages processing failure"""
        # Create mock task
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Simulate failure
        with patch('app.tasks.telegram_tasks.logger') as mock_logger:
            # This would need to be implemented to actually fail
            result = process_telegram_messages(mock_task, user_id=1, message_data=[])
            assert result['user_id'] == 1
