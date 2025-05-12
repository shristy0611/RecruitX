"""
LLM Service Interface for RecruitPro AI.

This module defines the base interface that all LLM services must implement.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class LLMService(ABC):
    """Base interface for all LLM services."""
    
    @abstractmethod
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
        Generate text with the LLM.
        
        Args:
            prompt: The prompt to send to the model
            system_instructions: Optional system instructions
            temperature: Temperature for generation (0.0 to 1.0)
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            max_output_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        system_instructions: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
        max_output_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a chat response with the LLM.
        
        Args:
            messages: List of message dictionaries with "role" and "content" keys
            system_instructions: Optional system instructions
            temperature: Temperature for generation (0.0 to 1.0)
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            max_output_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated chat response text
        """
        pass
