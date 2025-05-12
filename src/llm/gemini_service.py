"""
Gemini LLM Service integration for RecruitPro AI.

This module provides access to Gemini's free tier LLMs with built-in:
- API key rotation (supports up to 10 keys)
- Rate limiting to stay within free tier limits
- Automatic retries with exponential backoff
- Fallback to other keys when quota is exceeded
"""
import json
import logging
import random
import time
from typing import Dict, List, Any, Optional, Union, Tuple

import google.generativeai as genai
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

from src.utils.config import (
    GEMINI_API_KEYS,
    GEMINI_PRO_MODEL,
    GEMINI_THINKING_MODEL,
    DEBUG
)

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
MIN_BACKOFF = 1  # seconds
MAX_BACKOFF = 10  # seconds
FREE_TIER_RPM_LIMIT = 60  # Requests per minute for free tier (to be safe)

class QuotaExceededException(Exception):
    """Exception raised when Gemini quota is exceeded."""
    pass

class GeminiService:
    """
    Service for interacting with Gemini LLMs.
    
    Features:
    - Automatic key rotation to maximize free tier usage
    - Rate limiting to stay within free tier limits
    - Retry with exponential backoff for transient errors
    """
    
    def __init__(self):
        """Initialize the Gemini service."""
        self.api_keys = GEMINI_API_KEYS.copy()
        random.shuffle(self.api_keys)  # Randomize key order to distribute load
        
        if not self.api_keys:
            logger.warning("No Gemini API keys found. Gemini service will not function.")
        else:
            logger.info(f"Gemini service initialized with {len(self.api_keys)} API keys")
        
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
        Set up the Gemini client with the current API key.
        
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
            logger.error(f"Failed to set up Gemini client: {e}")
            return False
    
    def _rotate_key(self) -> bool:
        """
        Rotate to the next available API key.
        
        Returns:
            bool: True if rotation was successful, False if no keys are available
        """
        # Find a key that hasn't exceeded quota
        available_keys = [
            i for i, key in enumerate(self.api_keys)
            if not self.key_states[key]["quota_exceeded"]
        ]
        
        if not available_keys:
            logger.warning("All Gemini API keys have exceeded their quota")
            return False
        
        # Choose the least recently used key
        available_keys.sort(
            key=lambda i: self.key_states[self.api_keys[i]]["last_used"]
        )
        
        self._current_key_index = available_keys[0]
        return self._setup_client()
    
    def _check_rate_limit(self) -> bool:
        """
        Check if we're exceeding the rate limit for the free tier.
        
        Returns:
            bool: True if under rate limit, False if exceeded
        """
        # Remove timestamps older than 60 seconds
        current_time = time.time()
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if current_time - ts < 60
        ]
        
        # Check if we're over the limit
        if len(self.request_timestamps) >= FREE_TIER_RPM_LIMIT:
            logger.warning(f"Rate limit approached: {len(self.request_timestamps)} requests in the last minute")
            return False
        
        return True
    
    def _handle_quota_exceeded(self, key: str) -> bool:
        """
        Handle quota exceeded for a key.
        
        Args:
            key: API key that exceeded quota
            
        Returns:
            bool: True if successfully rotated to a new key, False otherwise
        """
        logger.warning(f"Quota exceeded for Gemini API key (last 4 digits: ...{key[-4:]})")
        
        # Mark this key as having exceeded quota
        self.key_states[key]["quota_exceeded"] = True
        self.key_states[key]["failures"] += 1
        
        # Try to rotate to a new key
        return self._rotate_key()
    
    @retry(
        retry=retry_if_exception_type((Exception)),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(min=MIN_BACKOFF, max=MAX_BACKOFF),
        reraise=True
    )
    def generate_text(
        self,
        prompt: str,
        system_instructions: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
        max_output_tokens: int = 2048,
        thinking_model: bool = False
    ) -> str:
        """
        Generate text with Gemini.
        
        Args:
            prompt: The prompt to send to Gemini
            system_instructions: Optional system instructions
            temperature: Temperature for generation (0.0 to 1.0)
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            max_output_tokens: Maximum number of tokens to generate
            thinking_model: Whether to use the thinking model (more capable but slower)
            
        Returns:
            Generated text
            
        Raises:
            Exception: If generation fails
        """
        if not self.api_keys:
            raise Exception("No Gemini API keys available")
        
        # Wait if we're approaching the rate limit
        while not self._check_rate_limit():
            time.sleep(1)
        
        # Record this request
        self.request_timestamps.append(time.time())
        
        try:
            # Select model
            model_name = GEMINI_THINKING_MODEL if thinking_model else GEMINI_PRO_MODEL
            
            # Get current key
            current_key = self.api_keys[self._current_key_index]
            
            # Create generation config
            generation_config = {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "max_output_tokens": max_output_tokens,
            }
            
            # Configure safety settings - minimal filtering for recruitment domain
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
            
            # Get model
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Prepare content
            if system_instructions:
                content = [
                    {"role": "system", "parts": [system_instructions]},
                    {"role": "user", "parts": [prompt]}
                ]
                response = model.generate_content(content)
            else:
                response = model.generate_content(prompt)
            
            # Update key status - successful request
            self.key_states[current_key]["last_used"] = time.time()
            
            if DEBUG:
                logger.debug(f"Gemini response: {response.text}")
            
            return response.text
        
        except Exception as e:
            error_str = str(e).lower()
            
            # Check for quota exceeded errors
            if "quota" in error_str or "rate" in error_str or "limit" in error_str:
                # Handle quota exceeded
                if not self._handle_quota_exceeded(current_key):
                    raise QuotaExceededException("All Gemini API keys have exceeded their quota")
                
                # Retry with the new key
                return self.generate_text(
                    prompt=prompt,
                    system_instructions=system_instructions,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    max_output_tokens=max_output_tokens,
                    thinking_model=thinking_model
                )
            
            # For other errors, let the retry mechanism handle it
            logger.error(f"Error generating text with Gemini: {e}")
            raise
    
    @retry(
        retry=retry_if_exception_type((Exception)),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(min=MIN_BACKOFF, max=MAX_BACKOFF),
        reraise=True
    )
    def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        system_instructions: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
        max_output_tokens: int = 2048,
        thinking_model: bool = False
    ) -> str:
        """
        Generate a chat response with Gemini.
        
        Args:
            messages: List of message dictionaries with "role" and "content" keys
            system_instructions: Optional system instructions
            temperature: Temperature for generation (0.0 to 1.0)
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            max_output_tokens: Maximum number of tokens to generate
            thinking_model: Whether to use the thinking model (more capable but slower)
            
        Returns:
            Generated chat response text
            
        Raises:
            Exception: If generation fails
        """
        if not self.api_keys:
            raise Exception("No Gemini API keys available")
        
        # Wait if we're approaching the rate limit
        while not self._check_rate_limit():
            time.sleep(1)
        
        # Record this request
        self.request_timestamps.append(time.time())
        
        try:
            # Select model
            model_name = GEMINI_THINKING_MODEL if thinking_model else GEMINI_PRO_MODEL
            
            # Get current key
            current_key = self.api_keys[self._current_key_index]
            
            # Create generation config
            generation_config = {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "max_output_tokens": max_output_tokens,
            }
            
            # Configure safety settings - minimal filtering for recruitment domain
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
            
            # Get model
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Prepare content
            content = []
            
            # Gemini doesn't support system messages directly in the content array
            # Instead, we'll integrate system instructions into the first user message or use a separate model parameter
            
            # Process and add chat messages
            system_added = False
            for i, message in enumerate(messages):
                role = message.get("role", "user").lower()
                msg_content = message.get("content", "")
                
                # Skip system messages - we'll handle them separately
                if role == "system":
                    system_instructions = system_instructions or msg_content
                    continue
                    
                # Gemini expects 'user' or 'model', not 'assistant'
                if role == "assistant":
                    role = "model"
                
                # If this is the first user message and we have system instructions,
                # prepend the system instructions to the user message
                if role == "user" and system_instructions and not system_added:
                    # Only add system instructions to the first user message
                    msg_content = f"[System: {system_instructions}]\n\n{msg_content}"
                    system_added = True
                
                content.append({
                    "role": role,
                    "parts": [msg_content]
                })
            
            # If we have no messages or couldn't add the system instructions, add a blank user message
            if not content:
                content.append({
                    "role": "user", 
                    "parts": [system_instructions or "Hello"]
                })
            elif system_instructions and not system_added:
                # If we have system instructions but no user message to add them to,
                # add a new user message at the beginning
                content.insert(0, {
                    "role": "user",
                    "parts": [f"[System: {system_instructions}]"]
                })
            
            # Generate response
            response = model.generate_content(content)
            
            # Update key status - successful request
            self.key_states[current_key]["last_used"] = time.time()
            
            if DEBUG:
                logger.debug(f"Gemini chat response: {response.text}")
            
            return response.text
        
        except Exception as e:
            error_str = str(e).lower()
            
            # Check for quota exceeded errors
            if "quota" in error_str or "rate" in error_str or "limit" in error_str:
                # Handle quota exceeded
                if not self._handle_quota_exceeded(current_key):
                    raise QuotaExceededException("All Gemini API keys have exceeded their quota")
                
                # Retry with the new key
                return self.generate_chat_response(
                    messages=messages,
                    system_instructions=system_instructions,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    max_output_tokens=max_output_tokens,
                    thinking_model=thinking_model
                )
            
            # For other errors, let the retry mechanism handle it
            logger.error(f"Error generating chat response with Gemini: {e}")
            raise

# Singleton instance for global use
_gemini_service = None

def get_gemini_service() -> GeminiService:
    """
    Get or create the GeminiService singleton.
    
    Returns:
        GeminiService instance
    """
    global _gemini_service
    
    if _gemini_service is None:
        _gemini_service = GeminiService()
    
    return _gemini_service
