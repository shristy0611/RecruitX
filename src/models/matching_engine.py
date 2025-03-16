from typing import List, Dict, Any, Optional
import sqlite3
from pathlib import Path
import numpy as np
from google.cloud import aiplatform
from ..utils.gemini_manager import GeminiKeyManager

class MatchingEngine:
    """Matching engine using Gemini for semantic matching"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent.parent / 'data' / 'prototype.db'
        self.gemini_manager = GeminiKeyManager()
        
        # Initialize Gemini models
        self.embedding_model = aiplatform.TextEmbeddingModel.from_pretrained("gemini-embedding-exp-03-07")
        self.pro_model = aiplatform.TextGenerationModel.from_pretrained("gemini-2.0-pro-exp-02-05")
        
    def find_matches(self, jd_id: int, resume_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Find matches between a job description and multiple resumes.
        
        Args:
            jd_id: ID of the job description document
            resume_ids: List of resume document IDs
            
        Returns:
            List of matches with scores and insights
        """
        # Get job description text
        jd_text = self._get_document_text(jd_id)
        
        # Generate JD embedding
        jd_embedding = self._generate_embedding(jd_text)
        
        matches = []
        for resume_id in resume_ids:
            # Get resume text
            resume_text = self._get_document_text(resume_id)
            
            # Generate resume embedding
            resume_embedding = self._generate_embedding(resume_text)
            
            # Calculate match score and get insights
            match_result = self._calculate_match(jd_text, resume_text, jd_embedding, resume_embedding)
            
            # Store match in database
            match_id = self._store_match(jd_id, resume_id, match_result)
            
            matches.append({
                'resume_id': resume_id,
                'score': match_result['score'],
                'insight': match_result['insight'],
                'match_id': match_id
            })
            
        return sorted(matches, key=lambda x: x['score'], reverse=True)
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using Gemini Embedding model."""
        api_key = self.gemini_manager.get_next_key()
        if not api_key:
            raise ValueError("No available Gemini API key")
            
        try:
            response = self.embedding_model.predict(text)
            self.gemini_manager.log_api_call(api_key, "embedding", True)
            return np.array(response.embeddings[0])
        except Exception as e:
            self.gemini_manager.log_api_call(api_key, "embedding", False, str(e))
            raise
    
    def _calculate_match(self, jd_text: str, resume_text: str, 
                        jd_embedding: np.ndarray, resume_embedding: np.ndarray) -> Dict[str, Any]:
        """
        Calculate match score and generate insights using Gemini.
        
        Args:
            jd_text: Job description text
            resume_text: Resume text
            jd_embedding: JD embedding vector
            resume_embedding: Resume embedding vector
            
        Returns:
            Dict containing match score and insights
        """
        # Calculate cosine similarity
        similarity = np.dot(jd_embedding, resume_embedding) / (
            np.linalg.norm(jd_embedding) * np.linalg.norm(resume_embedding)
        )
        
        # Generate insights using Gemini Pro
        api_key = self.gemini_manager.get_next_key()
        if not api_key:
            return {
                'score': float(similarity),
                'insight': "Unable to generate insights: No available API key"
            }
            
        try:
            prompt = f"""
            Analyze the match between this job description and resume:
            
            Job Description:
            {jd_text}
            
            Resume:
            {resume_text}
            
            Match Score: {similarity:.2f}
            
            Provide a concise analysis focusing on:
            1. Key matching skills and experience
            2. Areas of strong alignment
            3. Potential gaps or areas for improvement
            
            Format the response in a clear, professional manner.
            """
            
            response = self.pro_model.predict(prompt)
            self.gemini_manager.log_api_call(api_key, "insight", True)
            
            return {
                'score': float(similarity),
                'insight': response.text
            }
        except Exception as e:
            self.gemini_manager.log_api_call(api_key, "insight", False, str(e))
            return {
                'score': float(similarity),
                'insight': f"Error generating insights: {str(e)}"
            }
    
    def _get_document_text(self, document_id: int) -> str:
        """Retrieve document text from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT parsed_text FROM Documents WHERE id = ?', (document_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if not result:
            raise ValueError(f"Document not found: {document_id}")
            
        return result[0]
    
    def _store_match(self, jd_id: int, resume_id: int, match_result: Dict[str, Any]) -> int:
        """Store match result in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO Matches (jd_id, resume_id, score, gemini_insight)
            VALUES (?, ?, ?, ?)
        ''', (
            jd_id,
            resume_id,
            match_result['score'],
            match_result['insight']
        ))
        
        match_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return match_id
    
    def get_match_details(self, match_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve detailed information about a specific match."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.*, 
                   jd.file_name as jd_file_name,
                   r.file_name as resume_file_name
            FROM Matches m
            JOIN Documents jd ON m.jd_id = jd.id
            JOIN Documents r ON m.resume_id = r.id
            WHERE m.id = ?
        ''', (match_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
            
        return {
            'match_id': result[0],
            'jd_id': result[1],
            'resume_id': result[2],
            'score': result[3],
            'insight': result[4],
            'created_at': result[5],
            'jd_file_name': result[6],
            'resume_file_name': result[7]
        } 