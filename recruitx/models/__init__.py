"""RecruitX models package."""

from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class MatchResult:
    """Match result data."""
    score: float
    confidence: str
    insights: Dict[str, Any]
    error: Optional[str] = None

class RecruitX:
    """Main RecruitX class."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize RecruitX.
        
        Args:
            config: Optional configuration
        """
        self.config = config or {}
        
    async def match_resume(
        self,
        resume_path: str,
        job_description_path: str
    ) -> MatchResult:
        """Match resume against job description.
        
        Args:
            resume_path: Path to resume file
            job_description_path: Path to job description
            
        Returns:
            Match result
        """
        # TODO: Implement matching logic
        return MatchResult(
            score=0.95,
            confidence="high",
            insights={}
        ) 