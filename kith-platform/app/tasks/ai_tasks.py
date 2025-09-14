from celery import current_task
from app.celery_app import celery_app
from app.services.ai_service import AIService
from app.services.note_service import NoteService
from app.utils.database import DatabaseManager
from app.utils.dependencies import container
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def process_note_async(self, contact_id: int, content: str, user_id: int):
    """Process a note asynchronously with AI analysis"""
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Processing note...'})
        
        # Get services
        note_service = NoteService(container.database_manager, container.ai_service)
        
        # Process the note
        result = note_service.process_note(contact_id, content, user_id)
        
        # Update task state
        self.update_state(state='SUCCESS', meta={'status': 'Note processed successfully', 'result': result})
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing note asynchronously: {e}")
        self.update_state(state='FAILURE', meta={'status': 'Failed to process note', 'error': str(e)})
        raise

@celery_app.task(bind=True)
def batch_process_notes(self, note_data: list):
    """Process multiple notes in batch"""
    try:
        total_notes = len(note_data)
        processed = 0
        results = []
        
        for i, note_info in enumerate(note_data):
            # Update progress
            progress = (i / total_notes) * 100
            self.update_state(
                state='PROGRESS', 
                meta={'status': f'Processing note {i+1}/{total_notes}', 'progress': progress}
            )
            
            # Process individual note
            result = process_note_async.apply_async(
                args=[note_info['contact_id'], note_info['content'], note_info['user_id']]
            ).get()
            
            results.append(result)
            processed += 1
        
        self.update_state(
            state='SUCCESS', 
            meta={'status': f'Processed {processed} notes successfully', 'results': results}
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        self.update_state(state='FAILURE', meta={'status': 'Batch processing failed', 'error': str(e)})
        raise

@celery_app.task
def cleanup_old_tasks():
    """Clean up old completed tasks"""
    try:
        # This would clean up old task results from Redis
        # Implementation depends on your specific needs
        logger.info("Cleaning up old tasks...")
        return "Cleanup completed"
    except Exception as e:
        logger.error(f"Error cleaning up tasks: {e}")
        raise
