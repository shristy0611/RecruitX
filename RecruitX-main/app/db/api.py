from typing import Dict, List, Any, Optional, Union, Tuple
import hashlib
from pathlib import Path
import json

from .manager import DatabaseManager
from .utils import (
    generate_content_hash, 
    extract_file_metadata, 
    normalize_document_type, 
    serialize_metadata, 
    deserialize_metadata
)
from ..logger import logger

class DatabaseAPI:
    """High-level API for database operations"""
    
    def __init__(self):
        """Initialize the database API"""
        self.db = DatabaseManager()
    
    def store_document_from_text(
        self, 
        text: str, 
        file_name: str, 
        document_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Store a document from text content
        
        Args:
            text: Document text content
            file_name: Name of the file
            document_type: Type of document (e.g., 'resume', 'job_description')
            metadata: Optional metadata dict
            
        Returns:
            Document ID
        """
        content_hash = generate_content_hash(text)
        
        # Check if document already exists
        existing = self.db.get_document_by_hash(content_hash)
        if existing:
            logger.info(f"Document with hash {content_hash} already exists, returning existing ID")
            return existing['id']
        
        # Store new document
        return self.db.store_document(
            file_name=file_name,
            file_type=document_type,
            content_hash=content_hash,
            parsed_text=text,
            metadata=metadata
        )
    
    def store_document_from_file(
        self, 
        file_path: Union[str, Path], 
        document_type: Optional[str] = None,
        parsed_text: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Store a document from file
        
        Args:
            file_path: Path to the file
            document_type: Type of document (e.g., 'resume', 'job_description')
                          If not provided, it will be inferred from file extension
            parsed_text: Parsed text content (if already extracted)
            additional_metadata: Additional metadata to store
            
        Returns:
            Document ID
        """
        path = Path(file_path)
        file_metadata = extract_file_metadata(path)
        
        if document_type is None:
            document_type = normalize_document_type(file_metadata['file_extension'])
        
        # Combine metadata
        metadata = {
            **file_metadata,
            **(additional_metadata or {})
        }
        
        # If parsed_text not provided, read file content
        if parsed_text is None:
            with open(path, 'rb') as f:
                content = f.read()
                content_hash = generate_content_hash(content)
        else:
            content_hash = generate_content_hash(parsed_text)
        
        # Check if document already exists
        existing = self.db.get_document_by_hash(content_hash)
        if existing:
            logger.info(f"Document with hash {content_hash} already exists, returning existing ID")
            return existing['id']
        
        # Store document
        return self.db.store_document(
            file_name=path.name,
            file_type=document_type,
            content_hash=content_hash,
            parsed_text=parsed_text or "",
            metadata=metadata
        )
    
    def store_entities_for_document(
        self, 
        document_id: int, 
        entities: List[Dict[str, Any]]
    ) -> List[int]:
        """Store entities extracted from a document
        
        Args:
            document_id: ID of the document
            entities: List of entity dicts, each with:
                      - entity_type: Type of entity (e.g., 'skill', 'education')
                      - entity_value: Value of the entity
                      - confidence: (optional) Confidence score (0-1)
                      - metadata: (optional) Additional metadata
                      
        Returns:
            List of entity IDs
        """
        return self.db.store_entities(document_id, entities)
    
    def store_match_result(
        self, 
        document1_id: int, 
        document2_id: int, 
        score: float,
        match_details: Optional[Dict[str, Any]] = None
    ) -> int:
        """Store a match result between two documents
        
        Args:
            document1_id: ID of the first document
            document2_id: ID of the second document
            score: Match score (0-1)
            match_details: Optional details about the match
            
        Returns:
            Match ID
        """
        return self.db.store_match(document1_id, document2_id, score, match_details)
    
    def get_document_text(self, document_id: int) -> Optional[str]:
        """Get the text content of a document
        
        Args:
            document_id: ID of the document
            
        Returns:
            Text content or None if not found
        """
        document = self.db.get_document(document_id)
        return document['parsed_text'] if document else None
    
    def get_document_with_entities(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get a document with its entities
        
        Args:
            document_id: ID of the document
            
        Returns:
            Dict with document and entities, or None if not found
        """
        document = self.db.get_document(document_id)
        if not document:
            return None
            
        entities = self.db.get_entities(document_id)
        
        return {
            **document,
            'entities': entities
        }
    
    def get_matches_for_document(
        self, 
        document_id: int,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Get matches for a document
        
        Args:
            document_id: ID of the document
            min_score: Minimum match score (0-1)
            
        Returns:
            List of match dicts
        """
        matches = self.db.get_matches(document_id)
        
        if min_score is not None:
            matches = [m for m in matches if m['score'] >= min_score]
            
        return matches
    
    def search_documents(
        self, 
        document_type: Optional[str] = None,
        text_query: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search documents in the database
        
        Args:
            document_type: Filter by document type (e.g., 'resume', 'job_description')
            text_query: Full-text search query
            metadata_filters: Filter by metadata fields
            limit: Maximum number of results
            
        Returns:
            List of matching documents
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM documents WHERE 1=1"
            params = []
            
            if document_type:
                query += " AND file_type = ?"
                params.append(document_type)
                
            if text_query:
                query += " AND parsed_text LIKE ?"
                params.append(f"%{text_query}%")
                
            if metadata_filters:
                # This is a simplistic approach to metadata filtering
                # A more sophisticated approach would parse the JSON
                for key, value in metadata_filters.items():
                    query += f" AND metadata LIKE ?"
                    params.append(f"%\"{key}\":\"{value}\"%")
            
            query += f" LIMIT {limit}"
            
            cursor.execute(query, params)
            documents = cursor.fetchall()
            
            # Parse metadata JSON
            for doc in documents:
                if doc.get('metadata'):
                    doc['metadata'] = json.loads(doc['metadata'])
            
            return documents
    
    def cache_api_response(
        self, 
        api_name: str,
        request_data: Dict[str, Any],
        response_data: str,
        ttl_seconds: int = 3600 * 24 * 7  # Default: 1 week
    ):
        """Cache an API response
        
        Args:
            api_name: Name of the API (e.g., 'gemini', 'openai')
            request_data: Request data dict
            response_data: Response data string
            ttl_seconds: Time-to-live in seconds
        """
        # Generate a cache key from API name and request data
        cache_key = f"{api_name}:{generate_content_hash(request_data)}"
        
        # Store in cache
        self.db.cache_set(cache_key, response_data, ttl_seconds)
    
    def get_cached_api_response(
        self, 
        api_name: str,
        request_data: Dict[str, Any]
    ) -> Optional[str]:
        """Get a cached API response
        
        Args:
            api_name: Name of the API (e.g., 'gemini', 'openai')
            request_data: Request data dict
            
        Returns:
            Cached response or None if not found
        """
        # Generate cache key
        cache_key = f"{api_name}:{generate_content_hash(request_data)}"
        
        # Get from cache
        return self.db.cache_get(cache_key)
    
    def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries
        
        Returns:
            Number of cache entries removed
        """
        return self.db.clear_expired_cache() 