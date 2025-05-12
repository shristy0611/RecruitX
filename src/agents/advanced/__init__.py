"""
Advanced Agent Features for RecruitPro AI.

This module enhances the core agents with advanced capabilities including:
1. Enhanced document analysis using Gemini and Gemma 3
2. Advanced multi-turn dialogue with context switching
3. Multi-language support for global recruitment
4. Improved reasoning and domain knowledge
"""

from src.agents.advanced.enhanced_screening_agent import EnhancedScreeningAgent
from src.agents.advanced.advanced_engagement_agent import AdvancedEngagementAgent
from src.agents.advanced.multilingual_support import MultilingualProcessor

__all__ = [
    'EnhancedScreeningAgent',
    'AdvancedEngagementAgent',
    'MultilingualProcessor'
]
