"""
API routes for analytics dashboard.

This module provides FastAPI routes for accessing analytics metrics
including recruitment funnel metrics, agent performance, and candidate journeys.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Query, Path, HTTPException, Depends
from pydantic import BaseModel
from http import HTTPStatus

from src.analytics.models.metrics import (
    TimeFrame,
    AgentType,
    CandidateStatus,
    RecruitmentMetrics,
    AgentPerformanceMetrics,
    CandidateJourneyMetrics
)
from src.analytics.services.funnel_metrics import FunnelMetricsService
from src.analytics.services.agent_metrics import AgentMetricsService
from src.analytics.services.journey_metrics import JourneyMetricsService
from src.utils.redis_client import RedisClient

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Initialize services
redis_client = RedisClient()
funnel_metrics_service = FunnelMetricsService(redis_client)
agent_metrics_service = AgentMetricsService(redis_client)
journey_metrics_service = JourneyMetricsService(redis_client)


class DateRangeParams(BaseModel):
    """Date range parameters for analytics queries."""
    
    time_frame: TimeFrame = TimeFrame.MONTH
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    compare_with_previous: bool = True


@analytics_router.post("/funnel")
async def get_funnel_metrics(
    params: DateRangeParams,
    job_id: Optional[str] = Query(None, description="Optional job ID to filter metrics")
) -> Dict[str, Any]:
    """
    Get recruitment funnel metrics.
    
    Args:
        params: Date range parameters
        job_id: Optional job ID to filter metrics
        
    Returns:
        RecruitmentMetrics converted to dictionary
    """
    try:
        metrics = await funnel_metrics_service.get_funnel_metrics(
            time_frame=params.time_frame,
            job_id=job_id,
            start_date=params.start_date,
            end_date=params.end_date,
            compare_with_previous=params.compare_with_previous
        )
        
        # Add conversion rates to the response
        response = metrics.dict()
        response["conversion_rates"] = metrics.get_conversion_rates()
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting funnel metrics: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve funnel metrics: {str(e)}"
        )


@analytics_router.post("/agent/{agent_type}")
async def get_agent_performance_metrics(
    agent_type: AgentType,
    params: DateRangeParams
) -> Dict[str, Any]:
    """
    Get performance metrics for a specific agent.
    
    Args:
        agent_type: Type of agent
        params: Date range parameters
        
    Returns:
        AgentPerformanceMetrics converted to dictionary
    """
    try:
        metrics = await agent_metrics_service.get_agent_metrics(
            agent_type=agent_type,
            time_frame=params.time_frame,
            start_date=params.start_date,
            end_date=params.end_date,
            compare_with_previous=params.compare_with_previous
        )
        
        response = metrics.dict()
        response["success_rate"] = metrics.get_success_rate()
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting agent metrics: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve agent metrics: {str(e)}"
        )


@analytics_router.get("/journey/candidate/{candidate_id}")
async def get_candidate_journey_metrics(
    candidate_id: str = Path(..., description="ID of the candidate"),
    job_id: Optional[str] = Query(None, description="Optional job ID to filter journey")
) -> Dict[str, Any]:
    """
    Get journey metrics for a specific candidate.
    
    Args:
        candidate_id: ID of the candidate
        job_id: Optional job ID to filter journey
        
    Returns:
        CandidateJourneyMetrics converted to dictionary
    """
    try:
        metrics = await journey_metrics_service.get_candidate_journey(
            candidate_id=candidate_id,
            job_id=job_id
        )
        
        return metrics.dict()
        
    except Exception as e:
        logger.error(f"Error getting candidate journey: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve candidate journey: {str(e)}"
        )


@analytics_router.post("/journey/cohort")
async def get_cohort_journey_metrics(
    params: DateRangeParams,
    job_id: Optional[str] = Query(None, description="Optional job ID to filter cohort"),
    status: Optional[CandidateStatus] = Query(None, description="Optional status to filter cohort")
) -> Dict[str, Any]:
    """
    Get aggregated journey metrics for a cohort of candidates.
    
    Args:
        params: Date range parameters
        job_id: Optional job ID to filter cohort
        status: Optional status to filter cohort
        
    Returns:
        Aggregated cohort metrics
    """
    try:
        metrics = await journey_metrics_service.get_cohort_journey_metrics(
            job_id=job_id,
            status=status,
            time_frame=params.time_frame,
            start_date=params.start_date,
            end_date=params.end_date
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting cohort metrics: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cohort metrics: {str(e)}"
        )


@analytics_router.post("/generate-test-data")
async def generate_test_data(
    funnel_data: bool = Query(True, description="Generate funnel metrics test data"),
    agent_data: bool = Query(True, description="Generate agent performance test data"),
    journey_data: bool = Query(True, description="Generate candidate journey test data")
) -> Dict[str, str]:
    """
    Generate synthetic test data for analytics dashboard.
    This is for development/testing purposes only.
    
    Args:
        funnel_data: Whether to generate funnel metrics test data
        agent_data: Whether to generate agent performance test data
        journey_data: Whether to generate candidate journey test data
        
    Returns:
        Status message
    """
    try:
        if funnel_data:
            await funnel_metrics_service.generate_synthetic_data(
                job_count=5,
                candidates_per_job=50
            )
        
        if agent_data:
            await agent_metrics_service.generate_synthetic_data(
                days_back=30
            )
        
        if journey_data:
            await journey_metrics_service.generate_synthetic_data(
                candidate_count=100
            )
        
        return {"status": "Test data generated successfully"}
        
    except Exception as e:
        logger.error(f"Error generating test data: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate test data: {str(e)}"
        )
