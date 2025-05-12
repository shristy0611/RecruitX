"""
API data models for RecruitPro AI.

These Pydantic models define the structure of API requests and responses
for interacting with the RecruitPro AI system.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field, EmailStr, HttpUrl, validator


class JobDescriptionCreate(BaseModel):
    """Request model for creating a job description."""
    
    title: str = Field(..., description="Job title", min_length=3, max_length=100)
    description: str = Field(..., description="Detailed job description", min_length=20)
    requirements: str = Field(..., description="Job requirements", min_length=20)
    company: str = Field(..., description="Company name", min_length=2, max_length=100)
    location: Optional[str] = Field(None, description="Job location")
    salary_range: Optional[str] = Field(None, description="Salary range as text")
    job_type: Optional[str] = Field("Full-time", description="Job type (Full-time, Part-time, etc.)")


class JobDescriptionResponse(BaseModel):
    """Response model for job description data."""
    
    id: str = Field(..., description="Job UUID")
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Detailed job description")
    requirements: str = Field(..., description="Job requirements")
    company: str = Field(..., description="Company name")
    location: Optional[str] = Field(None, description="Job location")
    salary_range: Optional[str] = Field(None, description="Salary range as text")
    job_type: Optional[str] = Field(None, description="Job type (Full-time, Part-time, etc.)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ResumeUpload(BaseModel):
    """Request model for resume upload metadata."""
    
    job_id: str = Field(..., description="Job ID to match against")
    candidate_name: Optional[str] = Field(None, description="Candidate name (if known)")
    candidate_email: Optional[EmailStr] = Field(None, description="Candidate email (if known)")


class Skill(BaseModel):
    """Model for a candidate skill."""
    
    name: str = Field(..., description="Skill name")
    level: Optional[str] = Field(None, description="Skill level (if available)")


class ResumeData(BaseModel):
    """Model for structured resume data."""
    
    contact_info: Dict[str, str] = Field(..., description="Contact information")
    name: str = Field(..., description="Candidate name")
    skills: List[str] = Field(..., description="List of skills")
    education: List[str] = Field(..., description="Education entities")
    sections: Dict[str, str] = Field(..., description="Resume sections")


class ScoreData(BaseModel):
    """Model for candidate scoring data."""
    
    overall_score: float = Field(..., description="Overall match score (0-100)")
    skills_score: float = Field(..., description="Skills match score (0-100)")
    experience_score: float = Field(..., description="Experience match score (0-100)")
    education_score: float = Field(..., description="Education match score (0-100)")
    final_score: float = Field(..., description="Final weighted score (0-100)")
    explanation: str = Field(..., description="Score explanation")
    timestamp: str = Field(..., description="Scoring timestamp")


class ResumeAnalysisResponse(BaseModel):
    """Response model for resume analysis."""
    
    resume_data: ResumeData = Field(..., description="Structured resume data")
    job_data: Dict[str, Any] = Field(..., description="Job data")
    score_data: ScoreData = Field(..., description="Score data")


class ErrorResponse(BaseModel):
    """Model for API error responses."""
    
    detail: str = Field(..., description="Error detail")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    path: Optional[str] = Field(None, description="Request path")


class HealthCheck(BaseModel):
    """Response model for API health check."""
    
    status: str = Field("ok", description="API status")
    version: str = Field("0.1.0", description="API version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    components: Dict[str, str] = Field(..., description="Component statuses")


class CandidateMatchResponse(BaseModel):
    """Response model for candidate job matching."""
    
    candidate_id: str = Field(..., description="Candidate ID")
    matches: List[Dict[str, Any]] = Field(..., description="Job matches with scores")


class ExplanationResponse(BaseModel):
    """Response model for explainable AI (XAI) explanations."""
    
    agent_type: str = Field(..., description="Type of agent providing the explanation (matching, sourcing, screening)")
    detail_level: str = Field(..., description="Level of detail in the explanation (brief, standard, detailed)")
    job_id: str = Field(..., description="Job UUID")
    candidate_id: str = Field("", description="Candidate UUID, may be empty for sourcing operations")
    explanation: str = Field(..., description="Human-readable explanation text")
    score: float = Field(0.0, description="Overall score if applicable")
    factors: Dict[str, float] = Field({}, description="Factor scores that contributed to the overall score")
    metadata: Dict[str, Any] = Field({}, description="Additional explanation metadata")
    
    @validator('agent_type')
    def validate_agent_type(cls, v):
        """Validate that agent_type is one of the supported types."""
        valid_types = ["matching", "sourcing", "screening"]
        if v not in valid_types:
            raise ValueError(f"agent_type must be one of {valid_types}")
        return v
    
    @validator('detail_level')
    def validate_detail_level(cls, v):
        """Validate that detail_level is one of the supported levels."""
        valid_levels = ["brief", "standard", "detailed"]
        if v not in valid_levels:
            raise ValueError(f"detail_level must be one of {valid_levels}")
        return v
