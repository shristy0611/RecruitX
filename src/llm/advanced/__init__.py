"""
Advanced LLM Integration for RecruitPro AI.

This module provides sophisticated LLM capabilities building on the base Gemini
and Gemma services with advanced context management, prompt optimization, and
result caching for improved performance and quality.
"""

from src.llm.advanced.context_manager import ContextManager, get_context_manager, ExpiringCache
from src.llm.advanced.prompt_manager import PromptManager, get_prompt_manager, PromptTemplate
from src.llm.advanced.advanced_llm_service import (
    AdvancedLLMService, 
    get_advanced_llm_service,
    ModelSelectionStrategy
)

__all__ = [
    'ContextManager',
    'get_context_manager',
    'ExpiringCache',
    'PromptManager',
    'get_prompt_manager',
    'PromptTemplate',
    'AdvancedLLMService',
    'get_advanced_llm_service',
    'ModelSelectionStrategy'
]
