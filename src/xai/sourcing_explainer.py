"""
Sourcing Agent Explainer for RecruitPro AI.

This module provides detailed explanations for sourcing decisions,
leveraging LLM services to generate human-readable rationales.
"""
import json
import logging
from typing import Dict, Any, List, Optional

from src.xai.explanation_interface import ExplanationProvider, ExplanationFormat, LLMExplanationMixin
from src.llm import get_llm_service

# Configure logging
logger = logging.getLogger(__name__)

class SourcingExplainer(ExplanationProvider, LLMExplanationMixin):
    """
    Explainer for the Sourcing Agent's decisions.
    
    This class provides detailed explanations for why candidates were sourced
    for specific job requirements, using LLM services to generate human-readable
    rationales while preserving the privacy-first architecture.
    """
    
    def __init__(self):
        """Initialize the Sourcing Explainer with LLM service."""
        self.llm_service = get_llm_service()
        
    def generate_explanation(self, 
                             context: Dict[str, Any],
                             detail_level: str = "standard") -> Dict[str, Any]:
        """
        Generate an explanation for a sourcing decision.
        
        Args:
            context: Dictionary containing all relevant context, including:
                - job_description: Job details
                - sourcing_query: Original sourcing query
                - candidates: List of sourced candidates
                - search_strategy: Strategy used for sourcing
                - filters: Filters applied during sourcing
            detail_level: Level of detail ("brief", "standard", "detailed")
            
        Returns:
            Dictionary containing the generated explanation and metadata
        """
        # Extract required information from context
        job_description = context.get("job_description", {})
        sourcing_query = context.get("sourcing_query", {})
        candidates = context.get("candidates", [])
        search_strategy = context.get("search_strategy", "semantic search")
        filters = context.get("filters", {})
        
        # Generate the main explanation text
        explanation_text = self._generate_sourcing_explanation(
            job_description=job_description,
            sourcing_query=sourcing_query,
            candidates=candidates,
            search_strategy=search_strategy,
            filters=filters,
            detail_level=detail_level
        )
        
        # Return standardized explanation
        return ExplanationFormat.sourcing_explanation(
            candidates=candidates,
            query_context=sourcing_query,
            explanation_text=explanation_text,
            strategy_used=search_strategy,
            filters_applied=filters
        )
    
    def _generate_sourcing_explanation(
        self,
        job_description: Dict[str, Any],
        sourcing_query: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        search_strategy: str,
        filters: Dict[str, Any],
        detail_level: str
    ) -> str:
        """
        Generate the main sourcing explanation text.
        
        Args:
            job_description: Job details
            sourcing_query: Original sourcing query
            candidates: List of sourced candidates
            search_strategy: Strategy used for sourcing
            filters: Filters applied during sourcing
            detail_level: Level of detail
            
        Returns:
            Explanation text
        """
        # Create a prompt for the LLM
        prompt = f"""
        I need to explain the results of a candidate sourcing operation for a job.
        
        Job Title: {job_description.get('title', 'Unknown Position')}
        Company: {job_description.get('company', 'Unknown Company')}
        
        Sourcing Query:
        {json.dumps(sourcing_query, indent=2)}
        
        Search Strategy Used: {search_strategy}
        
        Filters Applied:
        {json.dumps(filters, indent=2)}
        
        Number of Candidates Found: {len(candidates)}
        
        Top Candidates:
        {self._format_candidate_list(candidates[:5])}
        """
        
        # Adjust system instruction based on detail level
        if detail_level == "brief":
            system_instruction = "Provide a brief, 2-3 sentence explanation of the sourcing results."
        elif detail_level == "standard":
            system_instruction = "Provide a clear, paragraph-length explanation of the sourcing results, highlighting the key factors and strategies used."
        else:  # detailed
            system_instruction = "Provide a comprehensive explanation of the sourcing results, with specific examples and details about the strategy, filters, and candidate matching."
        
        # Generate explanation using LLM
        try:
            explanation = self.generate_llm_explanation(
                prompt=prompt,
                system_instructions=system_instruction,
                temperature=0.3
            )
            return explanation
        except Exception as e:
            logger.error(f"Error generating sourcing explanation: {e}")
            # Fallback to a template-based explanation if LLM fails
            return self._fallback_sourcing_explanation(
                job_description, 
                candidates, 
                search_strategy,
                filters
            )
    
    def _format_candidate_list(self, candidates: List[Dict[str, Any]]) -> str:
        """
        Format a list of candidates for inclusion in the prompt.
        
        Args:
            candidates: List of candidate dictionaries
            
        Returns:
            Formatted string representing the candidates
        """
        if not candidates:
            return "No candidates found."
        
        formatted = ""
        for i, candidate in enumerate(candidates):
            name = candidate.get("name", f"Candidate {i+1}")
            score = candidate.get("score", 0.0)
            skills = candidate.get("skills", [])
            experience = candidate.get("experience", "Not specified")
            
            formatted += f"""
            Candidate: {name}
            Match Score: {score:.2f}
            Skills: {', '.join(skills) if skills else 'Not specified'}
            Experience: {experience}
            """
        
        return formatted
    
    def _fallback_sourcing_explanation(
        self,
        job_description: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        search_strategy: str,
        filters: Dict[str, Any]
    ) -> str:
        """
        Generate a fallback explanation without using LLM services.
        
        Args:
            job_description: Job details
            candidates: List of sourced candidates
            search_strategy: Strategy used for sourcing
            filters: Filters applied during sourcing
            
        Returns:
            Fallback explanation text
        """
        job_title = job_description.get("title", "the position")
        candidate_count = len(candidates)
        
        filter_text = ""
        if filters:
            filter_list = [f"{key}: {value}" for key, value in filters.items()]
            filter_text = f" with filters for {', '.join(filter_list)}"
        
        if candidate_count == 0:
            return f"No candidates were found for {job_title} using {search_strategy}{filter_text}. You may need to adjust your search criteria or expand your candidate pool."
        elif candidate_count == 1:
            return f"1 candidate was found for {job_title} using {search_strategy}{filter_text}. This candidate matches the job requirements based on our semantic search algorithm."
        else:
            return f"{candidate_count} candidates were found for {job_title} using {search_strategy}{filter_text}. These candidates are ranked by their relevance to the job requirements based on our semantic search algorithm."
