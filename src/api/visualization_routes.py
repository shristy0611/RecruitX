"""
API routes for XAI visualizations.

These FastAPI routes provide endpoints for rendering visualization
of explanations from the XAI layer.
"""
import logging
import os
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Path, Query, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from http import HTTPStatus

from src.api.routes import vector_store, matching_agent
from src.xai import get_explainer
from src.visualization.xai_visualizer import (
    generate_explanation_html,
    ExplanationVisualizationConfig
)

# Configure logging
logger = logging.getLogger(__name__)

# Get path to templates directory
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            "visualization", "templates")

# Import demo router
from src.visualization.xai_demo import demo_router

# Create API router for visualization endpoints
viz_router = APIRouter(prefix="/visualizations", tags=["Visualizations"])

# Include demo router
viz_router.include_router(demo_router)


@viz_router.get("/matching/{job_id}/{candidate_id}", response_class=HTMLResponse)
async def visualize_matching_explanation(
    job_id: str = Path(..., description="Job UUID"),
    candidate_id: str = Path(..., description="Candidate UUID"),
    detail_level: str = Query("detailed", description="Level of detail (brief, standard, detailed)"),
    theme: str = Query("light", description="Visual theme (light, dark)")
) -> str:
    """
    Generate an HTML visualization for a matching explanation.
    
    Args:
        job_id: Job UUID
        candidate_id: Candidate UUID
        detail_level: Level of detail (brief, standard, detailed)
        theme: Visual theme (light, dark)
        
    Returns:
        HTMLResponse: HTML visualization of the explanation
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
        
        # Get explanation data
        explanation_data = matching_agent.get_detailed_explanation(
            job_id=job_id,
            candidate_id=candidate_id,
            detail_level=detail_level
        )
        
        # Format the response for visualization
        visualization_data = {
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
            visualization_data["metadata"]["factor_explanations"] = explanation_data["factor_explanations"]
            
        if "strengths" in explanation_data:
            visualization_data["metadata"]["strengths"] = explanation_data["strengths"]
            
        if "improvement_areas" in explanation_data:
            visualization_data["metadata"]["improvement_areas"] = explanation_data["improvement_areas"]
        
        # Configure visualization
        config = ExplanationVisualizationConfig(
            title=f"Match Explanation: {candidate.get('name', 'Candidate')} for {job.get('title', 'Position')}",
            theme=theme,
            show_factors=True,
            show_strengths=True,
            show_improvements=True,
            show_metadata=False
        )
        
        # Generate HTML
        html = generate_explanation_html(visualization_data, config)
        return html
        
    except Exception as e:
        logger.error(f"Error generating visualization: {e}")
        # Return a simple error page
        return f"""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>Error Generating Visualization</h1>
                <p>{str(e)}</p>
                <p><a href="javascript:history.back()">Go Back</a></p>
            </body>
        </html>
        """


@viz_router.post("/sourcing", response_class=HTMLResponse)
async def visualize_sourcing_explanation(
    explanation_request: Dict[str, Any],
    theme: str = Query("light", description="Visual theme (light, dark)")
) -> str:
    """
    Generate an HTML visualization for a sourcing explanation.
    
    Args:
        explanation_request: Sourcing explanation request data
        theme: Visual theme (light, dark)
        
    Returns:
        HTMLResponse: HTML visualization of the explanation
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
        
        # Format the response for visualization
        visualization_data = {
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
                "filters_applied": explanation_data.get("filters_applied", filters),
                # Include first few candidates for display
                "top_candidates": candidates[:5] if len(candidates) > 0 else []
            }
        }
        
        # Configure visualization
        config = ExplanationVisualizationConfig(
            title=f"Sourcing Explanation: {job_description.get('title', 'Position')}",
            theme=theme,
            show_factors=False,  # No factors for sourcing
            show_strengths=False,
            show_improvements=False,
            show_metadata=True  # Show metadata for sourcing
        )
        
        # Generate HTML
        html = generate_explanation_html(visualization_data, config)
        return html
        
    except Exception as e:
        logger.error(f"Error generating visualization: {e}")
        # Return a simple error page
        return f"""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>Error Generating Visualization</h1>
                <p>{str(e)}</p>
                <p><a href="javascript:history.back()">Go Back</a></p>
            </body>
        </html>
        """


@viz_router.post("/screening", response_class=HTMLResponse)
async def visualize_screening_explanation(
    explanation_request: Dict[str, Any],
    theme: str = Query("light", description="Visual theme (light, dark)")
) -> str:
    """
    Generate an HTML visualization for a screening explanation.
    
    Args:
        explanation_request: Screening explanation request data
        theme: Visual theme (light, dark)
        
    Returns:
        HTMLResponse: HTML visualization of the explanation
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
        
        # Format the response for visualization
        visualization_data = {
            "agent_type": "screening",
            "detail_level": detail_level,
            "job_id": job_description.get("id", ""),
            "candidate_id": candidate_profile.get("id", ""),
            "explanation": explanation_data.get("explanation", ""),
            "score": explanation_data.get("score", 0.0),
            "factors": explanation_data.get("criteria", {}),
            "metadata": {
                "decision": explanation_data.get("decision", "unknown").upper()
            }
        }
        
        # Add key findings if available
        if "key_findings" in explanation_data:
            visualization_data["metadata"]["key_findings"] = explanation_data["key_findings"]
        
        # Set title based on screening decision
        decision = explanation_data.get("decision", "unknown").upper()
        title_prefix = "PASS" if decision == "PASS" else "HOLD" if decision == "HOLD" else "REJECT"
        
        # Configure visualization
        config = ExplanationVisualizationConfig(
            title=f"Screening Explanation ({title_prefix}): {candidate_profile.get('name', 'Candidate')}",
            theme=theme,
            show_factors=True,
            show_strengths=False,
            show_improvements=False,
            show_metadata=True
        )
        
        # Generate HTML
        html = generate_explanation_html(visualization_data, config)
        return html
        
    except Exception as e:
        logger.error(f"Error generating visualization: {e}")
        # Return a simple error page
        return f"""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>Error Generating Visualization</h1>
                <p>{str(e)}</p>
                <p><a href="javascript:history.back()">Go Back</a></p>
            </body>
        </html>
        """
