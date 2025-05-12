"""
Explainable AI (XAI) Module for RecruitPro AI.

This module provides explainable AI capabilities for agent decisions,
making the system's reasoning transparent and trustworthy.
"""

from src.xai.explanation_interface import (
    ExplanationProvider,
    ExplanationFormat,
    LLMExplanationMixin
)
from src.xai.matching_explainer import MatchingExplainer
from src.xai.sourcing_explainer import SourcingExplainer
from src.xai.screening_explainer import ScreeningExplainer

# Factory function to get the appropriate explainer
def get_explainer(agent_type: str):
    """
    Get an explainer for a specific agent type.
    
    Args:
        agent_type: Type of agent ('matching', 'sourcing', 'screening')
        
    Returns:
        An instance of the appropriate explainer
    """
    if agent_type.lower() == 'matching':
        return MatchingExplainer()
    elif agent_type.lower() == 'sourcing':
        return SourcingExplainer()
    elif agent_type.lower() == 'screening':
        return ScreeningExplainer()
    else:
        raise ValueError(f"Unknown agent type: {agent_type}. Supported types: matching, sourcing, screening")

__all__ = [
    'ExplanationProvider',
    'ExplanationFormat',
    'LLMExplanationMixin',
    'MatchingExplainer',
    'SourcingExplainer',
    'ScreeningExplainer',
    'get_explainer',
]
