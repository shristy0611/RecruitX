"""
Gemma LLM Service integration for RecruitPro AI.

This module provides access to Gemma API for multilingual capabilities with:
- API key management
- Rate limiting to avoid quota issues
- Automatic retries with exponential backoff
- Structured response handling
"""
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple
import random

import google.generativeai as genai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

from src.utils.config import (
    GEMMA_API_KEYS,
    GEMMA_MODEL,
    DEBUG
)

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
MIN_BACKOFF = 1  # seconds
MAX_BACKOFF = 10  # seconds
FREE_TIER_RPM_LIMIT = 40  # Requests per minute (to be safe)

class QuotaExceededException(Exception):
    """Exception raised when API quota is exceeded."""
    pass

class GemmaService:
    """
    Service for interacting with Gemma 3 LLM.
    
    Features:
    - Automatic key rotation to maximize usage
    - Rate limiting to stay within quota limits
    - Retry with exponential backoff for transient errors
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the Gemma service.
        
        Args:
            api_key: Optional specific API key to use
            model: Optional specific model to use
        """
        self.api_keys = GEMMA_API_KEYS.copy() if not api_key else [api_key]
        random.shuffle(self.api_keys)  # Randomize key order to distribute load
        
        self.model_name = model or GEMMA_MODEL
        
        if not self.api_keys:
            logger.warning("No Gemma API keys found. Gemma service will not function.")
        else:
            logger.info(f"Gemma service initialized with {len(self.api_keys)} API keys")
        
        # Track rate limits
        self.request_timestamps: List[float] = []
        
        # Track key states
        self.key_states: Dict[str, Dict[str, Any]] = {
            key: {"quota_exceeded": False, "last_used": 0, "failures": 0}
            for key in self.api_keys
        }
        
        # Init the model client with the first key
        self._current_key_index = 0
        self._setup_client()
    
    def _setup_client(self) -> bool:
        """
        Set up the Gemma client with the current API key.
        
        Returns:
            bool: True if setup was successful, False otherwise
        """
        if not self.api_keys:
            return False
        
        try:
            key = self.api_keys[self._current_key_index]
            genai.configure(api_key=key)
            
            # Update key state
            self.key_states[key]["last_used"] = time.time()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to set up Gemma client: {e}")
            return False
    
    def _rotate_key(self) -> bool:
        """
        Rotate to the next available API key.
        
        Returns:
            bool: True if rotation was successful, False if no viable keys remain
        """
        # Collect viable keys (those without exceeded quota)
        viable_keys = [
            key for key in self.api_keys 
            if not self.key_states[key]["quota_exceeded"]
        ]
        
        if not viable_keys:
            logger.error("All API keys have exceeded their quota")
            return False
        
        # Find next viable key index
        start_idx = self._current_key_index
        while True:
            self._current_key_index = (self._current_key_index + 1) % len(self.api_keys)
            if not self.key_states[self.api_keys[self._current_key_index]]["quota_exceeded"]:
                break
            
            # If we've checked all keys and come back to the start, no viable keys remain
            if self._current_key_index == start_idx:
                logger.error("No viable API keys remain")
                return False
        
        return self._setup_client()
    
    def _enforce_rate_limit(self) -> None:
        """
        Enforce rate limit to stay within free tier limits.
        """
        current_time = time.time()
        
        # Remove timestamps older than 60 seconds
        self.request_timestamps = [ts for ts in self.request_timestamps if current_time - ts < 60]
        
        # If we're at or near the limit, wait
        if len(self.request_timestamps) >= FREE_TIER_RPM_LIMIT:
            oldest_timestamp = min(self.request_timestamps)
            wait_time = 60 - (current_time - oldest_timestamp)
            
            if wait_time > 0:
                logger.warning(f"Rate limit approaching, waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
        
        # Add current request timestamp
        self.request_timestamps.append(time.time())
    
    @retry(
        retry=retry_if_exception_type(QuotaExceededException),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=MIN_BACKOFF, max=MAX_BACKOFF),
        reraise=True
    )
    def generate_content(
        self, 
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        structured_output: bool = False,
        json_schema: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate content using Gemma API.
        
        Args:
            prompt: The prompt to generate content from
            temperature: Temperature for generation (0.0-1.0)
            max_tokens: Maximum tokens to generate
            structured_output: Whether to expect structured output
            json_schema: Optional JSON schema for structured output
            
        Returns:
            Generated content as string
            
        Raises:
            Exception: If content generation fails after retries
        """
        if not self.api_keys:
            raise Exception("No API keys available")
        
        try:
            # Enforce rate limit
            self._enforce_rate_limit()
            
            # Get model instance
            model = genai.GenerativeModel(self.model_name)
            
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "top_p": 0.95,
                "top_k": 40,
            }
            
            # Generate content
            if structured_output and json_schema:
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    response_mime_type="application/json",
                )
            else:
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                )
            
            # Extract text from response
            if hasattr(response, 'text'):
                text = response.text
            else:
                text = str(response)
            
            # Update key state - successful request
            key = self.api_keys[self._current_key_index]
            self.key_states[key]["failures"] = 0
            
            return text
            
        except Exception as e:
            error_str = str(e).lower()
            key = self.api_keys[self._current_key_index]
            
            # Check if quota exceeded
            if "quota" in error_str or "limit" in error_str or "rate" in error_str:
                logger.warning(f"API key quota exceeded: {key[:5]}...")
                self.key_states[key]["quota_exceeded"] = True
                self.key_states[key]["failures"] += 1
                
                # Try to rotate key
                if self._rotate_key():
                    raise QuotaExceededException("Quota exceeded, retrying with new key")
                else:
                    raise Exception("All API keys have exceeded quota or failed")
            
            # Check for other errors
            self.key_states[key]["failures"] += 1
            
            # If too many failures, try another key
            if self.key_states[key]["failures"] >= 3:
                if self._rotate_key():
                    logger.warning(f"Rotating key after multiple failures")
                
            logger.error(f"Error generating content: {e}")
            raise
    
    def extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract JSON from a response that might contain explanatory text.
        
        Args:
            response_text: Response text possibly containing JSON
            
        Returns:
            Extracted JSON as dictionary
        """
        try:
            # Try direct parsing first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON object in the text
            import re
            
            # Find anything that looks like a JSON object
            json_pattern = r'(\{.*\})'
            matches = re.findall(json_pattern, response_text, re.DOTALL)
            
            if matches:
                # Try each match
                for match in matches:
                    try:
                        return json.loads(match)
                    except json.JSONDecodeError:
                        continue
            
            # If no valid JSON found, log and return empty dict
            logger.warning("No valid JSON found in response")
            return {}
    
    def translate_text(
        self, 
        text: str, 
        source_language: str, 
        target_language: str = "en"
    ) -> str:
        """
        Translate text from source language to target language.
        
        Args:
            text: Text to translate
            source_language: Source language code (ISO 639-1)
            target_language: Target language code (ISO 639-1)
            
        Returns:
            Translated text
        """
        prompt = f"""
        Translate the following text from {source_language} to {target_language}:
        
        {text}
        
        Translation:
        """
        
        try:
            response = self.generate_content(prompt, temperature=0.1)
            
            # Extract translation (remove any explanation text)
            translation = response.strip()
            
            # Remove "Translation:" prefix if present
            if translation.lower().startswith("translation:"):
                translation = translation[len("translation:"):].strip()
            
            return translation
            
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            # Return original text if translation fails
            return text


# Singleton instance for global use
_gemma_service = None

def get_gemma_service() -> GemmaService:
    """
    Get or create the GemmaService singleton.
    
    Returns:
        GemmaService instance
    """
    global _gemma_service
    if _gemma_service is None:
        _gemma_service = GemmaService()
    return _gemma_service
