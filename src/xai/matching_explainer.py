"""
Matching Agent Explainer for RecruitPro AI.

This module provides detailed explanations for matching decisions,
leveraging LLM services to generate human-readable rationales.
"""
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from src.xai.explanation_interface import ExplanationProvider, ExplanationFormat, LLMExplanationMixin
from src.llm import get_llm_service

# Configure logging
logger = logging.getLogger(__name__)

class MatchingExplainer(ExplanationProvider, LLMExplanationMixin):
    """
    Explainer for the Matching Agent's decisions.
    
    This class provides detailed explanations for why candidates match 
    certain job requirements, using LLM services to generate human-readable
    rationales while preserving the privacy-first architecture.
    """
    
    def __init__(self):
        """Initialize the Matching Explainer with LLM service."""
        self.llm_service = get_llm_service()
        
    def generate_explanation(self, 
                             context: Dict[str, Any],
                             detail_level: str = "standard") -> Dict[str, Any]:
        """
        Generate an explanation for a matching decision.
        
        Args:
            context: Dictionary containing all relevant context, including:
                - candidate_profile: Candidate details
                - job_description: Job details
                - match_result: Match scores and factors
            detail_level: Level of detail ("brief", "standard", "detailed")
            
        Returns:
            Dictionary containing the generated explanation and metadata
        """
        # Extract required information from context
        candidate_profile = context.get("candidate_profile", {})
        job_description = context.get("job_description", {})
        match_result = context.get("match_result", {})
        
        # Get overall match score
        overall_score = match_result.get("overall_score", 0.0)
        
        # Get factor scores
        factors = match_result.get("factors", {})
        
        # Generate main explanation text
        explanation_text = self._generate_overall_explanation(
            candidate_profile, 
            job_description, 
            match_result,
            detail_level
        )
        
        # For detailed explanations, generate factor-specific explanations
        factor_explanations = None
        strengths = None
        improvement_areas = None
        
        if detail_level in ["standard", "detailed"]:
            factor_explanations = self._generate_factor_explanations(
                candidate_profile,
                job_description,
                factors,
                detail_level
            )
            
        if detail_level == "detailed":
            strengths, improvement_areas = self._generate_strengths_and_improvements(
                candidate_profile,
                job_description,
                match_result
            )
        
        # Return standardized explanation
        return ExplanationFormat.matching_explanation(
            score=overall_score,
            factors=factors,
            explanation_text=explanation_text,
            factor_explanations=factor_explanations,
            strengths=strengths,
            improvement_areas=improvement_areas
        )
    
    def _generate_overall_explanation(
        self,
        candidate_profile: Dict[str, Any],
        job_description: Dict[str, Any],
        match_result: Dict[str, Any],
        detail_level: str
    ) -> str:
        """
        Generate the overall explanation text.
        
        Args:
            candidate_profile: Candidate details
            job_description: Job details
            match_result: Match scores and factors
            detail_level: Level of detail
            
        Returns:
            Overall explanation text
        """
        # Create a prompt for the LLM
        prompt = f"""
        [SYSTEM INSTRUCTION] Provide a {detail_level} explanation of why a candidate matches a job with a score of {match_result.get('overall_score', 0.0)}.
        
        Job Title: {job_description.get('title', 'Unknown Position')}
        Company: {job_description.get('company', 'Unknown Company')}
        
        Candidate: {candidate_profile.get('name', 'Unknown Candidate')}
        Candidate Experience: {candidate_profile.get('experience', 'Not specified')}
        
        Match Scores:
        Overall: {match_result.get('overall_score', 0.0):.2f}
        Skills: {match_result.get('factors', {}).get('skills_score', 0.0):.2f}
        Experience: {match_result.get('factors', {}).get('experience_score', 0.0):.2f}
        Education: {match_result.get('factors', {}).get('education_score', 0.0):.2f}
        
        Key Skills Match: {match_result.get('matched_skills', [])}
        Missing Skills: {match_result.get('missing_skills', [])}
        """
        
        # Adjust system instruction based on detail level
        if detail_level == "brief":
            system_instruction = "Provide a brief, 2-3 sentence explanation of why this candidate matches the job position."
        elif detail_level == "standard":
            system_instruction = "Provide a clear, paragraph-length explanation of why this candidate matches the job position, highlighting the key factors."
        else:  # detailed
            system_instruction = "Provide a comprehensive explanation of why this candidate matches the job position, with specific examples and details about their qualifications."
        
        # Generate explanation using LLM
        try:
            explanation = self.generate_llm_explanation(
                prompt=prompt,
                system_instructions=system_instruction,
                temperature=0.3
            )
            return explanation
        except Exception as e:
            logger.error(f"Error generating overall explanation: {e}")
            # Fallback to a template-based explanation if LLM fails
            return self._fallback_overall_explanation(
                candidate_profile, 
                job_description, 
                match_result
            )
    
    def _generate_factor_explanations(
        self,
        candidate_profile: Dict[str, Any],
        job_description: Dict[str, Any],
        factors: Dict[str, Any],
        detail_level: str
    ) -> Dict[str, str]:
        """
        Generate explanations for individual matching factors.
        
        Args:
            candidate_profile: Candidate details
            job_description: Job details
            factors: Factor scores
            detail_level: Level of detail
            
        Returns:
            Dictionary of factor explanations
        """
        factor_explanations = {}
        
        # Define factors to explain
        factors_to_explain = [
            ("skills_score", "Skills Match"), 
            ("experience_score", "Experience Match"), 
            ("education_score", "Education Match")
        ]
        
        for factor_key, factor_name in factors_to_explain:
            if factor_key in factors:
                factor_score = factors[factor_key]
                
                # Create a factor-specific prompt
                prompt = f"""
                Explain why the candidate's {factor_name.lower()} received a score of {factor_score:.2f} out of 1.0.
                
                Job Details:
                Title: {job_description.get('title', 'Unknown Position')}
                Required {factor_name}: {job_description.get(factor_key.replace('_score', '_requirements'), 'Not specified')}
                
                Candidate Details:
                Name: {candidate_profile.get('name', 'Unknown Candidate')}
                {factor_name}: {candidate_profile.get(factor_key.replace('_score', ''), 'Not specified')}
                """
                
                # Generate explanation for this factor
                try:
                    explanation = self.generate_llm_explanation(
                        prompt=prompt,
                        system_instructions=f"Provide a {detail_level} explanation for the {factor_name.lower()} score.",
                        temperature=0.3,
                        max_tokens=512
                    )
                    factor_explanations[factor_key] = explanation
                except Exception as e:
                    logger.error(f"Error generating explanation for {factor_key}: {e}")
                    factor_explanations[factor_key] = f"{factor_name} scored {factor_score:.2f} based on alignment with job requirements."
        
        return factor_explanations
    
    def _generate_strengths_and_improvements(
        self,
        candidate_profile: Dict[str, Any],
        job_description: Dict[str, Any],
        match_result: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """
        Generate strengths and improvement areas for the candidate.
        
        Args:
            candidate_profile: Candidate details
            job_description: Job details
            match_result: Match scores and factors
            
        Returns:
            Tuple of (strengths, improvement_areas)
        """
        # Create prompt for strengths and improvements
        prompt = f"""
        Based on the job requirements and candidate profile, identify:
        1. The candidate's top strengths for this position
        2. Areas where the candidate could improve to better match the job
        
        Job Title: {job_description.get('title', 'Unknown Position')}
        Required Skills: {job_description.get('skills_requirements', [])}
        Required Experience: {job_description.get('experience_requirements', 'Not specified')}
        
        Candidate Skills: {candidate_profile.get('skills', [])}
        Candidate Experience: {candidate_profile.get('experience', 'Not specified')}
        
        Match Scores:
        Overall: {match_result.get('overall_score', 0.0):.2f}
        Skills: {match_result.get('factors', {}).get('skills_score', 0.0):.2f}
        Experience: {match_result.get('factors', {}).get('experience_score', 0.0):.2f}
        Education: {match_result.get('factors', {}).get('education_score', 0.0):.2f}
        
        Matched Skills: {match_result.get('matched_skills', [])}
        Missing Skills: {match_result.get('missing_skills', [])}
        """
        
        system_instruction = """
        Provide a JSON response with two arrays:
        1. "strengths": List of 3-5 specific strengths the candidate has for this job
        2. "improvements": List of 2-4 specific areas where the candidate could improve
        
        Format your response as valid JSON like:
        {
            "strengths": ["Strength 1", "Strength 2", ...],
            "improvements": ["Improvement 1", "Improvement 2", ...]
        }
        """
        
        try:
            response = self.generate_llm_explanation(
                prompt=prompt,
                system_instructions=system_instruction,
                temperature=0.3
            )
            
            # Parse the response as JSON
            try:
                result = json.loads(response)
                strengths = result.get("strengths", [])
                improvements = result.get("improvements", [])
                return strengths, improvements
            except json.JSONDecodeError:
                # Fallback if response is not valid JSON
                logger.error("Invalid JSON response from LLM for strengths/improvements")
                lines = response.strip().split('\n')
                strengths = [line.strip('- ') for line in lines if line.lower().startswith(('- strength', '* strength'))]
                improvements = [line.strip('- ') for line in lines if line.lower().startswith(('- improvement', '* improvement'))]
                return strengths[:5], improvements[:4]
                
        except Exception as e:
            logger.error(f"Error generating strengths and improvements: {e}")
            # Fallback to basic strengths/improvements
            strengths = ["Matches core job requirements", "Has relevant experience"]
            improvements = ["Could develop additional skills in missing areas"]
            return strengths, improvements
    
    def _fallback_overall_explanation(
        self,
        candidate_profile: Dict[str, Any],
        job_description: Dict[str, Any],
        match_result: Dict[str, Any]
    ) -> str:
        """
        Generate a fallback explanation without using LLM services.
        
        Args:
            candidate_profile: Candidate details
            job_description: Job details
            match_result: Match scores and factors
            
        Returns:
            Fallback explanation text
        """
        score = match_result.get('overall_score', 0.0)
        candidate_name = candidate_profile.get('name', 'The candidate')
        job_title = job_description.get('title', 'the position')
        
        if score >= 0.8:
            return f"{candidate_name} is an excellent match for {job_title} with a strong score of {score:.2f}. Their skills and experience align well with the requirements."
        elif score >= 0.6:
            return f"{candidate_name} is a good match for {job_title} with a score of {score:.2f}. They meet many of the key requirements but may need some additional training in certain areas."
        elif score >= 0.4:
            return f"{candidate_name} is a moderate match for {job_title} with a score of {score:.2f}. While they have some relevant qualifications, there are several areas that may require further development."
        else:
            return f"{candidate_name} is not a strong match for {job_title} with a score of {score:.2f}. Their current qualifications do not align closely with the job requirements."
