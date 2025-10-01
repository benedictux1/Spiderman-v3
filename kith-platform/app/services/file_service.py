from typing import List, Optional, Dict, Any
from app.models import UploadedFile, Contact
from app.utils.database import DatabaseManager
from werkzeug.utils import secure_filename
import os
import uuid
import mimetypes
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FileService:
    """Service for managing file uploads"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.upload_folder = os.path.join(os.getcwd(), 'uploads')
        self.allowed_extensions = {
            'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
            'xls', 'xlsx', 'ppt', 'pptx', 'csv', 'json', 'xml'
        }
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
        # Ensure upload directory exists
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        if not filename:
            return False
        
        # Get file extension
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        return ext in self.allowed_extensions
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename for storage"""
        # Get file extension
        ext = ''
        if '.' in original_filename:
            ext = '.' + original_filename.rsplit('.', 1)[1].lower()
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{ext}"
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information"""
        try:
            stat = os.stat(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            return {
                'size': stat.st_size,
                'mime_type': mime_type or 'application/octet-stream',
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime)
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {}
    
    def upload_file(self, file, contact_id: int, user_id: int, description: str = None) -> Optional[UploadedFile]:
        """Upload a file"""
        try:
            # Validate file
            if not file or not file.filename:
                logger.warning("No file provided")
                return None
            
            # Check file extension
            if not self.is_allowed_file(file.filename):
                logger.warning(f"File type not allowed: {file.filename}")
                return None
            
            # Check file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > self.max_file_size:
                logger.warning(f"File too large: {file_size} bytes")
                return None
            
            # Generate secure filename
            original_filename = secure_filename(file.filename)
            stored_filename = self.generate_unique_filename(original_filename)
            file_path = os.path.join(self.upload_folder, stored_filename)
            
            # Save file
            file.save(file_path)
            
            # Get file info
            file_info = self.get_file_info(file_path)
            
            # Create database record
            with self.db_manager.get_session() as session:
                # Verify contact ownership
                contact = session.query(Contact).filter(
                    Contact.id == contact_id,
                    Contact.user_id == user_id
                ).first()
                
                if not contact:
                    # Clean up file
                    os.remove(file_path)
                    logger.warning(f"Contact {contact_id} not found for user {user_id}")
                    return None
                
                uploaded_file = UploadedFile(
                    contact_id=contact_id,
                    user_id=user_id,
                    original_filename=original_filename,
                    stored_filename=stored_filename,
                    file_path=file_path,
                    file_type=file_info.get('mime_type', 'application/octet-stream'),
                    file_size_bytes=file_size
                )
                
                session.add(uploaded_file)
                session.commit()
                session.refresh(uploaded_file)
                
                # Convert to dict before session closes to avoid detachment issues
                file_dict = {
                    'id': uploaded_file.id,
                    'contact_id': uploaded_file.contact_id,
                    'user_id': uploaded_file.user_id,
                    'original_filename': uploaded_file.original_filename,
                    'stored_filename': uploaded_file.stored_filename,
                    'file_path': uploaded_file.file_path,
                    'file_type': uploaded_file.file_type,
                    'file_size_bytes': uploaded_file.file_size_bytes,
                    'analysis_task_id': uploaded_file.analysis_task_id,
                    'generated_raw_note_id': uploaded_file.generated_raw_note_id,
                    'created_at': uploaded_file.created_at.isoformat() if uploaded_file.created_at else None
                }
                
                logger.info(f"Uploaded file {uploaded_file.id}: {original_filename}")
                return file_dict
                
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return None
    
    def get_file_by_id(self, file_id: int, user_id: int) -> Optional[UploadedFile]:
        """Get a file by ID, ensuring user ownership"""
        try:
            with self.db_manager.get_session() as session:
                file = session.query(UploadedFile).filter(
                    UploadedFile.id == file_id,
                    UploadedFile.user_id == user_id
                ).first()
                
                if file:
                    logger.debug(f"Retrieved file {file_id}: {file.original_filename}")
                else:
                    logger.warning(f"File {file_id} not found for user {user_id}")
                
                return file
                
        except Exception as e:
            logger.error(f"Error retrieving file {file_id}: {e}")
            return None
    
    def get_files_by_user(self, user_id: int) -> List[UploadedFile]:
        """Get all files for a user"""
        try:
            with self.db_manager.get_session() as session:
                files = session.query(UploadedFile).filter(
                    UploadedFile.user_id == user_id
                ).all()
                
                logger.info(f"Retrieved {len(files)} files for user {user_id}")
                return files
                
        except Exception as e:
            logger.error(f"Error retrieving files for user {user_id}: {e}")
            return []
    
    def get_files_by_contact(self, contact_id: int, user_id: int) -> List[UploadedFile]:
        """Get all files for a specific contact"""
        try:
            with self.db_manager.get_session() as session:
                files = session.query(UploadedFile).filter(
                    UploadedFile.contact_id == contact_id,
                    UploadedFile.user_id == user_id
                ).all()
                
                logger.info(f"Retrieved {len(files)} files for contact {contact_id}")
                return files
                
        except Exception as e:
            logger.error(f"Error retrieving files for contact {contact_id}: {e}")
            return []
    
    def delete_file(self, file_id: int, user_id: int) -> bool:
        """Delete a file"""
        try:
            with self.db_manager.get_session() as session:
                file = session.query(UploadedFile).filter(
                    UploadedFile.id == file_id,
                    UploadedFile.user_id == user_id
                ).first()
                
                if not file:
                    logger.warning(f"File {file_id} not found for user {user_id}")
                    return False
                
                # Delete physical file
                if os.path.exists(file.file_path):
                    os.remove(file.file_path)
                    logger.info(f"Deleted physical file: {file.file_path}")
                
                # Delete database record
                session.delete(file)
                session.commit()
                
                logger.info(f"Deleted file {file_id}: {file.original_filename}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            return False
    
    def get_file_content(self, file_id: int, user_id: int) -> Optional[bytes]:
        """Get file content as bytes"""
        try:
            file = self.get_file_by_id(file_id, user_id)
            if not file:
                return None
            
            if not os.path.exists(file.file_path):
                logger.error(f"Physical file not found: {file.file_path}")
                return None
            
            with open(file.file_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Error reading file {file_id}: {e}")
            return None
    
    def update_file_metadata(self, file_id: int, user_id: int, **updates) -> Optional[UploadedFile]:
        """Update file metadata"""
        try:
            with self.db_manager.get_session() as session:
                file = session.query(UploadedFile).filter(
                    UploadedFile.id == file_id,
                    UploadedFile.user_id == user_id
                ).first()
                
                if not file:
                    logger.warning(f"File {file_id} not found for user {user_id}")
                    return None
                
                # Update allowed fields
                allowed_fields = ['description', 'analysis_task_id']
                for field, value in updates.items():
                    if field in allowed_fields and hasattr(file, field):
                        setattr(file, field, value)
                
                session.commit()
                session.refresh(file)
                
                logger.info(f"Updated file metadata {file_id}")
                return file
                
        except Exception as e:
            logger.error(f"Error updating file metadata {file_id}: {e}")
            return None