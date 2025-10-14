"""
Centralized ChromaDB client for semantic search and vector storage

This module provides a singleton ChromaDB client that can be safely shared
across the application in both local development and production environments.

Usage:
    from app.utils.chromadb_client import chroma_client
    
    # Get or create a collection
    collection = chroma_client.get_or_create_collection('my_collection')
    
    # Add documents
    collection.add(
        documents=["This is a test document"],
        ids=["doc1"]
    )
    
    # Query
    results = collection.query(
        query_texts=["test"],
        n_results=5
    )
"""

import os
import logging
from typing import Optional, Any
import chromadb
from chromadb.api.models.Collection import Collection

logger = logging.getLogger(__name__)


class ChromaDBClient:
    """
    Singleton ChromaDB client for vector storage and semantic search
    
    This class ensures only one ChromaDB client instance is created across
    the application lifecycle, preventing resource leaks and connection issues.
    
    Attributes:
        _instance: Singleton instance
        _client: ChromaDB PersistentClient instance
        _db_path: Path to the ChromaDB persistent storage
    """
    
    _instance: Optional['ChromaDBClient'] = None
    _client: Optional[chromadb.PersistentClient] = None
    _db_path: Optional[str] = None
    
    def __new__(cls):
        """Ensure only one instance exists (Singleton pattern)"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _initialize_client(self) -> None:
        """
        Initialize the ChromaDB client if not already initialized
        
        Raises:
            Exception: If ChromaDB client initialization fails
        """
        if self._client is not None:
            return  # Already initialized
        
        try:
            # Disable anonymized telemetry by default unless explicitly enabled
            os.environ.setdefault('ANONYMIZED_TELEMETRY', 'FALSE')
            
            # Determine ChromaDB persistent storage path
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            default_chroma_dir = os.path.join(project_root, 'chroma_db')
            self._db_path = os.getenv('CHROMA_DB_PATH', default_chroma_dir)
            
            # Ensure directory exists
            os.makedirs(self._db_path, exist_ok=True)
            
            # Create persistent client
            self._client = chromadb.PersistentClient(path=self._db_path)
            
            logger.info(f"✅ ChromaDB initialized successfully at: {self._db_path}")
            
        except Exception as e:
            logger.error(f"❌ ChromaDB initialization failed: {e}")
            raise
    
    def get_client(self) -> chromadb.PersistentClient:
        """
        Get the ChromaDB client, initializing if necessary
        
        Returns:
            chromadb.PersistentClient: The initialized ChromaDB client
        
        Raises:
            Exception: If client initialization fails
        """
        if self._client is None:
            self._initialize_client()
        
        return self._client
    
    def get_or_create_collection(self, name: str, **kwargs) -> Collection:
        """
        Get an existing collection or create it if it doesn't exist
        
        Args:
            name: Collection name
            **kwargs: Additional arguments passed to ChromaDB collection creation
        
        Returns:
            Collection: ChromaDB collection instance
        
        Raises:
            Exception: If collection operation fails
        """
        try:
            client = self.get_client()
            collection = client.get_or_create_collection(name=name, **kwargs)
            logger.debug(f"📚 Collection accessed/created: {name}")
            return collection
            
        except Exception as e:
            logger.error(f"❌ Failed to get/create collection '{name}': {e}")
            raise
    
    def delete_collection(self, name: str) -> None:
        """
        Delete a collection if it exists
        
        Args:
            name: Collection name to delete
        """
        try:
            client = self.get_client()
            client.delete_collection(name=name)
            logger.info(f"🗑️  Collection deleted: {name}")
            
        except Exception as e:
            # Collection might not exist, which is fine
            logger.debug(f"Collection '{name}' deletion attempted but failed (may not exist): {e}")
    
    def list_collections(self) -> list:
        """
        List all collections in the ChromaDB instance
        
        Returns:
            list: List of collection objects
        """
        try:
            client = self.get_client()
            collections = client.list_collections()
            logger.debug(f"📋 Found {len(collections)} collections")
            return collections
            
        except Exception as e:
            logger.error(f"❌ Failed to list collections: {e}")
            return []
    
    def reset(self) -> None:
        """
        Reset the ChromaDB client (for testing purposes)
        
        Warning: This will clear the singleton instance and require re-initialization
        """
        logger.warning("⚠️  Resetting ChromaDB client singleton")
        ChromaDBClient._client = None
        ChromaDBClient._db_path = None
    
    @property
    def db_path(self) -> Optional[str]:
        """Get the database path"""
        return self._db_path
    
    def __repr__(self) -> str:
        """String representation of the client"""
        status = "initialized" if self._client else "not initialized"
        path = self._db_path if self._db_path else "unknown"
        return f"<ChromaDBClient status={status} path={path}>"


# Global singleton instance
chroma_client = ChromaDBClient()


# Convenience functions for common operations

def get_contact_collection(contact_id: int, prefix: str = "contact_") -> Collection:
    """
    Get or create a ChromaDB collection for a specific contact
    
    Args:
        contact_id: Contact ID
        prefix: Collection name prefix (default: "contact_")
    
    Returns:
        Collection: ChromaDB collection for the contact
    """
    collection_name = f"{prefix}{contact_id}"
    return chroma_client.get_or_create_collection(collection_name)


def delete_contact_collection(contact_id: int, prefix: str = "contact_") -> None:
    """
    Delete a ChromaDB collection for a specific contact
    
    Args:
        contact_id: Contact ID
        prefix: Collection name prefix (default: "contact_")
    """
    collection_name = f"{prefix}{contact_id}"
    chroma_client.delete_collection(collection_name)


def get_master_collection(name: str = "master_contacts") -> Collection:
    """
    Get or create the master contacts collection
    
    Args:
        name: Master collection name (default: "master_contacts")
    
    Returns:
        Collection: ChromaDB master collection
    """
    return chroma_client.get_or_create_collection(name)


# Health check function

def chromadb_health_check() -> dict:
    """
    Check ChromaDB client health status
    
    Returns:
        dict: Health status with keys 'status', 'db_path', 'collections_count'
    """
    try:
        client = chroma_client.get_client()
        collections = client.list_collections()
        
        return {
            'status': 'healthy',
            'db_path': chroma_client.db_path,
            'collections_count': len(collections),
            'initialized': True
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'initialized': False
        }

