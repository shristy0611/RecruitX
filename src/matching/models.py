"""
Data models for Advanced Matching V1.

This module defines the data structures used for advanced matching operations,
including team fit analysis and career trajectory prediction.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Union


@dataclass
class BiDirectionalPreference:
    """Model for bi-directional preference between candidate and job/company."""
    # Candidate's preferences
    candidate_preferences: Dict[str, float] = field(default_factory=dict)
    # Job/company preferences
    company_preferences: Dict[str, float] = field(default_factory=dict)
    # Compatibility scores
    preference_alignment_score: float = 0.0
    # Factor importance weights
    weight_candidate: float = 0.5
    weight_company: float = 0.5
    
    def calculate_alignment_score(self) -> float:
        """Calculate alignment score between candidate and company preferences."""
        if not self.candidate_preferences or not self.company_preferences:
            return 0.0
            
        # Find common factors
        common_factors = set(self.candidate_preferences.keys()) & set(self.company_preferences.keys())
        
        if not common_factors:
            return 0.0
            
        # Calculate score for each common factor
        factor_scores = []
        for factor in common_factors:
            candidate_value = self.candidate_preferences.get(factor, 0)
            company_value = self.company_preferences.get(factor, 0)
            
            # Convert to 0-1 range if not already
            if candidate_value > 1.0:
                candidate_value /= 100.0
            if company_value > 1.0:
                company_value /= 100.0
                
            # Calculate alignment (1 - absolute difference)
            alignment = 1.0 - abs(candidate_value - company_value)
            factor_scores.append(alignment)
        
        # Calculate weighted average alignment
        self.preference_alignment_score = sum(factor_scores) / len(factor_scores) * 100.0
        return self.preference_alignment_score


@dataclass
class TeamFitResult:
    """Result of team fit analysis."""
    team_id: str
    candidate_id: str
    compatibility_score: float
    key_factors: List[Dict[str, Any]] = field(default_factory=list)
    detailed_analysis: str = ""
    cultural_fit_score: float = 0.0
    working_style_compatibility: float = 0.0
    skill_complementarity: float = 0.0
    team_dynamics_impact: float = 0.0
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)


@dataclass
class CareerTrajectoryResult:
    """Result of career trajectory and growth potential analysis."""
    candidate_id: str
    job_id: str
    # Growth potential (0-100)
    growth_potential_score: float = 0.0
    # Career trajectory alignment (0-100)
    trajectory_alignment_score: float = 0.0
    # Skills growth opportunity (0-100)
    skills_growth_opportunity: float = 0.0
    # Predicted future roles
    predicted_future_roles: List[str] = field(default_factory=list)
    # Growth timeline (years to reach potential roles)
    growth_timeline: Dict[str, int] = field(default_factory=dict)
    # Detailed analysis
    detailed_analysis: str = ""
    # Development areas
    development_areas: List[str] = field(default_factory=list)
    # Result metadata
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)


@dataclass
class AdvancedMatchingResult:
    """Enhanced result model for advanced matching operations."""
    # Core identification
    candidate_id: str
    job_id: str
    matching_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic matching scores (from original MatchingResult)
    overall_score: float = 0.0
    skill_match_score: float = 0.0
    experience_match_score: float = 0.0
    education_match_score: float = 0.0
    skills_matched: List[str] = field(default_factory=list)
    skills_missing: List[str] = field(default_factory=list)
    
    # Advanced matching components
    bi_directional_preferences: Optional[BiDirectionalPreference] = None
    team_fit: Optional[TeamFitResult] = None
    career_trajectory: Optional[CareerTrajectoryResult] = None
    
    # Enhanced explanation
    explanation: str = ""
    detailed_explanation: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    timestamp: float = field(default_factory=time.time)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the matching result."""
        return {
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "matching_id": self.matching_id,
            "overall_score": self.overall_score,
            "skill_match_score": self.skill_match_score,
            "experience_match_score": self.experience_match_score,
            "education_match_score": self.education_match_score,
            "bi_directional_score": self.bi_directional_preferences.preference_alignment_score if self.bi_directional_preferences else 0.0,
            "team_fit_score": self.team_fit.compatibility_score if self.team_fit else 0.0,
            "growth_potential": self.career_trajectory.growth_potential_score if self.career_trajectory else 0.0,
            "timestamp": self.timestamp
        }
