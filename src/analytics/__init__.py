"""
Analytics module for RecruitPro AI.

This module provides analytics and reporting capabilities for tracking
recruitment metrics, agent performance, and candidate journeys.
"""

from src.analytics.services.funnel_metrics import FunnelMetricsService
from src.analytics.services.agent_metrics import AgentMetricsService
from src.analytics.services.journey_metrics import JourneyMetricsService
from src.analytics.models.metrics import (
    RecruitmentMetrics,
    AgentPerformanceMetrics,
    CandidateJourneyMetrics,
    FunnelStageMetrics
)

__all__ = [
    'FunnelMetricsService',
    'AgentMetricsService',
    'JourneyMetricsService',
    'RecruitmentMetrics',
    'AgentPerformanceMetrics',
    'CandidateJourneyMetrics',
    'FunnelStageMetrics'
]
