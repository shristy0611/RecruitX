"""Candidate Ranking Manager

This module provides an advanced candidate ranking system based on automated skill assessment results.
It leverages state-of-the-art practices including:
1. Multi-criteria ranking with weighted scores
2. Bias detection and mitigation
3. Gemini-powered ranking insights
4. Real-time performance tracking
5. Integration with feedback system

The design is inspired by patterns in the OpenManus-main repository.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from datetime import datetime
from google.generativeai.types import model_types

@dataclass
class RankingCriteria:
    """Criteria for ranking candidates."""
    technical_weight: float = 0.4
    soft_skills_weight: float = 0.2
    project_weight: float = 0.15
    experience_weight: float = 0.15
    education_weight: float = 0.1
    min_confidence: float = 0.7

@dataclass
class RankingResult:
    """Result of candidate ranking."""
    candidate_id: str
    overall_score: float
    confidence: float
    technical_score: float
    soft_skills_score: float
    project_score: float
    experience_score: float
    education_score: float
    strengths: List[str]
    areas_for_improvement: List[str]
    bias_indicators: List[Dict[str, Any]]
    ranking_insights: List[str]
    timestamp: datetime

class CandidateRankingManager:
    def __init__(
        self,
        results_dir: str,
        gemini_model: model_types.GenerativeModel,
        criteria: Optional[RankingCriteria] = None
    ):
        """Initialize the candidate ranking manager.
        
        Args:
            results_dir: Directory containing candidate assessment result JSON files
            gemini_model: Gemini model for generating insights
            criteria: Optional custom ranking criteria
        """
        self.results_dir = Path(results_dir)
        self.gemini = gemini_model
        self.criteria = criteria or RankingCriteria()
        self.candidates = self._load_candidates()
        self.ranking_cache = {}
        
    def _load_candidates(self) -> List[Dict[str, Any]]:
        """Load candidate assessment results from JSON files.
        
        Returns:
            List of candidate result dictionaries
        """
        candidates = []
        for file in self.results_dir.glob("*.json"):
            try:
                with open(file, "r") as f:
                    candidate = json.load(f)
                candidates.append(candidate)
            except Exception as e:
                print(f"Error loading {file}: {e}")
        return candidates
        
    async def rank_candidates(
        self,
        job_id: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[RankingResult]:
        """Rank candidates based on multiple criteria.
        
        Args:
            job_id: Optional job identifier to filter candidates
            min_score: Minimum overall score threshold
            
        Returns:
            List of ranking results sorted by overall score
        """
        # Filter candidates by job if specified
        candidates = [
            c for c in self.candidates
            if not job_id or c.get("job_id") == job_id
        ]
        
        # Calculate scores and check for biases
        ranking_results = []
        for candidate in candidates:
            # Calculate component scores
            technical_score = self._calculate_technical_score(candidate)
            soft_skills_score = self._calculate_soft_skills_score(candidate)
            project_score = self._calculate_project_score(candidate)
            experience_score = self._calculate_experience_score(candidate)
            education_score = self._calculate_education_score(candidate)
            
            # Calculate overall score with weights
            overall_score = (
                technical_score * self.criteria.technical_weight +
                soft_skills_score * self.criteria.soft_skills_weight +
                project_score * self.criteria.project_weight +
                experience_score * self.criteria.experience_weight +
                education_score * self.criteria.education_weight
            )
            
            # Skip if below minimum score
            if overall_score < min_score:
                continue
                
            # Check for potential biases
            bias_indicators = await self._detect_biases(candidate)
            
            # Generate ranking insights
            ranking_insights = await self._generate_insights(
                candidate,
                overall_score,
                {
                    "technical": technical_score,
                    "soft_skills": soft_skills_score,
                    "project": project_score,
                    "experience": experience_score,
                    "education": education_score
                }
            )
            
            # Create ranking result
            result = RankingResult(
                candidate_id=candidate["candidate_id"],
                overall_score=overall_score,
                confidence=candidate.get("confidence", 0.0),
                technical_score=technical_score,
                soft_skills_score=soft_skills_score,
                project_score=project_score,
                experience_score=experience_score,
                education_score=education_score,
                strengths=candidate.get("strengths", []),
                areas_for_improvement=candidate.get("areas_for_improvement", []),
                bias_indicators=bias_indicators,
                ranking_insights=ranking_insights,
                timestamp=datetime.now()
            )
            
            ranking_results.append(result)
            
        # Sort by overall score and confidence
        ranking_results.sort(
            key=lambda r: (r.overall_score, r.confidence),
            reverse=True
        )
        
        return ranking_results
        
    def _calculate_technical_score(self, candidate: Dict[str, Any]) -> float:
        """Calculate technical skills score.
        
        Args:
            candidate: Candidate data
            
        Returns:
            Technical score (0-1)
        """
        technical_skills = candidate.get("technical_skills", {})
        if not technical_skills:
            return 0.0
            
        # Calculate weighted average based on skill importance
        scores = []
        weights = []
        for skill, score in technical_skills.items():
            scores.append(score)
            weights.append(1.0 if skill in candidate.get("required_skills", []) else 0.5)
            
        return float(np.average(scores, weights=weights) if scores else 0.0)
        
    def _calculate_soft_skills_score(self, candidate: Dict[str, Any]) -> float:
        """Calculate soft skills score.
        
        Args:
            candidate: Candidate data
            
        Returns:
            Soft skills score (0-1)
        """
        soft_skills = candidate.get("soft_skills", {})
        if not soft_skills:
            return 0.0
            
        return float(np.mean(list(soft_skills.values())))
        
    def _calculate_project_score(self, candidate: Dict[str, Any]) -> float:
        """Calculate project experience score.
        
        Args:
            candidate: Candidate data
            
        Returns:
            Project score (0-1)
        """
        project_scores = candidate.get("project_scores", {})
        if not project_scores:
            return 0.0
            
        return float(np.mean(list(project_scores.values())))
        
    def _calculate_experience_score(self, candidate: Dict[str, Any]) -> float:
        """Calculate experience score.
        
        Args:
            candidate: Candidate data
            
        Returns:
            Experience score (0-1)
        """
        experience = candidate.get("experience_years", 0)
        required_experience = candidate.get("required_experience_years", 1)
        
        # Normalize experience score (cap at 2x required)
        return min(experience / required_experience, 2.0) / 2.0
        
    def _calculate_education_score(self, candidate: Dict[str, Any]) -> float:
        """Calculate education score.
        
        Args:
            candidate: Candidate data
            
        Returns:
            Education score (0-1)
        """
        education_level = candidate.get("education_level", 0)
        required_level = candidate.get("required_education_level", 1)
        
        # Normalize education score
        return min(education_level / required_level, 1.0)
        
    async def _detect_biases(self, candidate: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect potential biases in ranking.
        
        Args:
            candidate: Candidate data
            
        Returns:
            List of potential bias indicators
        """
        prompt = f"""Analyze this candidate data for potential ranking biases:

        {json.dumps(candidate, indent=2)}

        Consider:
        1. Overemphasis on specific skills/experience
        2. Demographic patterns
        3. Language bias
        4. Educational background bias

        Return as JSON array of:
        {{
            "type": "bias type",
            "description": "description",
            "severity": "high|medium|low",
            "mitigation": "suggested mitigation"
        }}
        """

        response = await self.gemini.generate_content(prompt)
        return response.json()
        
    async def _generate_insights(
        self,
        candidate: Dict[str, Any],
        overall_score: float,
        component_scores: Dict[str, float]
    ) -> List[str]:
        """Generate ranking insights using Gemini.
        
        Args:
            candidate: Candidate data
            overall_score: Overall ranking score
            component_scores: Individual component scores
            
        Returns:
            List of ranking insights
        """
        prompt = f"""Generate ranking insights for this candidate:

        Candidate Data:
        {json.dumps(candidate, indent=2)}

        Overall Score: {overall_score}
        Component Scores:
        {json.dumps(component_scores, indent=2)}

        Provide:
        1. Key strengths and differentiators
        2. Areas needing attention
        3. Fit for role analysis
        4. Development recommendations

        Return as JSON array of insight strings.
        """

        response = await self.gemini.generate_content(prompt)
        return response.json()
        
    def filter_candidates(
        self,
        min_score: float = 0.7,
        required_skills: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Filter candidates by criteria.
        
        Args:
            min_score: Minimum overall score required
            required_skills: Optional list of required skills
            
        Returns:
            Filtered list of candidates
        """
        filtered = [
            c for c in self.candidates
            if c.get("overall_score", 0) >= min_score
        ]
        
        if required_skills:
            filtered = [
                c for c in filtered
                if all(
                    skill in c.get("technical_skills", {})
                    for skill in required_skills
                )
            ]
            
        return filtered
        
    def save_ranking_results(
        self,
        results: List[RankingResult],
        output_file: str
    ):
        """Save ranking results to file.
        
        Args:
            results: List of ranking results
            output_file: Output file path
        """
        # Convert to dictionary format
        output = []
        for result in results:
            output.append({
                "candidate_id": result.candidate_id,
                "overall_score": result.overall_score,
                "confidence": result.confidence,
                "technical_score": result.technical_score,
                "soft_skills_score": result.soft_skills_score,
                "project_score": result.project_score,
                "experience_score": result.experience_score,
                "education_score": result.education_score,
                "strengths": result.strengths,
                "areas_for_improvement": result.areas_for_improvement,
                "bias_indicators": result.bias_indicators,
                "ranking_insights": result.ranking_insights,
                "timestamp": result.timestamp.isoformat()
            })
            
        # Save to file
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2) 