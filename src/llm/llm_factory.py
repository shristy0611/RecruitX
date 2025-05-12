"""
LLM Service Factory for RecruitPro AI.

This module provides a unified interface to different LLM backends:
1. Gemini API (free tier with key rotation)
2. Docker-based local models (lightweight for MacBook Air)

The factory automatically selects the appropriate service based on:
- Configuration preferences
- API key availability
- Docker container availability
"""
import enum
import logging
from typing import Dict, List, Any, Optional, Union, Tuple

from src.utils.config import (
    GEMINI_API_KEYS,
    USE_LOCAL_LLM,
    DEBUG
)

# Configure logging
logger = logging.getLogger(__name__)

class LLMServiceType(enum.Enum):
    """Enum for LLM service types."""
    GEMINI = "gemini"
    GEMMA3 = "gemma3"
    AUTO = "auto"

class LLMService:
    """
    Unified LLM service interface.
    
    This class provides a consistent interface for text generation
    regardless of the underlying LLM implementation.
    """
    
    def __init__(self, service_type: LLMServiceType = LLMServiceType.AUTO):
        """
        Initialize the LLM service.
        
        Args:
            service_type: Type of LLM service to use
        """
        self.service_type = service_type
        
        # Set up the appropriate backend
        self._setup_backend()
    
    def _setup_backend(self) -> None:
        """Set up the appropriate backend based on configuration and availability."""
        # Import backends here to avoid circular imports
        from src.llm.gemini_service import GeminiService, get_gemini_service
        from src.llm.gemma3_service import Gemma3Service, get_gemma3_service
        from src.llm.llm_service_interface import LLMService
        
        # Track available backends
        self.gemini_available = False
        self.gemma3_available = False
        
        # Set up Gemini backend if we have API keys
        if GEMINI_API_KEYS:
            try:
                self.gemini_service = get_gemini_service()
                self.gemini_available = True
                logger.info("Gemini service initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini service: {e}")
                self.gemini_service = None
        else:
            logger.warning("No Gemini API keys available")
            self.gemini_service = None
        
        # Set up Gemma 3 backend if local LLM is enabled
        if USE_LOCAL_LLM:
            try:
                self.gemma3_service = get_gemma3_service()
                # Check if Gemma3 service is actually available
                self.gemma3_available = self.gemma3_service.is_available
                
                if self.gemma3_available:
                    logger.info("Gemma 3 service initialized and available")
                else:
                    logger.warning("Gemma 3 service is not available")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemma 3 service: {e}")
                self.gemma3_service = None
                self.gemma3_available = False
        else:
            logger.info("Local LLM is disabled")
            self.gemma3_service = None
            self.gemma3_available = False
        
        # Select the active service based on service_type and availability
        if self.service_type == LLMServiceType.GEMINI and self.gemini_available:
            self.active_service = "gemini"
            logger.info("Using Gemini as the active LLM service")
        elif self.service_type == LLMServiceType.GEMMA3 and self.gemma3_available:
            self.active_service = "gemma3"
            logger.info("Using Gemma 3 as the active LLM service")
        else:
            # Auto-select based on availability
            if self.gemini_available:
                self.active_service = "gemini"
                logger.info("Auto-selected Gemini as the active LLM service")
            elif self.gemma3_available:
                self.active_service = "gemma3"
                logger.info("Auto-selected Gemma 3 as the active LLM service")
            else:
                logger.error("No LLM services are available!")
                raise RuntimeError("No LLM services are available. Please check your configuration.")
    
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
        Generate text using the active LLM service.
        
        Args:
            prompt: The prompt to send to the LLM
            system_instructions: Optional system instructions
            temperature: Temperature for generation (0.0 to 1.0)
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            max_output_tokens: Maximum number of tokens to generate
            thinking_model: Whether to use the thinking model (Gemini only)
            
        Returns:
            Generated text
            
        Raises:
            Exception: If generation fails
        """
        # Use the active service
        if self.active_service == "gemini":
            return self.gemini_service.generate_text(
                prompt=prompt,
                system_instructions=system_instructions,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                max_output_tokens=max_output_tokens,
                thinking_model=thinking_model
            )
        elif self.active_service == "gemma3":
            # Gemma 3 doesn't support thinking_model, so we ignore it
            return self.gemma3_service.generate_text(
                prompt=prompt,
                system_instructions=system_instructions,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                max_output_tokens=max_output_tokens
            )
        else:
            raise RuntimeError("No active LLM service")
    
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
        Generate a chat response using the active LLM service.
        
        Args:
            messages: List of message dictionaries with "role" and "content" keys
            system_instructions: Optional system instructions
            temperature: Temperature for generation (0.0 to 1.0)
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            max_output_tokens: Maximum number of tokens to generate
            thinking_model: Whether to use the thinking model (Gemini only)
            
        Returns:
            Generated chat response text
            
        Raises:
            Exception: If generation fails
        """
        # Use the active service
        if self.active_service == "gemini":
            return self.gemini_service.generate_chat_response(
                messages=messages,
                system_instructions=system_instructions,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                max_output_tokens=max_output_tokens,
                thinking_model=thinking_model
            )
        elif self.active_service == "gemma3":
            # Use Gemma 3's multimodal capabilities
            return self.gemma3_service.generate_chat_response(
                messages=messages,
                system_instructions=system_instructions,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                max_output_tokens=max_output_tokens
            )
        else:
            raise RuntimeError("No active LLM service")
    
    def switch_service(self, service_type: LLMServiceType) -> bool:
        """
        Switch to a different LLM service.
        
        Args:
            service_type: Type of LLM service to use
            
        Returns:
            True if switch was successful, False otherwise
        """
        if service_type == LLMServiceType.GEMINI and self.gemini_available:
            self.active_service = "gemini"
            logger.info("Switched to Gemini service")
            return True
        elif service_type == LLMServiceType.GEMMA3 and self.gemma3_available:
            self.active_service = "gemma3"
            logger.info("Switched to Gemma 3 service")
            return True
        else:
            logger.warning(f"Cannot switch to {service_type.value} service: not available")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get the status of all LLM services.
        
        Returns:
            Dictionary with service status information
        """
        status = {
            "active_service": self.active_service,
            "gemini": {
                "available": self.gemini_available,
                "api_keys": len(GEMINI_API_KEYS) if GEMINI_API_KEYS else 0
            },
            "gemma3": {
                "available": self.gemma3_available,
                "model": "gemma3:4B-Q4_K_M" if self.gemma3_available else None
            }
        }
        
        # Add Gemma 3 model details if available
        if self.gemma3_available and hasattr(self, "gemma3_service"):
            # Add additional details like multimodal capabilities
            status["gemma3"]["capabilities"] = {
                "text": True,
                "vision": True,
                "multilingual": True,
                "context_window": 131000
            }
        
        return status

# Singleton instance for global use
_llm_service = None

def get_llm_service(service_type: LLMServiceType = LLMServiceType.AUTO) -> LLMService:
    """
    Get or create the LLMService singleton.
    
    Args:
        service_type: Type of LLM service to use
    
    Returns:
        LLMService instance
    """
    global _llm_service
    
    if _llm_service is None:
        _llm_service = LLMService(service_type=service_type)
    elif service_type != LLMServiceType.AUTO:
        # If a specific service type is requested and we already have an instance,
        # try to switch to the requested type
        _llm_service.switch_service(service_type)
    
    return _llm_service
