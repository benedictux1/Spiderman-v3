"""
S3 Storage Module for Kith Platform
Handles file uploads and downloads to/from AWS S3
"""
import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import logging

logger = logging.getLogger(__name__)

class S3Storage:
    def __init__(self):
        self.s3_client = None
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.region = os.getenv('AWS_REGION', 'ap-southeast-1')
        
        # Initialize S3 client if credentials are available
        if self._has_credentials():
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=self.region
            )
    
    def _has_credentials(self):
        """Check if AWS credentials are available"""
        return (
            os.getenv('AWS_ACCESS_KEY_ID') and 
            os.getenv('AWS_SECRET_ACCESS_KEY') and 
            os.getenv('S3_BUCKET_NAME')
        )
    
    def upload_file(self, file_obj, object_key):
        """
        Upload a file object to S3
        
        Args:
            file_obj: File object to upload
            object_key: S3 object key (filename)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.s3_client:
            logger.error("S3 client not initialized - missing credentials")
            return False
        
        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                object_key
            )
            logger.info(f"File uploaded successfully to S3: {object_key}")
            return True
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return False
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            return False
    
    def generate_presigned_url(self, object_key, expiration=3600):
        """
        Generate a presigned URL for file access
        
        Args:
            object_key: S3 object key
            expiration: URL expiration time in seconds (default 1 hour)
        
        Returns:
            str: Presigned URL or None if failed
        """
        if not self.s3_client:
            return None
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
    
    def delete_file(self, object_key):
        """
        Delete a file from S3
        
        Args:
            object_key: S3 object key to delete
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.s3_client:
            return False
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            logger.info(f"File deleted successfully from S3: {object_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False
    
    def is_available(self):
        """Check if S3 storage is available"""
        return self.s3_client is not None

# Global S3 storage instance
s3_storage = S3Storage()
