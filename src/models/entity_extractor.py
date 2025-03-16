from typing import List, Dict, Any, Optional
import sqlite3
from pathlib import Path
from flair.data import Sentence
from flair.models import SequenceTagger
from ..utils.gemini_manager import GeminiKeyManager

class EntityExtractor:
    """Entity extractor using both Gemini and FLAIR"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent.parent / 'data' / 'prototype.db'
        self.gemini_manager = GeminiKeyManager()
        self.flair_tagger = SequenceTagger.load('flair/ner-english-large')
        
    def extract_entities(self, text: str, document_id: int) -> List[Dict[str, Any]]:
        """
        Extract entities from text using both Gemini and FLAIR.
        
        Args:
            text: Text to extract entities from
            document_id: ID of the document in the database
            
        Returns:
            List of extracted entities with their types and values
        """
        # Extract entities using FLAIR
        flair_entities = self._extract_with_flair(text)
        
        # Extract entities using Gemini
        gemini_entities = self._extract_with_gemini(text)
        
        # Combine and deduplicate entities
        all_entities = self._merge_entities(flair_entities, gemini_entities)
        
        # Store entities in database
        self._store_entities(document_id, all_entities)
        
        return all_entities
    
    def _extract_with_flair(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using FLAIR."""
        sentence = Sentence(text)
        self.flair_tagger.predict(sentence)
        
        entities = []
        for entity in sentence.get_spans('ner'):
            entities.append({
                'type': entity.tag,
                'value': entity.text,
                'source': 'flair',
                'confidence': entity.score
            })
            
        return entities
    
    def _extract_with_gemini(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using Gemini."""
        # TODO: Implement Gemini entity extraction
        # This will be implemented once we have the Gemini API integration
        return []
    
    def _merge_entities(self, flair_entities: List[Dict], gemini_entities: List[Dict]) -> List[Dict]:
        """Merge and deduplicate entities from different sources."""
        merged = {}
        
        for entity in flair_entities + gemini_entities:
            key = (entity['type'], entity['value'].lower())
            if key not in merged or entity['confidence'] > merged[key]['confidence']:
                merged[key] = entity
                
        return list(merged.values())
    
    def _store_entities(self, document_id: int, entities: List[Dict[str, Any]]):
        """Store extracted entities in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for entity in entities:
            cursor.execute('''
                INSERT INTO Entities (document_id, entity_type, entity_value, source, confidence)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                document_id,
                entity['type'],
                entity['value'],
                entity['source'],
                entity['confidence']
            ))
            
        conn.commit()
        conn.close()
    
    def get_document_entities(self, document_id: int) -> List[Dict[str, Any]]:
        """Retrieve entities for a specific document."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT entity_type, entity_value, source, confidence
            FROM Entities
            WHERE document_id = ?
        ''', (document_id,))
        
        entities = []
        for row in cursor.fetchall():
            entities.append({
                'type': row[0],
                'value': row[1],
                'source': row[2],
                'confidence': row[3]
            })
            
        conn.close()
        return entities 