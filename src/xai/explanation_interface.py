"""
Explainable AI (XAI) Interface for RecruitPro AI.

This module provides a standardized interface for generating explanations
about agent decisions, ensuring transparency and accountability.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class ExplanationProvider(ABC):
    """Base interface for all explanation providers."""
    
    @abstractmethod
    def generate_explanation(self, 
                             context: Dict[str, Any],
                             detail_level: str = "standard") -> Dict[str, Any]:
        """
        Generate an explanation for an agent decision.
        
        Args:
            context: Dictionary containing all relevant context for generating the explanation
            detail_level: Level of detail to include in the explanation ("brief", "standard", "detailed")
            
        Returns:
            Dictionary containing the generated explanation and metadata
        """
        pass


class ExplanationFormat:
    """Standard formats for explanations to ensure consistency."""
    
    @staticmethod
    def matching_explanation(
        score: float,
        factors: Dict[str, Any],
        explanation_text: str,
        factor_explanations: Optional[Dict[str, str]] = None,
        strengths: Optional[List[str]] = None,
        improvement_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized explanation for matching decisions.
        
        Args:
            score: Overall match score (0.0 to 1.0)
            factors: Factor scores that contributed to the overall score
            explanation_text: Main textual explanation
            factor_explanations: Optional detailed explanations for each factor
            strengths: Optional list of candidate strengths for this match
            improvement_areas: Optional list of areas where candidate could improve
        
        Returns:
            Standardized explanation dictionary
        """
        explanation = {
            "score": score,
            "explanation": explanation_text,
            "factors": factors,
        }
        
        if factor_explanations:
            explanation["factor_explanations"] = factor_explanations
            
        if strengths:
            explanation["strengths"] = strengths
            
        if improvement_areas:
            explanation["improvement_areas"] = improvement_areas
            
        return explanation
    
    @staticmethod
    def sourcing_explanation(
        candidates: List[Dict[str, Any]],
        query_context: Dict[str, Any],
        explanation_text: str,
        strategy_used: str,
        filters_applied: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized explanation for sourcing decisions.
        
        Args:
            candidates: List of sourced candidates with scores
            query_context: Context of the original sourcing query
            explanation_text: Main textual explanation
            strategy_used: Description of the sourcing strategy used
            filters_applied: Optional details on filters that were applied
        
        Returns:
            Standardized explanation dictionary
        """
        explanation = {
            "candidate_count": len(candidates),
            "explanation": explanation_text,
            "strategy": strategy_used,
            "query_context": query_context
        }
        
        if filters_applied:
            explanation["filters_applied"] = filters_applied
            
        return explanation
    
    @staticmethod
    def screening_explanation(
        decision: str,
        score: float,
        criteria: Dict[str, Any],
        explanation_text: str,
        key_findings: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized explanation for screening decisions.
        
        Args:
            decision: Overall decision (e.g., "pass", "reject", "hold")
            score: Overall screening score (0.0 to 1.0)
            criteria: Scores for individual screening criteria
            explanation_text: Main textual explanation
            key_findings: Optional list of key findings from the screening
        
        Returns:
            Standardized explanation dictionary
        """
        explanation = {
            "decision": decision,
            "score": score,
            "explanation": explanation_text,
            "criteria": criteria
        }
        
        if key_findings:
            explanation["key_findings"] = key_findings
            
        return explanation


class LLMExplanationMixin:
    """
    Mixin for agents to generate explanations using LLM services.
    
    This mixin requires the implementing class to have self.llm_service available.
    """
    
    def generate_llm_explanation(
        self, 
        prompt: str,
        system_instructions: str,
        temperature: float = 0.3,
        max_tokens: int = 1024
    ) -> str:
        """
        Generate an explanation using the LLM service.
        
        Args:
            prompt: Prompt for the LLM to generate an explanation
            system_instructions: System instructions for the LLM
            temperature: Temperature for LLM generation (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated explanation text
        """
        # Gemini API doesn't support system_instructions, so incorporate them into the prompt
        combined_prompt = f"""Instructions: {system_instructions}

Please analyze the following information:

{prompt}

Remember to follow the instructions above."""
        
        # This requires the implementing class to have self.llm_service
        return self.llm_service.generate_text(
            prompt=combined_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens
        )
