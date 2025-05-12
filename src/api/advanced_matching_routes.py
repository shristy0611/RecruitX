"""
Advanced Matching V1 API routes for RecruitPro AI.

This module provides API endpoints for advanced matching capabilities including:
1. Context-aware matching with bi-directional preferences 
2. Team fit analysis using Gemini's comparative reasoning
3. Career trajectory prediction and growth potential assessment
"""

import logging
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field

from src.knowledge_base.vector_store import VectorStore
from src.agents.matching_agent import MatchingAgent
from src.matching.advanced_matcher import AdvancedMatcher
from src.matching.team_fit_analyzer import TeamFitAnalyzer
from src.matching.career_trajectory_analyzer import CareerTrajectoryAnalyzer

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/advanced-matching", tags=["Advanced Matching"])

# Initialize dependencies
vector_store = VectorStore()
base_matcher = MatchingAgent(vector_store=vector_store)
advanced_matcher = AdvancedMatcher(base_matcher=base_matcher, vector_store=vector_store)
team_fit_analyzer = TeamFitAnalyzer(vector_store=vector_store)
career_analyzer = CareerTrajectoryAnalyzer(vector_store=vector_store)


# Data models for requests and responses
class AdvancedMatchingRequest(BaseModel):
    """Request model for advanced matching."""
    candidate_ids: List[str] = Field(..., description="List of candidate IDs to match")
    include_team_fit: bool = Field(True, description="Whether to include team fit analysis")
    include_career_trajectory: bool = Field(True, description="Whether to include career trajectory analysis")
    team_id: Optional[str] = Field(None, description="Optional team ID for team fit analysis")
    min_score: float = Field(60.0, description="Minimum overall score to include in results")
    max_results: int = Field(10, description="Maximum number of results to return")
    detailed: bool = Field(False, description="Whether to generate detailed explanations")


class TeamFitRequest(BaseModel):
    """Request model for team fit analysis."""
    team_id: str = Field(..., description="ID of the team")
    detailed: bool = Field(True, description="Whether to generate detailed analysis")


class CareerTrajectoryRequest(BaseModel):
    """Request model for career trajectory analysis."""
    job_id: str = Field(..., description="ID of the job")
    detailed: bool = Field(True, description="Whether to generate detailed analysis")


class AdvancedMatchSummary(BaseModel):
    """Summary response model for advanced matching."""
    candidate_id: str
    job_id: str
    matching_id: str
    overall_score: float
    skill_match_score: float
    experience_match_score: float
    education_match_score: float
    preference_alignment_score: Optional[float] = None
    team_fit_score: Optional[float] = None
    growth_potential_score: Optional[float] = None
    

class DetailedMatchResponse(BaseModel):
    """Detailed response model for advanced matching."""
    summary: AdvancedMatchSummary
    explanation: Dict[str, Any]
    

# API routes
@router.post("/job/{job_id}/match", response_model=List[AdvancedMatchSummary])
async def match_candidates_to_job(
    job_id: str = Path(..., description="ID of the job"),
    request: AdvancedMatchingRequest = None
):
    """
    Match candidates to a job using advanced matching capabilities.
    
    Returns a list of matching results with scores for multiple dimensions:
    - Basic matching (skills, experience, education)
    - Bi-directional preference alignment
    - Team fit analysis
    - Career trajectory and growth potential
    """
    try:
        if request is None:
            request = AdvancedMatchingRequest(candidate_ids=[])
            
        # If no candidate IDs provided, find best matches
        if not request.candidate_ids:
            results = advanced_matcher.match_job_to_candidates(
                job_id=job_id,
                include_team_fit=request.include_team_fit,
                include_career_trajectory=request.include_career_trajectory,
                team_id=request.team_id,
                min_score=request.min_score,
                max_results=request.max_results,
                detailed=request.detailed
            )
        else:
            # Match specific candidates
            results = advanced_matcher.match_candidates_to_job(
                job_id=job_id,
                candidate_ids=request.candidate_ids,
                include_team_fit=request.include_team_fit,
                include_career_trajectory=request.include_career_trajectory,
                team_id=request.team_id,
                min_score=request.min_score,
                max_results=request.max_results,
                detailed=request.detailed
            )
            
        # Convert to response model
        response = []
        for result in results:
            summary = AdvancedMatchSummary(
                candidate_id=result.candidate_id,
                job_id=result.job_id,
                matching_id=result.matching_id,
                overall_score=result.overall_score,
                skill_match_score=result.skill_match_score,
                experience_match_score=result.experience_match_score,
                education_match_score=result.education_match_score,
                preference_alignment_score=result.bi_directional_preferences.preference_alignment_score if result.bi_directional_preferences else None,
                team_fit_score=result.team_fit.compatibility_score if result.team_fit else None,
                growth_potential_score=result.career_trajectory.growth_potential_score if result.career_trajectory else None
            )
            response.append(summary)
            
        return response
        
    except Exception as e:
        logger.error(f"Error in advanced matching: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error performing advanced matching: {str(e)}"
        )


@router.get("/match/{matching_id}", response_model=DetailedMatchResponse)
async def get_detailed_match_result(
    matching_id: str = Path(..., description="ID of the matching result")
):
    """
    Get detailed information about a specific matching result.
    
    Returns comprehensive analysis including:
    - Detailed explanations for each matching dimension
    - Specific insights about skill matches and gaps
    - Team fit analysis with key factors
    - Career trajectory prediction with future roles and development areas
    """
    try:
        # Check if the result is in the cache
        cached_results = advanced_matcher.result_cache
        
        for key, result in cached_results.items():
            if result.matching_id == matching_id:
                # Convert to response model
                summary = AdvancedMatchSummary(
                    candidate_id=result.candidate_id,
                    job_id=result.job_id,
                    matching_id=result.matching_id,
                    overall_score=result.overall_score,
                    skill_match_score=result.skill_match_score,
                    experience_match_score=result.experience_match_score,
                    education_match_score=result.education_match_score,
                    preference_alignment_score=result.bi_directional_preferences.preference_alignment_score if result.bi_directional_preferences else None,
                    team_fit_score=result.team_fit.compatibility_score if result.team_fit else None,
                    growth_potential_score=result.career_trajectory.growth_potential_score if result.career_trajectory else None
                )
                
                response = DetailedMatchResponse(
                    summary=summary,
                    explanation=result.detailed_explanation
                )
                
                return response
                
        # If not found in cache
        raise HTTPException(
            status_code=404,
            detail=f"Matching result not found: {matching_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving detailed match result: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving detailed match result: {str(e)}"
        )


@router.post("/candidate/{candidate_id}/team-fit", tags=["Team Fit"])
async def analyze_team_fit(
    candidate_id: str = Path(..., description="ID of the candidate"),
    request: TeamFitRequest = None
):
    """
    Analyze how well a candidate would fit with a specific team.
    
    Uses Gemini's comparative reasoning to evaluate:
    - Cultural alignment
    - Working style compatibility
    - Skill complementarity
    - Team dynamics impact
    """
    try:
        if request is None:
            raise HTTPException(
                status_code=400,
                detail="Team ID is required"
            )
            
        result = team_fit_analyzer.predict_team_fit(
            candidate_id=candidate_id,
            team_id=request.team_id,
            detailed=request.detailed
        )
        
        # Convert to response
        response = {
            "candidate_id": result.candidate_id,
            "team_id": result.team_id,
            "compatibility_score": result.compatibility_score,
            "cultural_fit_score": result.cultural_fit_score,
            "working_style_compatibility": result.working_style_compatibility,
            "skill_complementarity": result.skill_complementarity,
            "team_dynamics_impact": result.team_dynamics_impact,
            "key_factors": result.key_factors,
            "detailed_analysis": result.detailed_analysis if request.detailed else None,
            "result_id": result.result_id
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing team fit: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing team fit: {str(e)}"
        )


@router.post("/candidate/{candidate_id}/career-trajectory", tags=["Career Trajectory"])
async def analyze_career_trajectory(
    candidate_id: str = Path(..., description="ID of the candidate"),
    request: CareerTrajectoryRequest = None
):
    """
    Predict career trajectory and growth potential for a candidate.
    
    Provides insights into:
    - Growth potential in the role
    - Career trajectory alignment
    - Skill growth opportunities
    - Predicted future roles
    - Development areas for optimal career growth
    """
    try:
        if request is None:
            raise HTTPException(
                status_code=400,
                detail="Job ID is required"
            )
            
        result = career_analyzer.predict_career_trajectory(
            candidate_id=candidate_id,
            job_id=request.job_id,
            detailed=request.detailed
        )
        
        # Convert to response
        response = {
            "candidate_id": result.candidate_id,
            "job_id": result.job_id,
            "growth_potential_score": result.growth_potential_score,
            "trajectory_alignment_score": result.trajectory_alignment_score,
            "skills_growth_opportunity": result.skills_growth_opportunity,
            "predicted_future_roles": result.predicted_future_roles,
            "growth_timeline": result.growth_timeline,
            "development_areas": result.development_areas,
            "detailed_analysis": result.detailed_analysis if request.detailed else None,
            "result_id": result.result_id
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing career trajectory: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing career trajectory: {str(e)}"
        )
