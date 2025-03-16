"""Automated skill assessment manager."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import numpy as np
import pandas as pd

from ml_models.model_manager import ModelManager
from google.generativeai.types import model_types

logger = logging.getLogger(__name__)

@dataclass
class SkillAssessmentResult:
    """Result of skill assessment."""
    candidate_id: str
    job_id: str
    timestamp: datetime
    technical_skills: Dict[str, float]  # Skill -> Score
    soft_skills: Dict[str, float]
    project_scores: Dict[str, float]
    certifications: List[Dict[str, Any]]
    gaps: List[Dict[str, Any]]
    recommendations: List[str]
    overall_score: float
    confidence: float

class AssessmentManager:
    """Manages automated skill assessment."""
    
    def __init__(
        self,
        model_manager: ModelManager,
        gemini_model: model_types.GenerativeModel,
        output_dir: Union[str, Path],
        min_confidence: float = 0.7,
        cache_dir: Optional[Union[str, Path]] = None
    ):
        """Initialize manager.
        
        Args:
            model_manager: ML model manager
            gemini_model: Gemini model for assessment
            output_dir: Directory for assessment outputs
            min_confidence: Minimum confidence threshold
            cache_dir: Cache directory
        """
        self.model_manager = model_manager
        self.gemini = gemini_model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.min_confidence = min_confidence
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
    async def assess_candidate(
        self,
        candidate_id: str,
        job_id: str,
        resume_text: str,
        job_description: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> SkillAssessmentResult:
        """Assess candidate skills for job.
        
        Args:
            candidate_id: Candidate identifier
            job_id: Job identifier
            resume_text: Resume text
            job_description: Job description text
            additional_data: Optional additional data
            
        Returns:
            Assessment result
        """
        # Extract required skills from job description
        required_skills = await self._extract_required_skills(job_description)
        
        # Assess technical skills
        technical_scores = await self._assess_technical_skills(
            resume_text,
            required_skills["technical"]
        )
        
        # Assess soft skills
        soft_scores = await self._assess_soft_skills(
            resume_text,
            required_skills["soft"]
        )
        
        # Evaluate projects
        project_scores = await self._evaluate_projects(resume_text)
        
        # Validate certifications
        certifications = await self._validate_certifications(resume_text)
        
        # Analyze skill gaps
        gaps = await self._analyze_skill_gaps(
            technical_scores,
            soft_scores,
            required_skills
        )
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            technical_scores,
            soft_scores,
            gaps,
            job_description
        )
        
        # Calculate overall score
        overall_score, confidence = await self._calculate_overall_score(
            technical_scores,
            soft_scores,
            project_scores,
            required_skills
        )
        
        # Create result
        result = SkillAssessmentResult(
            candidate_id=candidate_id,
            job_id=job_id,
            timestamp=datetime.now(),
            technical_skills=technical_scores,
            soft_skills=soft_scores,
            project_scores=project_scores,
            certifications=certifications,
            gaps=gaps,
            recommendations=recommendations,
            overall_score=overall_score,
            confidence=confidence
        )
        
        # Save result
        self._save_result(result)
        
        return result
        
    async def _extract_required_skills(
        self,
        job_description: str
    ) -> Dict[str, List[str]]:
        """Extract required skills from job description.
        
        Args:
            job_description: Job description text
            
        Returns:
            Dictionary of required skills
        """
        prompt = f"""Analyze this job description and extract required skills:
        
        {job_description}
        
        Return a JSON object with:
        {{
            "technical": [
                {{
                    "skill": "skill name",
                    "level": "required level (0-1)",
                    "importance": "high|medium|low"
                }}
            ],
            "soft": [
                {{
                    "skill": "skill name",
                    "importance": "high|medium|low"
                }}
            ]
        }}
        """
        
        response = await self.model_manager._retry_gemini_call(
            lambda: self.gemini.generate_content(prompt)
        )
        
        return response.json()
        
    async def _assess_technical_skills(
        self,
        resume_text: str,
        required_skills: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Assess technical skills from resume.
        
        Args:
            resume_text: Resume text
            required_skills: Required technical skills
            
        Returns:
            Dictionary of skill scores
        """
        scores = {}
        
        for skill in required_skills:
            # Get skill classifier
            model_id = await self.model_manager.create_skill_classifier(
                training_data=[{"text": resume_text, "skill": skill["skill"]}]
            )
            
            # Make prediction
            prediction, confidence = await self.model_manager.predict(
                model_id,
                {"description": resume_text}
            )
            
            if confidence >= self.min_confidence:
                scores[skill["skill"]] = float(prediction)
                
        # Enhance with Gemini analysis
        prompt = f"""Analyze the technical skills in this resume:
        
        {resume_text}
        
        Required skills:
        {json.dumps(required_skills, indent=2)}
        
        Initial ML scores:
        {json.dumps(scores, indent=2)}
        
        Return an enhanced JSON object with:
        {{
            "skill_name": {{
                "score": float,  // 0.0 to 1.0
                "evidence": "supporting text from resume",
                "confidence": float  // 0.0 to 1.0
            }}
        }}
        """
        
        response = await self.model_manager._retry_gemini_call(
            lambda: self.gemini.generate_content(prompt)
        )
        
        enhanced_scores = response.json()
        
        # Combine ML and Gemini scores
        final_scores = {}
        for skill, details in enhanced_scores.items():
            if details["confidence"] >= self.min_confidence:
                final_scores[skill] = details["score"]
                
        return final_scores
        
    async def _assess_soft_skills(
        self,
        resume_text: str,
        required_skills: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Assess soft skills from resume.
        
        Args:
            resume_text: Resume text
            required_skills: Required soft skills
            
        Returns:
            Dictionary of skill scores
        """
        prompt = f"""Analyze the soft skills demonstrated in this resume:
        
        {resume_text}
        
        Required skills:
        {json.dumps(required_skills, indent=2)}
        
        For each skill, analyze:
        1. Evidence in achievements and responsibilities
        2. Language and communication style
        3. Project collaboration indicators
        4. Leadership and initiative examples
        
        Return a JSON object with:
        {{
            "skill_name": {{
                "score": float,  // 0.0 to 1.0
                "evidence": [
                    "supporting examples from resume"
                ],
                "confidence": float  // 0.0 to 1.0
            }}
        }}
        """
        
        response = await self.model_manager._retry_gemini_call(
            lambda: self.gemini.generate_content(prompt)
        )
        
        results = response.json()
        
        # Filter by confidence
        scores = {
            skill: details["score"]
            for skill, details in results.items()
            if details["confidence"] >= self.min_confidence
        }
        
        return scores
        
    async def _evaluate_projects(
        self,
        resume_text: str
    ) -> Dict[str, float]:
        """Evaluate projects from resume.
        
        Args:
            resume_text: Resume text
            
        Returns:
            Dictionary of project scores
        """
        prompt = f"""Analyze the projects mentioned in this resume:
        
        {resume_text}
        
        For each project, evaluate:
        1. Technical complexity
        2. Scale and impact
        3. Role and responsibilities
        4. Technologies used
        5. Measurable outcomes
        
        Return a JSON object with:
        {{
            "project_name": {{
                "complexity_score": float,  // 0.0 to 1.0
                "impact_score": float,  // 0.0 to 1.0
                "role_score": float,  // 0.0 to 1.0
                "tech_score": float,  // 0.0 to 1.0
                "outcome_score": float,  // 0.0 to 1.0
                "overall_score": float,  // 0.0 to 1.0
                "confidence": float  // 0.0 to 1.0
            }}
        }}
        """
        
        response = await self.model_manager._retry_gemini_call(
            lambda: self.gemini.generate_content(prompt)
        )
        
        results = response.json()
        
        # Filter by confidence and get overall scores
        scores = {
            project: details["overall_score"]
            for project, details in results.items()
            if details["confidence"] >= self.min_confidence
        }
        
        return scores
        
    async def _validate_certifications(
        self,
        resume_text: str
    ) -> List[Dict[str, Any]]:
        """Validate certifications from resume.
        
        Args:
            resume_text: Resume text
            
        Returns:
            List of validated certifications
        """
        prompt = f"""Extract and validate certifications from this resume:
        
        {resume_text}
        
        For each certification, analyze:
        1. Name and issuing organization
        2. Validity period
        3. Relevance to technical skills
        4. Industry recognition
        
        Return a JSON array with:
        [
            {{
                "name": "certification name",
                "issuer": "organization",
                "valid_until": "YYYY-MM-DD or null",
                "relevance_score": float,  // 0.0 to 1.0
                "recognition_score": float,  // 0.0 to 1.0
                "confidence": float  // 0.0 to 1.0
            }}
        ]
        """
        
        response = await self.model_manager._retry_gemini_call(
            lambda: self.gemini.generate_content(prompt)
        )
        
        certifications = response.json()
        
        # Filter by confidence
        return [
            cert for cert in certifications
            if cert["confidence"] >= self.min_confidence
        ]
        
    async def _analyze_skill_gaps(
        self,
        technical_scores: Dict[str, float],
        soft_scores: Dict[str, float],
        required_skills: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Analyze skill gaps.
        
        Args:
            technical_scores: Technical skill scores
            soft_scores: Soft skill scores
            required_skills: Required skills
            
        Returns:
            List of skill gaps
        """
        gaps = []
        
        # Analyze technical gaps
        for skill in required_skills["technical"]:
            name = skill["skill"]
            if name not in technical_scores:
                gaps.append({
                    "type": "technical",
                    "skill": name,
                    "importance": skill["importance"],
                    "required_level": float(skill["level"]),
                    "current_level": 0.0,
                    "gap_size": float(skill["level"])
                })
            elif technical_scores[name] < float(skill["level"]):
                gaps.append({
                    "type": "technical",
                    "skill": name,
                    "importance": skill["importance"],
                    "required_level": float(skill["level"]),
                    "current_level": technical_scores[name],
                    "gap_size": float(skill["level"]) - technical_scores[name]
                })
                
        # Analyze soft skill gaps
        for skill in required_skills["soft"]:
            name = skill["skill"]
            if name not in soft_scores:
                gaps.append({
                    "type": "soft",
                    "skill": name,
                    "importance": skill["importance"],
                    "current_level": 0.0
                })
                
        return gaps
        
    async def _generate_recommendations(
        self,
        technical_scores: Dict[str, float],
        soft_scores: Dict[str, float],
        gaps: List[Dict[str, Any]],
        job_description: str
    ) -> List[str]:
        """Generate improvement recommendations.
        
        Args:
            technical_scores: Technical skill scores
            soft_scores: Soft skill scores
            gaps: Identified skill gaps
            job_description: Job description text
            
        Returns:
            List of recommendations
        """
        prompt = f"""Generate specific recommendations based on skill assessment:
        
        Job Description:
        {job_description}
        
        Technical Scores:
        {json.dumps(technical_scores, indent=2)}
        
        Soft Skill Scores:
        {json.dumps(soft_scores, indent=2)}
        
        Skill Gaps:
        {json.dumps(gaps, indent=2)}
        
        Provide actionable recommendations for:
        1. Addressing skill gaps
        2. Enhancing existing skills
        3. Professional development
        4. Project experience
        5. Certifications
        
        Return a JSON array of specific, actionable recommendations.
        """
        
        response = await self.model_manager._retry_gemini_call(
            lambda: self.gemini.generate_content(prompt)
        )
        
        return response.json()
        
    async def _calculate_overall_score(
        self,
        technical_scores: Dict[str, float],
        soft_scores: Dict[str, float],
        project_scores: Dict[str, float],
        required_skills: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[float, float]:
        """Calculate overall assessment score.
        
        Args:
            technical_scores: Technical skill scores
            soft_scores: Soft skill scores
            project_scores: Project evaluation scores
            required_skills: Required skills
            
        Returns:
            Tuple of (overall_score, confidence)
        """
        # Calculate technical score
        tech_weights = {
            s["skill"]: 1.0 if s["importance"] == "high" else 0.5
            for s in required_skills["technical"]
        }
        tech_scores = []
        tech_weights_used = []
        
        for skill, score in technical_scores.items():
            if skill in tech_weights:
                tech_scores.append(score)
                tech_weights_used.append(tech_weights[skill])
                
        technical_score = (
            np.average(tech_scores, weights=tech_weights_used)
            if tech_scores else 0.0
        )
        
        # Calculate soft skills score
        soft_weights = {
            s["skill"]: 1.0 if s["importance"] == "high" else 0.5
            for s in required_skills["soft"]
        }
        soft_scores_list = []
        soft_weights_used = []
        
        for skill, score in soft_scores.items():
            if skill in soft_weights:
                soft_scores_list.append(score)
                soft_weights_used.append(soft_weights[skill])
                
        soft_score = (
            np.average(soft_scores_list, weights=soft_weights_used)
            if soft_scores_list else 0.0
        )
        
        # Calculate project score
        project_score = np.mean(list(project_scores.values())) if project_scores else 0.0
        
        # Combine scores
        weights = [0.5, 0.3, 0.2]  # Technical, Soft, Projects
        overall_score = np.average(
            [technical_score, soft_score, project_score],
            weights=weights
        )
        
        # Calculate confidence
        tech_coverage = len(tech_scores) / len(required_skills["technical"])
        soft_coverage = len(soft_scores_list) / len(required_skills["soft"])
        confidence = np.average([tech_coverage, soft_coverage])
        
        return float(overall_score), float(confidence)
        
    def _save_result(self, result: SkillAssessmentResult):
        """Save assessment result.
        
        Args:
            result: Assessment result
        """
        # Create output file
        output_file = self.output_dir / f"{result.candidate_id}_{result.job_id}.json"
        
        # Convert to dictionary
        result_dict = {
            "candidate_id": result.candidate_id,
            "job_id": result.job_id,
            "timestamp": result.timestamp.isoformat(),
            "technical_skills": result.technical_skills,
            "soft_skills": result.soft_skills,
            "project_scores": result.project_scores,
            "certifications": result.certifications,
            "gaps": result.gaps,
            "recommendations": result.recommendations,
            "overall_score": result.overall_score,
            "confidence": result.confidence
        }
        
        # Save to file
        with open(output_file, "w") as f:
            json.dump(result_dict, f, indent=2) 