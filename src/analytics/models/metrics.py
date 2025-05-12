"""
Analytics metrics models for RecruitPro AI.

This module defines the data models for various metrics tracked in the
recruitment process, agent performance, and candidate journeys.
"""

from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator


class TimeFrame(str, Enum):
    """Time frames for analytics reporting."""
    
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    ALL_TIME = "all_time"
    CUSTOM = "custom"


class FunnelStage(str, Enum):
    """Stages in the recruitment funnel."""
    
    SOURCED = "sourced"
    REVIEWED = "reviewed"
    SHORTLISTED = "shortlisted"
    INTERVIEWED = "interviewed"
    OFFERED = "offered"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class FunnelStageMetrics(BaseModel):
    """Metrics for a specific stage in the recruitment funnel."""
    
    stage: FunnelStage
    count: int = 0
    percentage: float = 0.0
    average_time_in_stage: Optional[float] = None  # in days
    conversion_rate: Optional[float] = None  # conversion to next stage
    comparison_to_previous: Optional[float] = None  # percentage change from previous period


class RecruitmentMetrics(BaseModel):
    """Overall recruitment metrics."""
    
    job_id: Optional[str] = None
    time_frame: TimeFrame
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Recruitment Velocity Metrics
    time_to_fill: Optional[float] = None  # average days to fill a position
    time_to_hire: Optional[float] = None  # average days from first contact to offer acceptance
    
    # Funnel Metrics
    funnel_stages: Dict[FunnelStage, FunnelStageMetrics] = Field(default_factory=dict)
    candidates_per_hire: Optional[float] = None
    offer_acceptance_rate: Optional[float] = None
    
    # Cost Metrics
    cost_per_hire: Optional[float] = None
    
    # Additional metrics
    total_active_jobs: Optional[int] = None
    total_candidates: Optional[int] = None
    total_hires: Optional[int] = None
    
    def get_conversion_rates(self) -> Dict[str, float]:
        """Calculate conversion rates between funnel stages."""
        rates = {}
        stages = list(FunnelStage)
        
        for i in range(len(stages) - 1):
            current_stage = stages[i]
            next_stage = stages[i + 1]
            
            if (current_stage in self.funnel_stages and 
                next_stage in self.funnel_stages and 
                self.funnel_stages[current_stage].count > 0):
                
                rate = (self.funnel_stages[next_stage].count / 
                       self.funnel_stages[current_stage].count) * 100
                rates[f"{current_stage.value}_to_{next_stage.value}"] = rate
                
        return rates


class AgentType(str, Enum):
    """Types of agents in the system."""
    
    SOURCING = "sourcing"
    MATCHING = "matching"
    SCREENING = "screening"
    ENGAGEMENT = "engagement"
    ORCHESTRATOR = "orchestrator"


class AgentMetricType(str, Enum):
    """Types of metrics for agent performance."""
    
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    EXPLANATION_QUALITY = "explanation_quality"


class AgentPerformanceMetrics(BaseModel):
    """Performance metrics for an AI agent."""
    
    agent_type: AgentType
    time_frame: TimeFrame
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Performance Metrics
    metrics: Dict[AgentMetricType, float] = Field(default_factory=dict)
    
    # Volume Metrics
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    
    # Temporal Metrics
    average_response_time: Optional[float] = None  # in milliseconds
    peak_response_time: Optional[float] = None
    
    # Comparison to previous period
    comparison: Dict[str, float] = Field(default_factory=dict)
    
    def get_success_rate(self) -> float:
        """Calculate the success rate of the agent."""
        if self.request_count == 0:
            return 0.0
        return (self.success_count / self.request_count) * 100


class CandidateStatus(str, Enum):
    """Status of a candidate in the recruitment process."""
    
    NEW = "new"
    CONTACTED = "contacted"
    SCREENING = "screening"
    INTERVIEWING = "interviewing"
    OFFER_PENDING = "offer_pending"
    OFFER_EXTENDED = "offer_extended"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_DECLINED = "offer_declined"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class CandidateJourneyEvent(BaseModel):
    """Event in a candidate's journey through the recruitment process."""
    
    timestamp: datetime
    status: CandidateStatus
    agent_type: Optional[AgentType] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CandidateJourneyMetrics(BaseModel):
    """Metrics for a candidate's journey through the recruitment process."""
    
    candidate_id: str
    job_id: Optional[str] = None
    
    # Timeline events
    events: List[CandidateJourneyEvent] = Field(default_factory=list)
    
    # Temporal metrics
    time_in_pipeline: Optional[float] = None  # in days
    time_to_first_contact: Optional[float] = None  # in days
    time_to_decision: Optional[float] = None  # in days
    
    # Current status
    current_status: Optional[CandidateStatus] = None
    
    # Interaction metrics
    interaction_count: int = 0
    response_rate: Optional[float] = None  # percentage
    
    # Match metrics
    match_score: Optional[float] = None
    
    @validator('current_status', pre=True, always=True)
    def set_current_status(cls, v, values):
        """Set current status based on the most recent event."""
        events = values.get('events', [])
        if events and not v:
            # Sort events by timestamp in descending order
            sorted_events = sorted(events, key=lambda x: x.timestamp, reverse=True)
            return sorted_events[0].status
        return v
