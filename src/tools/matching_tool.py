from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field, validator
import numpy as np
from google.cloud import aiplatform
import json
import logging
import asyncio
from datetime import datetime
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

from app.tool.base import BaseTool, ToolResult, CLIResult
from ..utils.gemini_manager import GeminiKeyManager
from ..exceptions import (
    MatchingError,
    EmbeddingError,
    InsightError,
    ValidationError,
    APIError
)

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Performance monitoring
from time import perf_counter
from contextlib import contextmanager

@contextmanager
def timer(operation: str):
    """Context manager for timing operations."""
    start = perf_counter()
    try:
        yield
    finally:
        duration = perf_counter() - start
        logger.info(f"⏱️ {operation} took {duration:.2f} seconds")

class MatchingInput(BaseModel):
    """Input schema for document matching."""
    jd_text: str = Field(..., description="Job description text")
    resume_text: str = Field(..., description="Resume text")
    jd_entities: Optional[List[Dict]] = Field(None, description="Extracted entities from JD")
    resume_entities: Optional[List[Dict]] = Field(None, description="Extracted entities from resume")
    
    @validator('jd_text', 'resume_text')
    def validate_text_length(cls, v: str) -> str:
        """Validate text length to prevent token limit issues."""
        if len(v) < 50:
            raise ValidationError("Text is too short - minimum 50 characters required")
        if len(v) > 50000:
            raise ValidationError("Text is too long - maximum 50000 characters allowed")
        return v.strip()  # Clean input

class MatchResult(BaseModel):
    """Structured output for matching results."""
    score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    key_matches: List[Dict[str, Any]]
    gaps: List[Dict[str, Any]]
    recommendations: List[str]
    summary: str
    metadata: Dict[str, Any]
    
    @validator('score', 'confidence')
    def validate_scores(cls, v: float) -> float:
        """Ensure scores are within valid range."""
        if not 0 <= v <= 1:
            raise ValidationError(f"Score {v} must be between 0 and 1")
        return round(v, 4)  # Standardize precision

class MatchingTool(BaseTool):
    """Tool for matching resumes to job descriptions using semantic similarity and Gemini."""
    
    name: str = "matcher"
    description: str = "Match resumes to job descriptions using semantic similarity and generate insights"
    parameters: Dict = {
        "type": "object",
        "properties": {
            "jd_text": {
                "type": "string",
                "description": "Job description text"
            },
            "resume_text": {
                "type": "string",
                "description": "Resume text"
            },
            "jd_entities": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Extracted entities from JD"
            },
            "resume_entities": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Extracted entities from resume"
            }
        },
        "required": ["jd_text", "resume_text"]
    }
    
    def __init__(self):
        super().__init__()
        self.gemini_manager = GeminiKeyManager()
        self.embedding_model = aiplatform.TextEmbeddingModel.from_pretrained("gemini-embedding-exp-03-07")
        self.pro_model = aiplatform.TextGenerationModel.from_pretrained("gemini-2.0-pro-exp-02-05")
        self._cache = {}
        self._executor = ThreadPoolExecutor(max_workers=3)  # For CPU-bound tasks
        
    async def execute(self, **kwargs) -> ToolResult:
        """Execute document matching with enhanced error handling."""
        operation_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        logger.info(f"🚀 Starting matching operation {operation_id}")
        
        try:
            with timer("Total matching operation"):
                # Validate input
                try:
                    input_data = MatchingInput(**kwargs)
                except ValidationError as e:
                    raise ValidationError(f"Invalid input: {str(e)}")
                
                # Check cache with timeout
                cache_key = self._get_cache_key(input_data)
                if result := await self._get_cached_result(cache_key):
                    logger.info("🎯 Using cached match result")
                    return ToolResult(output=result)
                
                # Parallel embedding generation
                embedding_tasks = [
                    self._generate_embedding(input_data.jd_text),
                    self._generate_embedding(input_data.resume_text)
                ]
                try:
                    jd_embedding, resume_embedding = await asyncio.gather(*embedding_tasks)
                except Exception as e:
                    raise EmbeddingError(f"Failed to generate embeddings: {str(e)}")
                
                # Calculate similarity score
                try:
                    similarity = await asyncio.get_event_loop().run_in_executor(
                        self._executor,
                        self._calculate_similarity,
                        jd_embedding,
                        resume_embedding
                    )
                except Exception as e:
                    raise MatchingError(f"Failed to calculate similarity: {str(e)}")
                
                # Generate detailed insights
                try:
                    insights = await self._generate_insights(
                        input_data.jd_text,
                        input_data.resume_text,
                        similarity,
                        input_data.jd_entities,
                        input_data.resume_entities
                    )
                except Exception as e:
                    raise InsightError(f"Failed to generate insights: {str(e)}")
                
                # Create structured result
                try:
                    result = MatchResult(
                        score=float(similarity),
                        confidence=float(insights.get('confidence', 0.0)),
                        key_matches=insights.get('key_matches', []),
                        gaps=insights.get('gaps', []),
                        recommendations=insights.get('recommendations', []),
                        summary=insights.get('summary', ''),
                        metadata={
                            'operation_id': operation_id,
                            'timestamp': datetime.now().isoformat(),
                            'model_versions': {
                                'embedding': 'gemini-embedding-exp-03-07',
                                'analysis': 'gemini-2.0-pro-exp-02-05'
                            }
                        }
                    )
                except ValidationError as e:
                    raise ValidationError(f"Invalid result structure: {str(e)}")
                
                # Cache result with metadata
                await self._cache_result(cache_key, result.dict())
                
                logger.info(f"✅ Matching operation {operation_id} completed successfully")
                return CLIResult(output=json.dumps(result.dict(), indent=2))
            
        except ValidationError as e:
            error_msg = f"Validation error in operation {operation_id}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return ToolResult(error=error_msg)
            
        except (EmbeddingError, MatchingError, InsightError) as e:
            error_msg = f"Processing error in operation {operation_id}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return ToolResult(error=error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error in operation {operation_id}: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return ToolResult(error=error_msg)
        
        finally:
            logger.info(f"🏁 Matching operation {operation_id} finished")
    
    @lru_cache(maxsize=1000)
    def _get_cache_key(self, input_data: MatchingInput) -> str:
        """Generate a cache key for the input data."""
        key_parts = [
            input_data.jd_text[:100],  # First 100 chars
            input_data.resume_text[:100],
            str(sorted([str(e) for e in (input_data.jd_entities or [])])),
            str(sorted([str(e) for e in (input_data.resume_entities or [])]))
        ]
        return "|".join(key_parts)
    
    async def _get_cached_result(self, cache_key: str, timeout: float = 0.1) -> Optional[Dict]:
        """Get cached result with timeout."""
        try:
            return await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    lambda: self._cache.get(cache_key)
                ),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning("⚠️ Cache lookup timed out")
            return None
    
    async def _cache_result(self, cache_key: str, result: Dict) -> None:
        """Cache result with cleanup."""
        self._cache[cache_key] = result
        if len(self._cache) > 1000:  # Prevent memory bloat
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.info("🧹 Cleaned up oldest cache entry")
    
    async def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using Gemini with retries."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                api_key = self.gemini_manager.get_next_key()
                if not api_key:
                    raise ValueError("No available Gemini API key")
                    
                response = await self.embedding_model.predict(text)
                self.gemini_manager.log_api_call(api_key, "embedding", True)
                return np.array(response.embeddings[0])
                
            except Exception as e:
                if api_key:
                    self.gemini_manager.log_api_call(api_key, "embedding", False, str(e))
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"⚠️ Embedding generation failed (attempt {attempt + 1}/{max_retries})")
    
    def _calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity with input validation."""
        if not isinstance(vec1, np.ndarray) or not isinstance(vec2, np.ndarray):
            raise ValueError("Invalid input: vectors must be numpy arrays")
            
        if vec1.shape != vec2.shape:
            raise ValueError(f"Vector shapes do not match: {vec1.shape} vs {vec2.shape}")
            
        if np.isnan(vec1).any() or np.isnan(vec2).any():
            raise ValueError("Vectors contain NaN values")
            
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
    
    async def _generate_insights(
        self,
        jd_text: str,
        resume_text: str,
        similarity: float,
        jd_entities: Optional[List[Dict]],
        resume_entities: Optional[List[Dict]]
    ) -> Dict[str, Any]:
        """Generate insights using Gemini Pro with enhanced prompting."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                api_key = self.gemini_manager.get_next_key()
                if not api_key:
                    raise ValueError("No available Gemini API key")
                    
                # Create a detailed prompt
                prompt = self._create_analysis_prompt(
                    jd_text, resume_text, similarity,
                    jd_entities, resume_entities
                )
                
                response = await self.pro_model.predict(prompt)
                self.gemini_manager.log_api_call(api_key, "insight", True)
                
                # Parse and validate response
                insights = self._parse_insights(response.text)
                return insights
                
            except Exception as e:
                if api_key:
                    self.gemini_manager.log_api_call(api_key, "insight", False, str(e))
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"⚠️ Insight generation failed (attempt {attempt + 1}/{max_retries})")
    
    def _create_analysis_prompt(
        self,
        jd_text: str,
        resume_text: str,
        similarity: float,
        jd_entities: Optional[List[Dict]],
        resume_entities: Optional[List[Dict]]
    ) -> str:
        """Create a detailed prompt for Gemini analysis."""
        prompt = f"""
        Analyze the match between this job description and resume with high attention to detail.
        
        Job Description:
        {jd_text}
        
        Resume:
        {resume_text}
        
        Initial Similarity Score: {similarity:.2f}
        
        Instructions:
        1. Analyze the semantic match between the documents
        2. Consider both explicit and implicit skill matches
        3. Evaluate experience alignment and potential
        4. Assess education and certification relevance
        5. Consider cultural fit indicators
        """
        
        if jd_entities and resume_entities:
            prompt += f"""
            
            Job Description Entities:
            {json.dumps(jd_entities, indent=2)}
            
            Resume Entities:
            {json.dumps(resume_entities, indent=2)}
            """
            
        prompt += """
        
        Provide a detailed analysis in JSON format with:
        {
            "key_matches": [
                {
                    "type": "skill|experience|education|certification",
                    "jd_requirement": "specific requirement",
                    "resume_match": "matching evidence",
                    "strength": float  // 0.0 to 1.0
                }
            ],
            "gaps": [
                {
                    "type": "skill|experience|education|certification",
                    "requirement": "missing requirement",
                    "impact": "high|medium|low",
                    "mitigation": "possible way to address"
                }
            ],
            "recommendations": [
                "specific, actionable recommendations"
            ],
            "confidence": float,  // 0.0 to 1.0
            "summary": "concise match analysis"
        }
        """
        
        return prompt
    
    def _parse_insights(self, response: str) -> Dict[str, Any]:
        """Parse and validate Gemini's response."""
        try:
            insights = json.loads(response)
            required_fields = ['key_matches', 'gaps', 'recommendations', 'confidence', 'summary']
            
            if not all(field in insights for field in required_fields):
                raise ValueError("Missing required fields in insights")
                
            if not isinstance(insights['confidence'], (int, float)):
                raise ValueError("Invalid confidence value")
                
            return insights
            
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON response from Gemini")