"""
Matching Routes for RecruitX API.

This module defines FastAPI routes for handling candidate matching to jobs.
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class MatchCandidatesRequest(BaseModel):
    jobId: str
    model: Optional[str] = "gemma"

class CandidateMatch(BaseModel):
    candidateId: str
    name: str
    score: float
    skills_match: List[str]
    summary: str

class MatchCandidatesResponse(BaseModel):
    success: bool
    matches: List[CandidateMatch]

@router.post("/recruiting/match-candidates", response_model=MatchCandidatesResponse)
async def match_candidates(request: MatchCandidatesRequest = Body(...)):
    """
    Match candidates to a job based on job ID.
    """
    try:
        logger.info(f"Matching candidates for job ID: {request.jobId}")
        # Mock response - in real implementation, query database and use vector similarity
        matches = [
            CandidateMatch(
                candidateId="cand_001",
                name="John Doe",
                score=0.92,
                skills_match=["Python", "AI", "Cloud"],
                summary="Strong match with relevant experience"
            ),
            CandidateMatch(
                candidateId="cand_002",
                name="Jane Smith",
                score=0.87,
                skills_match=["Python", "Machine Learning"],
                summary="Good match with strong technical skills"
            )
        ]
        return {"success": true, "matches": matches}
    except Exception as e:
        logger.error(f"Error matching candidates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to match candidates: {str(e)}")
