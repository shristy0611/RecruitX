import sqlite3
import os
from pathlib import Path
import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import threading
from contextlib import contextmanager

from ..logger import logger

class DatabaseManager:
    """SQLite database manager for RecruitX persistent storage"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one database connection is created"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance.initialized = False
            return cls._instance
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the database manager
        
        Args:
            db_path: Optional path to the database file. If not provided,
                     a default path will be used.
        """
        if self.initialized:
            return
            
        self.db_path = db_path or Path(os.path.dirname(os.path.abspath(__file__))) / "../../data/recruitx.db"
        self.db_path = Path(self.db_path).resolve()
        
        # Create data directory if it doesn't exist
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Connection pool (thread-local)
        self.connections = threading.local()
        
        # Initialize database
        self._init_database()
        
        self.initialized = True
        logger.info(f"Database initialized at {self.db_path}")
    
    def _init_database(self):
        """Initialize the database schema if it doesn't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create Documents table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                content_hash TEXT UNIQUE,
                parsed_text TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create Entities table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                entity_type TEXT NOT NULL,
                entity_value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
            ''')
            
            # Create Matches table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document1_id INTEGER,
                document2_id INTEGER,
                score REAL NOT NULL,
                match_details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document1_id) REFERENCES documents (id),
                FOREIGN KEY (document2_id) REFERENCES documents (id)
            )
            ''')
            
            # Create Cache table for storing API responses
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE,
                cache_value TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool or create a new one
        
        Returns:
            A sqlite3 connection with row factory set to dict
        """
        if not hasattr(self.connections, 'conn'):
            self.connections.conn = sqlite3.connect(self.db_path)
            self.connections.conn.row_factory = self._dict_factory
        
        try:
            yield self.connections.conn
        except Exception as e:
            self.connections.conn.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
    
    def _dict_factory(self, cursor, row):
        """Convert sqlite3 row to dict"""
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions
        
        Usage:
            with db_manager.transaction() as conn:
                # Do something with conn
                conn.execute("INSERT INTO...")
        """
        with self.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction error: {str(e)}")
                raise
    
    def store_document(self, file_name: str, file_type: str, content_hash: str, 
                       parsed_text: str, metadata: Optional[Dict] = None) -> int:
        """Store a document in the database
        
        Args:
            file_name: Name of the file
            file_type: Type of file (e.g., 'resume', 'job_description')
            content_hash: Hash of the document content for deduplication
            parsed_text: Parsed text content of the document
            metadata: Optional metadata dict
            
        Returns:
            The document ID
        """
        with self.transaction() as conn:
            cursor = conn.cursor()
            
            # Check if document with same hash exists
            cursor.execute(
                "SELECT id FROM documents WHERE content_hash = ?", 
                (content_hash,)
            )
            existing = cursor.fetchone()
            
            if existing:
                return existing['id']
            
            # Store new document
            cursor.execute(
                """
                INSERT INTO documents (file_name, file_type, content_hash, parsed_text, metadata) 
                VALUES (?, ?, ?, ?, ?)
                """, 
                (
                    file_name, 
                    file_type, 
                    content_hash, 
                    parsed_text, 
                    json.dumps(metadata) if metadata else None
                )
            )
            
            return cursor.lastrowid
    
    def store_entities(self, document_id: int, entities: List[Dict]) -> List[int]:
        """Store entities extracted from a document
        
        Args:
            document_id: ID of the document
            entities: List of entity dicts with keys:
                      - entity_type: Type of entity (e.g., 'skill', 'education')
                      - entity_value: Value of the entity
                      - confidence: Optional confidence score (0-1)
                      - metadata: Optional metadata dict
        
        Returns:
            List of entity IDs
        """
        with self.transaction() as conn:
            cursor = conn.cursor()
            entity_ids = []
            
            for entity in entities:
                cursor.execute(
                    """
                    INSERT INTO entities (
                        document_id, entity_type, entity_value, confidence, metadata
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        document_id,
                        entity['entity_type'],
                        entity['entity_value'],
                        entity.get('confidence', 1.0),
                        json.dumps(entity.get('metadata', {})) if entity.get('metadata') else None
                    )
                )
                entity_ids.append(cursor.lastrowid)
            
            return entity_ids
    
    def store_match(self, document1_id: int, document2_id: int, score: float, 
                   match_details: Optional[Dict] = None) -> int:
        """Store a match between two documents
        
        Args:
            document1_id: ID of the first document
            document2_id: ID of the second document
            score: Match score (0-1)
            match_details: Optional details about the match
            
        Returns:
            The match ID
        """
        with self.transaction() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO matches (document1_id, document2_id, score, match_details)
                VALUES (?, ?, ?, ?)
                """,
                (
                    document1_id,
                    document2_id,
                    score,
                    json.dumps(match_details) if match_details else None
                )
            )
            
            return cursor.lastrowid
    
    def get_document(self, document_id: int) -> Optional[Dict]:
        """Get a document by ID
        
        Args:
            document_id: ID of the document
            
        Returns:
            Document dict or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
            document = cursor.fetchone()
            
            if document and document.get('metadata'):
                document['metadata'] = json.loads(document['metadata'])
                
            return document
    
    def get_document_by_hash(self, content_hash: str) -> Optional[Dict]:
        """Get a document by content hash
        
        Args:
            content_hash: Hash of the document content
            
        Returns:
            Document dict or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM documents WHERE content_hash = ?", (content_hash,))
            document = cursor.fetchone()
            
            if document and document.get('metadata'):
                document['metadata'] = json.loads(document['metadata'])
                
            return document
    
    def get_entities(self, document_id: int) -> List[Dict]:
        """Get entities for a document
        
        Args:
            document_id: ID of the document
            
        Returns:
            List of entity dicts
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM entities WHERE document_id = ?", (document_id,))
            entities = cursor.fetchall()
            
            # Parse metadata JSON
            for entity in entities:
                if entity.get('metadata'):
                    entity['metadata'] = json.loads(entity['metadata'])
            
            return entities
    
    def get_matches(self, document_id: int) -> List[Dict]:
        """Get matches for a document
        
        Args:
            document_id: ID of the document
            
        Returns:
            List of match dicts
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT * FROM matches 
                WHERE document1_id = ? OR document2_id = ?
                """, 
                (document_id, document_id)
            )
            matches = cursor.fetchall()
            
            # Parse match_details JSON
            for match in matches:
                if match.get('match_details'):
                    match['match_details'] = json.loads(match['match_details'])
            
            return matches
    
    def cache_get(self, cache_key: str) -> Optional[str]:
        """Get a value from the cache
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT cache_value FROM cache 
                WHERE cache_key = ? AND (expires_at IS NULL OR expires_at > datetime('now'))
                """, 
                (cache_key,)
            )
            result = cursor.fetchone()
            
            return result['cache_value'] if result else None
    
    def cache_set(self, cache_key: str, cache_value: str, ttl_seconds: Optional[int] = None):
        """Set a value in the cache
        
        Args:
            cache_key: Cache key
            cache_value: Value to cache
            ttl_seconds: Time-to-live in seconds (None for no expiration)
        """
        expires_at = None
        if ttl_seconds is not None:
            expires_at = datetime.now().timestamp() + ttl_seconds
            expires_at = datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')
        
        with self.transaction() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO cache (cache_key, cache_value, expires_at)
                VALUES (?, ?, ?)
                """,
                (cache_key, cache_value, expires_at)
            )
    
    def clear_expired_cache(self):
        """Clear expired cache entries"""
        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache WHERE expires_at < datetime('now')")
            return cursor.rowcount 