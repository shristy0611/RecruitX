"""
Screening Agent Explainer for RecruitPro AI.

This module provides detailed explanations for screening decisions,
leveraging LLM services to generate human-readable rationales.
"""
import json
import logging
from typing import Dict, Any, List, Optional

from src.xai.explanation_interface import ExplanationProvider, ExplanationFormat, LLMExplanationMixin
from src.llm import get_llm_service

# Configure logging
logger = logging.getLogger(__name__)

class ScreeningExplainer(ExplanationProvider, LLMExplanationMixin):
    """
    Explainer for the Screening Agent's decisions.
    
    This class provides detailed explanations for screening decisions,
    using LLM services to generate human-readable rationales while
    preserving the privacy-first architecture.
    """
    
    def __init__(self):
        """Initialize the Screening Explainer with LLM service."""
        self.llm_service = get_llm_service()
        
    def generate_explanation(self, 
                             context: Dict[str, Any],
                             detail_level: str = "standard") -> Dict[str, Any]:
        """
        Generate an explanation for a screening decision.
        
        Args:
            context: Dictionary containing all relevant context, including:
                - candidate_profile: Candidate details
                - job_description: Job details
                - screening_result: Screening scores and decision
            detail_level: Level of detail ("brief", "standard", "detailed")
            
        Returns:
            Dictionary containing the generated explanation and metadata
        """
        # Extract required information from context
        candidate_profile = context.get("candidate_profile", {})
        job_description = context.get("job_description", {})
        screening_result = context.get("screening_result", {})
        
        # Extract screening decision and scores
        decision = screening_result.get("decision", "unknown")
        overall_score = screening_result.get("overall_score", 0.0)
        criteria_scores = screening_result.get("criteria", {})
        
        # Generate the main explanation text
        explanation_text = self._generate_screening_explanation(
            candidate_profile=candidate_profile,
            job_description=job_description,
            decision=decision,
            overall_score=overall_score,
            criteria_scores=criteria_scores,
            detail_level=detail_level
        )
        
        # Generate key findings for detailed explanations
        key_findings = None
        if detail_level == "detailed":
            key_findings = self._generate_key_findings(
                candidate_profile=candidate_profile,
                job_description=job_description,
                screening_result=screening_result
            )
        
        # Return standardized explanation
        return ExplanationFormat.screening_explanation(
            decision=decision,
            score=overall_score,
            criteria=criteria_scores,
            explanation_text=explanation_text,
            key_findings=key_findings
        )
    
    def _generate_screening_explanation(
        self,
        candidate_profile: Dict[str, Any],
        job_description: Dict[str, Any],
        decision: str,
        overall_score: float,
        criteria_scores: Dict[str, float],
        detail_level: str
    ) -> str:
        """
        Generate the main screening explanation text.
        
        Args:
            candidate_profile: Candidate details
            job_description: Job details
            decision: Screening decision ("pass", "reject", "hold")
            overall_score: Overall screening score
            criteria_scores: Scores for individual criteria
            detail_level: Level of detail
            
        Returns:
            Explanation text
        """
        # Create a prompt for the LLM
        prompt = f"""
        I need to explain a screening decision for a candidate.
        
        Job Title: {job_description.get('title', 'Unknown Position')}
        Company: {job_description.get('company', 'Unknown Company')}
        
        Candidate: {candidate_profile.get('name', 'Unknown Candidate')}
        Resume Summary: {candidate_profile.get('summary', 'Not provided')}
        
        Screening Decision: {decision.upper()}
        Overall Score: {overall_score:.2f}
        
        Criteria Scores:
        {json.dumps(criteria_scores, indent=2)}
        
        Job Requirements:
        {job_description.get('requirements', 'Not specified')}
        """
        
        # Adjust system instruction based on detail level
        if detail_level == "brief":
            system_instruction = "Provide a brief, 2-3 sentence explanation of the screening decision."
        elif detail_level == "standard":
            system_instruction = "Provide a clear, paragraph-length explanation of the screening decision, highlighting the key factors that led to this decision."
        else:  # detailed
            system_instruction = "Provide a comprehensive explanation of the screening decision, with specific examples from the candidate's profile and how they align or don't align with the job requirements."
        
        # Generate explanation using LLM
        try:
            explanation = self.generate_llm_explanation(
                prompt=prompt,
                system_instructions=system_instruction,
                temperature=0.3
            )
            return explanation
        except Exception as e:
            logger.error(f"Error generating screening explanation: {e}")
            # Fallback to a template-based explanation if LLM fails
            return self._fallback_screening_explanation(
                candidate_profile, 
                job_description, 
                decision,
                overall_score,
                criteria_scores
            )
    
    def _generate_key_findings(
        self,
        candidate_profile: Dict[str, Any],
        job_description: Dict[str, Any],
        screening_result: Dict[str, Any]
    ) -> List[str]:
        """
        Generate key findings from the screening process.
        
        Args:
            candidate_profile: Candidate details
            job_description: Job details
            screening_result: Screening scores and decision
            
        Returns:
            List of key findings
        """
        # Create prompt for key findings
        prompt = f"""
        Based on the candidate profile and job requirements, identify the key findings from the screening process:
        
        Job Title: {job_description.get('title', 'Unknown Position')}
        Requirements: {job_description.get('requirements', 'Not specified')}
        
        Candidate: {candidate_profile.get('name', 'Unknown Candidate')}
        Experience: {candidate_profile.get('experience', 'Not specified')}
        Skills: {candidate_profile.get('skills', 'Not specified')}
        Education: {candidate_profile.get('education', 'Not specified')}
        
        Screening Results:
        Decision: {screening_result.get('decision', 'unknown').upper()}
        Overall Score: {screening_result.get('overall_score', 0.0):.2f}
        Criteria Scores: {json.dumps(screening_result.get('criteria', {}), indent=2)}
        """
        
        system_instruction = """
        Generate a bulleted list of 4-6 key findings from the screening process.
        Each finding should highlight a specific strength or weakness in relation to the job requirements.
        Format your response as a single JSON array of strings, like:
        ["Finding 1", "Finding 2", "Finding 3", "Finding 4"]
        """
        
        try:
            response = self.generate_llm_explanation(
                prompt=prompt,
                system_instructions=system_instruction,
                temperature=0.3
            )
            
            # Parse the response as JSON
            try:
                findings = json.loads(response)
                if isinstance(findings, list):
                    return findings
            except json.JSONDecodeError:
                # If not valid JSON, try to extract list items
                findings = []
                for line in response.strip().split('\n'):
                    if line.strip().startswith('- ') or line.strip().startswith('* '):
                        findings.append(line.strip()[2:])
                if findings:
                    return findings
            
            # Default fallback if parsing fails
            logger.warning("Failed to parse key findings response, using default")
            if screening_result.get('decision') == 'pass':
                return [
                    "Candidate meets the minimum requirements for the position",
                    "Skills align with job requirements",
                    "Has relevant experience in the field"
                ]
            else:
                return [
                    "Candidate does not meet all minimum requirements",
                    "Missing critical skills required for the position",
                    "Insufficient relevant experience"
                ]
                
        except Exception as e:
            logger.error(f"Error generating key findings: {e}")
            # Return default findings based on decision
            if screening_result.get('decision') == 'pass':
                return [
                    "Candidate meets the minimum requirements for the position",
                    "Skills align with job requirements",
                    "Has relevant experience in the field"
                ]
            else:
                return [
                    "Candidate does not meet all minimum requirements",
                    "Missing critical skills required for the position",
                    "Insufficient relevant experience"
                ]
    
    def _fallback_screening_explanation(
        self,
        candidate_profile: Dict[str, Any],
        job_description: Dict[str, Any],
        decision: str,
        overall_score: float,
        criteria_scores: Dict[str, float]
    ) -> str:
        """
        Generate a fallback explanation without using LLM services.
        
        Args:
            candidate_profile: Candidate details
            job_description: Job details
            decision: Screening decision
            overall_score: Overall screening score
            criteria_scores: Scores for individual criteria
            
        Returns:
            Fallback explanation text
        """
        job_title = job_description.get("title", "the position")
        candidate_name = candidate_profile.get("name", "The candidate")
        
        if decision.lower() == "pass":
            return f"{candidate_name} passed the screening for {job_title} with a score of {overall_score:.2f}. The candidate meets the minimum requirements for this position based on the screening criteria."
        elif decision.lower() == "hold":
            return f"{candidate_name} is on hold for {job_title} with a score of {overall_score:.2f}. The candidate meets some requirements but further assessment is needed before making a final decision."
        else:  # reject
            return f"{candidate_name} did not pass the screening for {job_title} with a score of {overall_score:.2f}. The candidate does not meet the minimum requirements for this position based on the screening criteria."
