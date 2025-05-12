"""
LLM Service package for RecruitPro AI.

This package provides unified access to various LLM backends:
1. Gemini API (primary for MVP, uses free tier with API key rotation)
2. Gemma 3
"""
from src.llm.llm_factory import LLMService, LLMServiceType, get_llm_service
from src.llm.gemini_service import GeminiService, get_gemini_service
from src.llm.gemma3_service import Gemma3Service, get_gemma3_service
