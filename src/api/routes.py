"""
API routes for RecruitPro AI.

These FastAPI routes provide the interface for interacting with the RecruitPro AI system,
including job description management, resume analysis, and candidate matching.
"""
import logging
import os
from datetime import datetime
from http import HTTPStatus
from typing import Dict, List, Optional, Any, Union
import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.api.models import (
    JobDescriptionCreate,
    JobDescriptionResponse,
    ResumeUpload,
    ResumeAnalysisResponse,
    ErrorResponse,
    HealthCheck,
    CandidateMatchResponse,
    ExplanationResponse,
)
from src.knowledge_base.vector_store import get_vector_store
from src.agents.screening_agent import get_screening_agent
from src.agents.matching_agent import MatchingAgent
from src.agents.sourcing_agent import SourcingAgent
from src.xai import get_explainer
from src.utils.config import (
    API_PREFIX, 
    DOCUMENT_BUCKET
)

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix=API_PREFIX)

# Get instances of our core components
vector_store = get_vector_store()
screening_agent = get_screening_agent()
matching_agent = MatchingAgent(vector_store=vector_store)
sourcing_agent = SourcingAgent(vector_store=vector_store)


@router.get("/health", response_model=HealthCheck, tags=["System"])
async def health_check() -> HealthCheck:
    """
    Health check endpoint to verify API and component status.
    
    Returns:
        HealthCheck: Health status of the API and its components
    """
    # Check vector store connectivity
    vector_store_status = "ok"
    try:
        # Simple schema check to verify connection
        schema_exists = vector_store.client.schema.exists("JobDescription")
        if not schema_exists:
            vector_store_status = "schema_missing"
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        vector_store_status = "error"
    
    # Build response
    return HealthCheck(
        status="ok" if vector_store_status == "ok" else "degraded",
        version="0.1.0",  # Hardcoded for now, could be imported from a version.py
        components={
            "vector_store": vector_store_status,
            "screening_agent": "ok",  # Currently no easy way to check, assume ok
            "api": "ok",
        }
    )


@router.post(
    "/jobs", 
    response_model=JobDescriptionResponse, 
    status_code=HTTPStatus.CREATED,
    tags=["Jobs"]
)
async def create_job_description(job: JobDescriptionCreate) -> JobDescriptionResponse:
    """
    Create a new job description in the system.
    
    Args:
        job: Job description data
        
    Returns:
        JobDescriptionResponse: Created job description with ID
        
    Raises:
        HTTPException: If job creation fails
    """
    try:
        # Store in vector database
        job_id = vector_store.add_job_description(
            title=job.title,
            description=job.description,
            requirements=job.requirements,
            company=job.company,
            location=job.location or "",
            salary_range=job.salary_range or "",
            job_type=job.job_type or "Full-time",
        )
        
        # Get full job data
        job_data = vector_store.get_by_id("JobDescription", job_id)
        if not job_data:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Job was created but could not be retrieved"
            )
            
        # In our VectorStore implementation, properties are already at the top level
        # The get_by_id method already extracts properties from the Weaviate response
        properties = job_data
        
        # Convert to response model
        return JobDescriptionResponse(
            id=job_id,
            title=properties.get("title", ""),
            description=properties.get("description", ""),
            requirements=properties.get("requirements", ""),
            company=properties.get("company", ""),
            location=properties.get("location", ""),
            salary_range=properties.get("salary_range", ""),
            job_type=properties.get("job_type", "Full-time"),
            created_at=datetime.fromisoformat(properties.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(properties.get("updated_at", datetime.now().isoformat())),
        )
        
    except Exception as e:
        logger.error(f"Error creating job description: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job description: {str(e)}"
        )


@router.get(
    "/jobs/{job_id}", 
    response_model=JobDescriptionResponse,
    tags=["Jobs"]
)
async def get_job_description(
    job_id: str = Path(..., description="Job UUID")
) -> JobDescriptionResponse:
    """
    Get a job description by ID.
    
    Args:
        job_id: Job UUID
        
    Returns:
        JobDescriptionResponse: Job description data
        
    Raises:
        HTTPException: If job not found
    """
    try:
        # Get job from vector database
        job_data = vector_store.get_by_id("JobDescription", job_id)
        if not job_data:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Job description with ID {job_id} not found"
            )
            
        # In our VectorStore implementation, properties are already at the top level
        # The get_by_id method already extracts properties from the Weaviate response
        properties = job_data
        
        # Convert to response model
        return JobDescriptionResponse(
            id=job_id,
            title=properties.get("title", ""),
            description=properties.get("description", ""),
            requirements=properties.get("requirements", ""),
            company=properties.get("company", ""),
            location=properties.get("location", ""),
            salary_range=properties.get("salary_range", ""),
            job_type=properties.get("job_type", "Full-time"),
            created_at=datetime.fromisoformat(properties.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(properties.get("updated_at", datetime.now().isoformat())),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job description: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job description: {str(e)}"
        )


@router.post(
    "/candidates/analyze", 
    response_model=ResumeAnalysisResponse,
    tags=["Candidates"]
)
async def analyze_resume(
    job_id: str = Form(..., description="Job ID to match against"),
    resume_file: UploadFile = File(..., description="Resume file (PDF or text)"),
) -> ResumeAnalysisResponse:
    """
    Analyze a resume against a job description.
    
    Args:
        job_id: Job ID to match against
        resume_file: Resume file to analyze
        
    Returns:
        ResumeAnalysisResponse: Analysis results
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        # Read resume content
        resume_content = await resume_file.read()
        
        # For simplicity, we'll assume it's a text file for now
        # In a real implementation, we'd detect file type and use appropriate parser
        resume_text = resume_content.decode("utf-8")
        
        # Process resume with screening agent
        result = screening_agent.process_resume(resume_text, job_id)
        
        # Check for errors
        if "error" in result and result["error"]:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=result["error"]
            )
            
        # Convert to response model
        return ResumeAnalysisResponse(
            resume_data=result["resume_data"],
            job_data=result["job_data"],
            score_data=result["score_data"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing resume: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze resume: {str(e)}"
        )


@router.post(
    "/candidates/analyze_text", 
    response_model=ResumeAnalysisResponse,
    tags=["Candidates"]
)
async def analyze_resume_text(
    resume_data: dict,
) -> ResumeAnalysisResponse:
    """
    Analyze a resume text against a job description.
    
    Args:
        resume_data: Dictionary containing job_id and resume_text
        
    Returns:
        ResumeAnalysisResponse: Analysis results
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        # Extract data from request
        job_id = resume_data.get("job_id")
        resume_text = resume_data.get("resume_text")
        
        # Validate inputs
        if not job_id or not resume_text:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Both job_id and resume_text are required"
            )
        
        # Process resume with screening agent
        result = screening_agent.process_resume(resume_text, job_id)
        
        # Check for errors
        if "error" in result and result["error"]:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=result["error"]
            )
            
        # Convert to response model
        return ResumeAnalysisResponse(
            resume_data=result["resume_data"],
            job_data=result["job_data"],
            score_data=result["score_data"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing resume text: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Resume analysis failed due to invalid input or processing error."
        )


@router.get(
    "/candidates/{candidate_id}/jobs",
    response_model=List[Dict[str, Any]],
    tags=["Candidates"]
)
async def find_matching_jobs(
    candidate_id: str = Path(..., description="Candidate UUID"),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=100)
) -> List[Dict[str, Any]]:
    """
    Find jobs that match a candidate profile.
    
    Args:
        candidate_id: Candidate UUID
        limit: Maximum number of results
        
    Returns:
        List[Dict[str, Any]]: List of matching jobs with scores
        
    Raises:
        HTTPException: If candidate not found or search fails
    """
    try:
        # Get candidate from vector database
        candidate_data = vector_store.get_by_id("CandidateProfile", candidate_id)
        if not candidate_data:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Candidate profile with ID {candidate_id} not found"
            )
            
        # Find matching jobs
        matching_jobs = vector_store.get_candidate_jobs_match(candidate_id, limit=limit)
        
        # Return matched jobs
        return matching_jobs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding matching jobs: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to find matching jobs: {str(e)}"
        )


# XAI Endpoints
@router.get("/explanations/matching/{job_id}/{candidate_id}", responses={404: {"model": ErrorResponse}}, tags=["Explanations"])
async def get_matching_explanation(
    job_id: str = Path(..., description="Job UUID"),
    candidate_id: str = Path(..., description="Candidate UUID"),
    detail_level: str = Query("standard", description="Level of detail for the explanation", regex="^(brief|standard|detailed)$")
) -> Dict[str, Any]:
    """
    Get an explanation for a matching decision between a job and candidate.
    
    Args:
        job_id: Job UUID
        candidate_id: Candidate UUID
        detail_level: Level of detail (brief, standard, detailed)
        
    Returns:
        Dict[str, Any]: Detailed explanation with factors
        
    Raises:
        HTTPException: If job or candidate not found
    """
    try:
        # Verify job and candidate exist
        job = vector_store.get_by_id(job_id)
        candidate = vector_store.get_by_id(candidate_id)
        
        if not job or not candidate:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Job or candidate not found: {job_id}/{candidate_id}"
            )
        
        # Generate detailed explanation
        explanation_data = matching_agent.get_detailed_explanation(
            job_id=job_id,
            candidate_id=candidate_id,
            detail_level=detail_level
        )
        
        # Format response
        response = {
            "agent_type": "matching",
            "detail_level": detail_level,
            "job_id": job_id,
            "candidate_id": candidate_id,
            "explanation": explanation_data.get("explanation", ""),
            "score": explanation_data.get("score", 0.0),
            "factors": explanation_data.get("factors", {}),
            "metadata": {}
        }
        
        # Add additional explanation details if available
        if "factor_explanations" in explanation_data:
            response["metadata"]["factor_explanations"] = explanation_data["factor_explanations"]
            
        if "strengths" in explanation_data:
            response["metadata"]["strengths"] = explanation_data["strengths"]
            
        if "improvement_areas" in explanation_data:
            response["metadata"]["improvement_areas"] = explanation_data["improvement_areas"]
            
        return response
        
    except Exception as e:
        logger.error(f"Error generating matching explanation: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )


@router.post("/explanations/sourcing", responses={400: {"model": ErrorResponse}}, tags=["Explanations"])
async def get_sourcing_explanation(
    explanation_request: dict
) -> Dict[str, Any]:
    """
    Get an explanation for a sourcing operation.
    
    Args:
        explanation_request: Dictionary containing:
            - job_description: Job details
            - sourcing_query: Original sourcing query
            - candidates: List of sourced candidates
            - detail_level: Level of detail (brief, standard, detailed)
        
    Returns:
        Dict[str, Any]: Detailed explanation of sourcing results
        
    Raises:
        HTTPException: If request is invalid
    """
    try:
        # Extract parameters
        job_description = explanation_request.get("job_description", {})
        sourcing_query = explanation_request.get("sourcing_query", {})
        candidates = explanation_request.get("candidates", [])
        search_strategy = explanation_request.get("search_strategy", "semantic search")
        filters = explanation_request.get("filters", {})
        detail_level = explanation_request.get("detail_level", "standard")
        
        if not job_description or not candidates:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Job description and candidates are required"
            )
        
        # Get explainer
        explainer = get_explainer("sourcing")
        
        # Generate explanation
        explanation_data = explainer.generate_explanation(
            context={
                "job_description": job_description,
                "sourcing_query": sourcing_query,
                "candidates": candidates,
                "search_strategy": search_strategy,
                "filters": filters
            },
            detail_level=detail_level
        )
        
        # Format response
        response = {
            "agent_type": "sourcing",
            "detail_level": detail_level,
            "job_id": job_description.get("id", ""),
            "candidate_id": "",  # Multiple candidates in sourcing
            "explanation": explanation_data.get("explanation", ""),
            "score": 0.0,  # No overall score for sourcing
            "factors": {},  # No factors for sourcing
            "metadata": {
                "candidate_count": len(candidates),
                "strategy": explanation_data.get("strategy", search_strategy),
                "filters_applied": explanation_data.get("filters_applied", filters)
            }
        }
            
        return response
        
    except Exception as e:
        logger.error(f"Error generating sourcing explanation: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )


@router.post("/explanations/screening", responses={400: {"model": ErrorResponse}}, tags=["Explanations"])
async def get_screening_explanation(
    explanation_request: dict
) -> Dict[str, Any]:
    """
    Get an explanation for a screening decision.
    
    Args:
        explanation_request: Dictionary containing:
            - candidate_profile: Candidate details
            - job_description: Job details
            - screening_result: Screening scores and decision
            - detail_level: Level of detail (brief, standard, detailed)
        
    Returns:
        Dict[str, Any]: Detailed explanation of screening decision
        
    Raises:
        HTTPException: If request is invalid
    """
    try:
        # Extract parameters
        candidate_profile = explanation_request.get("candidate_profile", {})
        job_description = explanation_request.get("job_description", {})
        screening_result = explanation_request.get("screening_result", {})
        detail_level = explanation_request.get("detail_level", "standard")
        
        if not candidate_profile or not job_description or not screening_result:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Candidate profile, job description, and screening result are required"
            )
        
        # Get explainer
        explainer = get_explainer("screening")
        
        # Generate explanation
        explanation_data = explainer.generate_explanation(
            context={
                "candidate_profile": candidate_profile,
                "job_description": job_description,
                "screening_result": screening_result
            },
            detail_level=detail_level
        )
        
        # Format response
        response = {
            "agent_type": "screening",
            "detail_level": detail_level,
            "job_id": job_description.get("id", ""),
            "candidate_id": candidate_profile.get("id", ""),
            "explanation": explanation_data.get("explanation", ""),
            "score": explanation_data.get("score", 0.0),
            "factors": explanation_data.get("criteria", {}),
            "metadata": {
                "decision": explanation_data.get("decision", "unknown")
            }
        }
        
        # Add key findings if available
        if "key_findings" in explanation_data:
            response["metadata"]["key_findings"] = explanation_data["key_findings"]
            
        return response
        
    except Exception as e:
        logger.error(f"Error generating screening explanation: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )
