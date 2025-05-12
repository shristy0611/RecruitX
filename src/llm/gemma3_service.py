"""
Gemma 3 Service for RecruitPro AI.

This module provides integration with Google's Gemma 3 model
running in Docker container using the Model Runner API format.
Optimized for local execution on Apple Silicon machines (16GB RAM).
"""
import json
import logging
import os
import requests
from typing import Dict, List, Any, Optional

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from src.llm.llm_service_interface import LLMService
from src.utils.config import DEBUG, LOCAL_LLM_URL, LOCAL_LLM_MODEL

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
MIN_BACKOFF = 1  # seconds
MAX_BACKOFF = 10  # seconds
DEFAULT_TIMEOUT = 30  # seconds

class Gemma3Service(LLMService):
    """
    Service for Google's Gemma 3 multimodal model running in Docker.
    
    This service provides text generation and vision capabilities
    with both Japanese and English language support.
    """
    
    def __init__(
        self,
        base_url: str = None,
        model_name: str = None,
    ):
        """
        Initialize the Gemma 3 service.
        
        Args:
            base_url: Base URL of the Docker Model Runner service
            model_name: Name of the model to use
        """
        # Get configuration from environment variables
        self.base_url = base_url or LOCAL_LLM_URL
        self.model_name = model_name or LOCAL_LLM_MODEL
        
        # Set up API endpoints
        self.text_endpoint = "/completions"
        self.chat_endpoint = "/chat/completions"
        self.model_info_endpoint = "/models"
        
        # Check if model is available
        self.is_available = self._check_availability()
        
        if self.is_available:
            logger.info(f"Gemma 3 service initialized and available at {self.base_url}")
            logger.info(f"Using model: {self.model_name}")
        else:
            logger.warning(f"Gemma 3 service initialized but not available at {self.base_url}")
    
    def _check_availability(self) -> bool:
        """Check if the Gemma 3 service is available"""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                timeout=DEFAULT_TIMEOUT
            )
            if response.status_code == 200:
                # Check if our model is in the list
                result = response.json()
                if "data" in result:
                    models = result["data"]
                    for model in models:
                        if model.get("id") == self.model_name:
                            return True
            return False
        except Exception as e:
            logger.warning(f"Gemma 3 service not available: {str(e)}")
            return False
    
    @retry(
        retry=retry_if_exception_type((requests.RequestException, ConnectionError, TimeoutError)),
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
        max_output_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text with Gemma 3.
        
        Args:
            prompt: The prompt to send to the model
            system_instructions: Optional system instructions
            temperature: Temperature for generation (0.0 to 1.0)
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            max_output_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text
            
        Raises:
            Exception: If generation fails
        """
        if not self.is_available:
            raise Exception("Gemma 3 service is not available")
        
        # Use default max tokens if not specified
        if max_output_tokens is None:
            max_output_tokens = 1024
        
        # Prepare request payload
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_output_tokens,
        }
        
        # Make API call
        try:
            url = f"{self.base_url}{self.text_endpoint}"
            response = requests.post(
                url,
                json=payload,
                timeout=DEFAULT_TIMEOUT
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract generated text
            if "choices" in result and len(result["choices"]) > 0:
                generated_text = result["choices"][0].get("text", "")
            else:
                logger.warning(f"Unexpected response format: {result}")
                generated_text = str(result)
            
            if DEBUG:
                logger.debug(f"Generated text: {generated_text[:100]}...")
            
            return generated_text
        
        except Exception as e:
            logger.error(f"Error generating text with Gemma 3: {e}")
            raise
    
    @retry(
        retry=retry_if_exception_type((requests.RequestException, ConnectionError, TimeoutError)),
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
        max_output_tokens: Optional[int] = None,
        image_url: Optional[str] = None,  # For multimodal capabilities
    ) -> str:
        """
        Generate a chat response with Gemma 3.
        
        Args:
            messages: List of message dictionaries with "role" and "content" keys
            system_instructions: Optional system instructions
            temperature: Temperature for generation (0.0 to 1.0)
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            max_output_tokens: Maximum number of tokens to generate
            image_url: Optional URL to an image for multimodal queries
            
        Returns:
            Generated chat response text
            
        Raises:
            Exception: If generation fails
        """
        if not self.is_available:
            raise Exception("Gemma 3 service is not available")
        
        # Use default max tokens if not specified
        if max_output_tokens is None:
            max_output_tokens = 1024
        
        # Process messages for the API
        formatted_messages = []
        
        # Add system instructions if provided
        if system_instructions:
            formatted_messages.append({
                "role": "system",
                "content": system_instructions
            })
        
        # Process conversation messages
        for message in messages:
            role = message.get("role", "user").lower()
            content = message.get("content", "")
            
            # Skip empty messages
            if not content:
                continue
                
            # Create the message
            formatted_message = {"role": role, "content": content}
            formatted_messages.append(formatted_message)
        
        # Prepare request payload
        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_output_tokens,
        }
        
        # Make API call
        try:
            url = f"{self.base_url}{self.chat_endpoint}"
            response = requests.post(
                url,
                json=payload,
                timeout=DEFAULT_TIMEOUT
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract generated text from OpenAI-compatible response format
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "message" in choice:
                    generated_text = choice["message"].get("content", "")
                else:
                    generated_text = choice.get("text", "")
            else:
                logger.warning(f"Unexpected response format: {result}")
                generated_text = str(result)
            
            if DEBUG:
                logger.debug(f"Generated chat response: {generated_text[:100]}...")
            
            return generated_text
        
        except Exception as e:
            logger.error(f"Error generating chat response with Gemma 3: {e}")
            raise

# Singleton instance for global use
_gemma3_service = None

def get_gemma3_service() -> Gemma3Service:
    """
    Get a global instance of the Gemma 3 service.
    
    Returns:
        A Gemma 3 service instance
    """
    global _gemma3_service
    
    if _gemma3_service is None:
        _gemma3_service = Gemma3Service()
    
    return _gemma3_service
