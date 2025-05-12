"""
Main FastAPI application for RecruitPro AI.

This module creates and configures the FastAPI application,
including CORS middleware, error handlers, and API routes.
"""
import logging
from http import HTTPStatus
from typing import Any, Dict, Union

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from src.api.routes import router
from src.api.visualization_routes import viz_router
from src.api.analytics_routes import analytics_router
from src.api.skills_routes import router as skills_router
from src.api.advanced_matching_routes import router as advanced_matching_router
from src.api.advanced_agent_routes import router as advanced_agent_router
from src.api.advanced_llm_routes import router as advanced_llm_router
from src.api.llm_routes import router as llm_router
from src.api.job_routes import router as job_router
from src.api.resume_routes import router as resume_router
from src.api.recruiting_routes import router as recruiting_router
from src.api.matching_routes import router as matching_router
from src.api.agent_routes import router as agent_router
from src.api.models import ErrorResponse
from src.utils.config import API_CORS_ORIGINS, DEBUG

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="RecruitPro AI API",
    description="Privacy-first, locally-hosted multi-agent AI system for recruitment",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(router, prefix="/api", tags=["General"])
app.include_router(viz_router, prefix="/api", tags=["Visualization"])
app.include_router(analytics_router, prefix="/api", tags=["Analytics"])
app.include_router(skills_router, prefix="/api", tags=["Skills"])
app.include_router(advanced_matching_router, prefix="/api", tags=["Advanced Matching"])
app.include_router(advanced_agent_router, prefix="/api", tags=["Advanced Agents"])
app.include_router(advanced_llm_router, prefix="/api", tags=["Advanced LLM"])
app.include_router(llm_router, prefix="/api", tags=["LLM"])
app.include_router(job_router, prefix="/api", tags=["Jobs"])
app.include_router(resume_router, prefix="/api", tags=["Resume"])
app.include_router(recruiting_router, prefix="/api", tags=["Recruiting"])
app.include_router(matching_router, prefix="/api", tags=["Matching"])
app.include_router(agent_router, prefix="/api", tags=["Agents"])

# Check if all routers are included
routers = [
    router,
    viz_router,
    analytics_router,
    skills_router,
    advanced_matching_router,
    advanced_agent_router,
    advanced_llm_router,
    llm_router,
    job_router,
    resume_router,
    recruiting_router,
    matching_router,
    agent_router,
]

for router in routers:
    if not app.router.routes:
        raise Exception(f"Router {router} is not included in the app")

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all unhandled exceptions.
    
    Args:
        request: Request that caused the exception
        exc: Exception that was raised
        
    Returns:
        JSONResponse: Error response
    """
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            detail=f"Internal server error: {str(exc)}",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            path=request.url.path,
        ).dict(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle validation errors.
    
    Args:
        request: Request that caused the exception
        exc: Validation exception that was raised
        
    Returns:
        JSONResponse: Error response
    """
    errors = [f"{e['loc'][-1]}: {e['msg']}" for e in exc.errors()]
    error_message = f"Validation error: {'; '.join(errors)}"
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=HTTPStatus.BAD_REQUEST,
        content=ErrorResponse(
            detail=error_message,
            status_code=HTTPStatus.BAD_REQUEST,
            path=request.url.path,
        ).dict(),
    )


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint that redirects to API documentation.
    
    Returns:
        Dict[str, str]: Message with link to documentation
    """
    return {
        "message": "Welcome to RecruitPro AI API",
        "documentation": "/api/docs",
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify API is running.
    
    Returns:
        Dict[str, str]: Status message indicating API is healthy
    """
    return {
        "status": "healthy",
        "message": "RecruitPro AI API is operational",
    }
