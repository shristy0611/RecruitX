"""
Advanced Matching V1 module for RecruitPro AI.

This module provides sophisticated matching capabilities including:
1. Context-aware matching with bi-directional preferences
2. Team fit analysis using Gemini's comparative reasoning
3. Career trajectory prediction and growth potential assessment
"""

from src.matching.advanced_matcher import AdvancedMatcher
from src.matching.team_fit_analyzer import TeamFitAnalyzer
from src.matching.career_trajectory_analyzer import CareerTrajectoryAnalyzer
from src.matching.models import (
    AdvancedMatchingResult, 
    TeamFitResult,
    CareerTrajectoryResult,
    BiDirectionalPreference
)

__all__ = [
    'AdvancedMatcher',
    'TeamFitAnalyzer',
    'CareerTrajectoryAnalyzer',
    'AdvancedMatchingResult',
    'TeamFitResult',
    'CareerTrajectoryResult',
    'BiDirectionalPreference'
]
