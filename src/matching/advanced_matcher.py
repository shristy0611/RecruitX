"""
Advanced Matcher for RecruitPro AI.

This module provides advanced matching capabilities with bi-directional preferences,
team fit analysis, and career trajectory prediction.
"""

import logging
import time
import uuid
from dataclasses import asdict
from typing import Dict, List, Any, Optional, Tuple, Union, Set

from src.agents.matching_agent import MatchingAgent, MatchingResult
from src.knowledge_base.vector_store import VectorStore
from src.llm.gemini_service import GeminiService
from src.matching.models import (
    AdvancedMatchingResult,
    BiDirectionalPreference,
    TeamFitResult,
    CareerTrajectoryResult
)
from src.matching.team_fit_analyzer import TeamFitAnalyzer
from src.matching.career_trajectory_analyzer import CareerTrajectoryAnalyzer

# Configure logging
logger = logging.getLogger(__name__)


class AdvancedMatcher:
    """
    Advanced matcher providing sophisticated candidate-job matching capabilities.
    
    Features:
    1. Context-aware matching with bi-directional preference consideration
    2. Team fit analysis with Gemini's comparative reasoning
    3. Career trajectory prediction and growth potential assessment
    """
    
    def __init__(
        self,
        base_matcher: Optional[MatchingAgent] = None,
        vector_store: Optional[VectorStore] = None,
        gemini_service: Optional[GeminiService] = None
    ):
        """
        Initialize the advanced matcher.
        
        Args:
            base_matcher: Pre-configured base matching agent (optional)
            vector_store: Vector store for data retrieval
            gemini_service: Gemini service for advanced analysis
        """
        # Initialize base components
        self.base_matcher = base_matcher or MatchingAgent()
        self.vector_store = vector_store or VectorStore()
        
        # Initialize specialized analyzers
        self.team_fit_analyzer = TeamFitAnalyzer(
            gemini_service=gemini_service,
            vector_store=self.vector_store
        )
        
        self.career_analyzer = CareerTrajectoryAnalyzer(
            gemini_service=gemini_service,
            vector_store=self.vector_store
        )
        
        # Cache for results
        self.result_cache: Dict[str, AdvancedMatchingResult] = {}
    
    def match_candidate_to_job(
        self,
        candidate_id: str,
        job_id: str,
        include_team_fit: bool = True,
        include_career_trajectory: bool = True,
        team_id: Optional[str] = None,
        detailed: bool = True
    ) -> AdvancedMatchingResult:
        """
        Perform comprehensive matching between a candidate and job.
        
        Args:
            candidate_id: ID of the candidate
            job_id: ID of the job
            include_team_fit: Whether to include team fit analysis
            include_career_trajectory: Whether to include career trajectory analysis
            team_id: Optional team ID (if not provided, will be derived from job data)
            detailed: Whether to generate detailed explanations
            
        Returns:
            Comprehensive matching result
        """
        try:
            # Generate cache key
            cache_key = f"{candidate_id}:{job_id}:{include_team_fit}:{include_career_trajectory}"
            
            # Check if result is cached
            if cache_key in self.result_cache:
                return self.result_cache[cache_key]
            
            # Retrieve job and candidate data
            job_data = self.vector_store.get_by_id("JobDescription", job_id)
            candidate_data = self.vector_store.get_by_id("CandidateProfile", candidate_id)
            
            if not job_data or not candidate_data:
                logger.error(f"Missing data for job {job_id} or candidate {candidate_id}")
                return AdvancedMatchingResult(
                    candidate_id=candidate_id,
                    job_id=job_id,
                    explanation="Unable to perform matching due to missing data."
                )
            
            # Perform basic matching using the base matcher
            basic_results = self.base_matcher.match_candidates(
                job_id=job_id,
                candidate_ids=[candidate_id],
                require_explanation=True
            )
            
            if not basic_results:
                logger.error(f"Base matching failed for candidate {candidate_id} and job {job_id}")
                return AdvancedMatchingResult(
                    candidate_id=candidate_id,
                    job_id=job_id,
                    explanation="Base matching failed to produce results."
                )
            
            basic_result = basic_results[0]
            
            # Extract team ID from job data if not provided
            if include_team_fit and not team_id:
                team_id = self._extract_team_id(job_data)
            
            # Initialize advanced result with basic matching data
            advanced_result = AdvancedMatchingResult(
                candidate_id=candidate_id,
                job_id=job_id,
                matching_id=basic_result.matching_id,
                overall_score=basic_result.overall_score,
                skill_match_score=basic_result.skill_match_score,
                experience_match_score=basic_result.experience_match_score,
                education_match_score=basic_result.education_match_score,
                skills_matched=basic_result.skills_matched,
                skills_missing=basic_result.skills_missing,
                explanation=basic_result.explanation
            )
            
            # Analyze bi-directional preferences
            preference_result = self._analyze_bi_directional_preferences(candidate_data, job_data)
            advanced_result.bi_directional_preferences = preference_result
            
            # Perform team fit analysis if requested
            if include_team_fit and team_id:
                team_fit_result = self.team_fit_analyzer.predict_team_fit(
                    candidate_id=candidate_id,
                    team_id=team_id,
                    detailed=detailed
                )
                advanced_result.team_fit = team_fit_result
            
            # Perform career trajectory analysis if requested
            if include_career_trajectory:
                trajectory_result = self.career_analyzer.predict_career_trajectory(
                    candidate_id=candidate_id,
                    job_id=job_id,
                    detailed=detailed
                )
                advanced_result.career_trajectory = trajectory_result
            
            # Generate enhanced explanation
            advanced_result.detailed_explanation = self._generate_enhanced_explanation(
                advanced_result, 
                job_data,
                candidate_data
            )
            
            # Cache result
            self.result_cache[cache_key] = advanced_result
            
            return advanced_result
            
        except Exception as e:
            logger.error(f"Error in advanced matching: {e}")
            return AdvancedMatchingResult(
                candidate_id=candidate_id,
                job_id=job_id,
                explanation=f"Error performing advanced matching: {str(e)}"
            )
    
    def match_candidates_to_job(
        self,
        job_id: str,
        candidate_ids: List[str],
        include_team_fit: bool = True,
        include_career_trajectory: bool = True,
        team_id: Optional[str] = None,
        min_score: float = 60.0,
        max_results: int = 10,
        detailed: bool = False
    ) -> List[AdvancedMatchingResult]:
        """
        Match multiple candidates to a job with advanced analysis.
        
        Args:
            job_id: ID of the job
            candidate_ids: List of candidate IDs to match
            include_team_fit: Whether to include team fit analysis
            include_career_trajectory: Whether to include career trajectory analysis
            team_id: Optional team ID (if not provided, will be derived from job data)
            min_score: Minimum overall score to include in results
            max_results: Maximum number of results to return
            detailed: Whether to generate detailed explanations
            
        Returns:
            List of advanced matching results, sorted by overall score
        """
        results = []
        
        for candidate_id in candidate_ids:
            try:
                result = self.match_candidate_to_job(
                    candidate_id=candidate_id,
                    job_id=job_id,
                    include_team_fit=include_team_fit,
                    include_career_trajectory=include_career_trajectory,
                    team_id=team_id,
                    detailed=detailed
                )
                
                # Only include results above minimum score
                if result.overall_score >= min_score:
                    results.append(result)
                    
            except Exception as e:
                logger.error(f"Error matching candidate {candidate_id} to job {job_id}: {e}")
                continue
        
        # Sort by overall score (descending)
        results.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Limit to max results
        return results[:max_results]
    
    def match_job_to_candidates(
        self,
        job_id: str,
        include_team_fit: bool = True,
        include_career_trajectory: bool = True,
        team_id: Optional[str] = None,
        min_score: float = 60.0,
        max_results: int = 10,
        detailed: bool = False
    ) -> List[AdvancedMatchingResult]:
        """
        Find best matching candidates for a job with advanced analysis.
        
        Args:
            job_id: ID of the job
            include_team_fit: Whether to include team fit analysis
            include_career_trajectory: Whether to include career trajectory analysis
            team_id: Optional team ID (if not provided, will be derived from job data)
            min_score: Minimum overall score to include in results
            max_results: Maximum number of results to return
            detailed: Whether to generate detailed explanations
            
        Returns:
            List of advanced matching results, sorted by overall score
        """
        try:
            # Find candidate IDs using vector store
            candidate_matches = self.vector_store.get_job_candidates_match(
                job_id=job_id,
                limit=max_results * 2  # Get more candidates than needed
            )
            
            if not candidate_matches:
                logger.warning(f"No initial candidate matches found for job {job_id}")
                return []
            
            # Extract candidate IDs
            candidate_ids = [match["id"] for match in candidate_matches if "id" in match]
            
            # Perform advanced matching
            return self.match_candidates_to_job(
                job_id=job_id,
                candidate_ids=candidate_ids,
                include_team_fit=include_team_fit,
                include_career_trajectory=include_career_trajectory,
                team_id=team_id,
                min_score=min_score,
                max_results=max_results,
                detailed=detailed
            )
            
        except Exception as e:
            logger.error(f"Error matching job {job_id} to candidates: {e}")
            return []
    
    def _extract_team_id(self, job_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract team ID from job data.
        
        Args:
            job_data: Job data dictionary
            
        Returns:
            Team ID if found, None otherwise
        """
        # Check if team ID is directly specified
        team_id = job_data.get("team_id")
        if team_id:
            return team_id
            
        # Check if team is specified in company data
        company = job_data.get("company", {})
        if company:
            team_id = company.get("team_id")
            if team_id:
                return team_id
                
            # Check for default team
            teams = company.get("teams", [])
            if teams and len(teams) > 0:
                return teams[0].get("id")
        
        return None
    
    def _analyze_bi_directional_preferences(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> BiDirectionalPreference:
        """
        Analyze bi-directional preferences between candidate and job.
        
        Args:
            candidate_data: Candidate profile data
            job_data: Job data
            
        Returns:
            Bi-directional preference analysis
        """
        # Extract candidate preferences
        candidate_preferences = {}
        
        # Convert explicit preferences if available
        if "preferences" in candidate_data:
            raw_preferences = candidate_data["preferences"]
            if isinstance(raw_preferences, dict):
                candidate_preferences = {
                    k: float(v) if isinstance(v, (int, float)) else 0.0
                    for k, v in raw_preferences.items()
                }
        
        # Infer preferences from resume if not explicitly stated
        if not candidate_preferences:
            candidate_preferences = self._infer_candidate_preferences(candidate_data)
        
        # Extract company/job preferences
        company_preferences = {}
        
        # Get preferences from job posting
        if "preferences" in job_data:
            raw_preferences = job_data["preferences"]
            if isinstance(raw_preferences, dict):
                company_preferences = {
                    k: float(v) if isinstance(v, (int, float)) else 0.0
                    for k, v in raw_preferences.items()
                }
        
        # Infer preferences from job description if not explicitly stated
        if not company_preferences:
            company_preferences = self._infer_job_preferences(job_data)
        
        # Create and calculate bi-directional preference
        preference = BiDirectionalPreference(
            candidate_preferences=candidate_preferences,
            company_preferences=company_preferences
        )
        
        # Calculate alignment score
        preference.calculate_alignment_score()
        
        return preference
    
    def _infer_candidate_preferences(self, candidate_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Infer candidate preferences from profile data.
        
        Args:
            candidate_data: Candidate profile data
            
        Returns:
            Dictionary of inferred preferences
        """
        preferences = {}
        
        # Extract text for analysis
        experience = candidate_data.get("experience", "")
        summary = candidate_data.get("summary", "")
        text = f"{summary} {experience}"
        text_lower = text.lower()
        
        # Check for remote work preference
        if "remote" in text_lower:
            if "prefer remote" in text_lower or "remote preferred" in text_lower:
                preferences["remote_work"] = 0.8
            elif "open to remote" in text_lower:
                preferences["remote_work"] = 0.5
        
        # Check for work-life balance preference
        if "work-life balance" in text_lower or "work life balance" in text_lower:
            preferences["work_life_balance"] = 0.8
        
        # Check for growth preference
        if "growth" in text_lower:
            if "career growth" in text_lower or "professional growth" in text_lower:
                preferences["growth_opportunities"] = 0.9
            else:
                preferences["growth_opportunities"] = 0.7
        
        # Check for learning preference
        if "learning" in text_lower or "continuous learning" in text_lower:
            preferences["learning_opportunities"] = 0.8
        
        # Check for team preference
        if "collaborative" in text_lower or "team environment" in text_lower:
            preferences["collaborative_environment"] = 0.8
        
        # Check for innovation preference
        if "innovation" in text_lower or "cutting edge" in text_lower:
            preferences["innovation"] = 0.8
        
        # Default preferences if none detected
        if not preferences:
            preferences = {
                "growth_opportunities": 0.7,
                "work_life_balance": 0.6,
                "collaborative_environment": 0.5,
                "remote_work": 0.5
            }
        
        return preferences
    
    def _infer_job_preferences(self, job_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Infer job/company preferences from job data.
        
        Args:
            job_data: Job data
            
        Returns:
            Dictionary of inferred preferences
        """
        preferences = {}
        
        # Extract text for analysis
        description = job_data.get("description", "")
        requirements = job_data.get("requirements", "")
        company_info = job_data.get("company", {}).get("description", "")
        text = f"{description} {requirements} {company_info}"
        text_lower = text.lower()
        
        # Check for team preference
        if "team player" in text_lower or "collaborative" in text_lower:
            preferences["collaborative_environment"] = 0.9
        
        # Check for self-starter preference
        if "self-starter" in text_lower or "independent" in text_lower:
            preferences["independence"] = 0.8
        
        # Check for innovation preference
        if "innovation" in text_lower or "innovative" in text_lower:
            preferences["innovation"] = 0.8
        
        # Check for fast-paced preference
        if "fast-paced" in text_lower or "fast paced" in text_lower:
            preferences["fast_paced"] = 0.8
        
        # Check for growth preference
        if "growth" in text_lower:
            preferences["growth_opportunities"] = 0.7
        
        # Check for remote work preference
        if "remote" in text_lower:
            if "fully remote" in text_lower or "100% remote" in text_lower:
                preferences["remote_work"] = 1.0
            elif "hybrid" in text_lower:
                preferences["remote_work"] = 0.5
            else:
                preferences["remote_work"] = 0.7
        else:
            preferences["remote_work"] = 0.0
        
        # Default preferences if none detected
        if not preferences:
            preferences = {
                "collaborative_environment": 0.7,
                "growth_opportunities": 0.6,
                "innovation": 0.5,
                "remote_work": 0.3
            }
        
        return preferences
    
    def _generate_enhanced_explanation(
        self,
        result: AdvancedMatchingResult,
        job_data: Dict[str, Any],
        candidate_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate enhanced explanation with all advanced matching components.
        
        Args:
            result: Advanced matching result
            job_data: Job data
            candidate_data: Candidate data
            
        Returns:
            Enhanced explanation dictionary
        """
        # Start with basic explanation
        explanation = result.explanation
        
        # Add explanation sections for advanced components
        sections = []
        
        # Add bi-directional preferences section
        if result.bi_directional_preferences:
            pref = result.bi_directional_preferences
            bi_directional_section = {
                "title": "Preference Alignment",
                "score": pref.preference_alignment_score,
                "content": self._generate_preference_explanation(pref, job_data, candidate_data)
            }
            sections.append(bi_directional_section)
        
        # Add team fit section
        if result.team_fit:
            team_fit_section = {
                "title": "Team Fit Analysis",
                "score": result.team_fit.compatibility_score,
                "content": result.team_fit.detailed_analysis,
                "factors": result.team_fit.key_factors
            }
            sections.append(team_fit_section)
        
        # Add career trajectory section
        if result.career_trajectory:
            career_section = {
                "title": "Career Trajectory",
                "score": result.career_trajectory.growth_potential_score,
                "content": result.career_trajectory.detailed_analysis,
                "future_roles": result.career_trajectory.predicted_future_roles,
                "development_areas": result.career_trajectory.development_areas
            }
            sections.append(career_section)
        
        # Create enhanced explanation
        enhanced_explanation = {
            "summary": self._generate_summary(result),
            "basic_explanation": explanation,
            "sections": sections,
            "overall_recommendation": self._generate_overall_recommendation(result)
        }
        
        return enhanced_explanation
    
    def _generate_preference_explanation(
        self,
        preferences: BiDirectionalPreference,
        job_data: Dict[str, Any],
        candidate_data: Dict[str, Any]
    ) -> str:
        """
        Generate explanation for preference alignment.
        
        Args:
            preferences: BiDirectionalPreference object
            job_data: Job data
            candidate_data: Candidate data
            
        Returns:
            Preference alignment explanation
        """
        job_title = job_data.get("title", "the position")
        candidate_name = candidate_data.get("name", "The candidate")
        company_name = job_data.get("company", {}).get("name", "the company")
        
        # Format the alignment score
        alignment_score = f"{preferences.preference_alignment_score:.1f}%"
        
        # Create explanation
        explanation = f"""
        ## Preference Alignment: {alignment_score}
        
        {candidate_name}'s preferences align {alignment_score} with the requirements and culture of {company_name}.
        
        ### Key Alignment Factors:
        """
        
        # Find common factors
        common_factors = set(preferences.candidate_preferences.keys()) & set(preferences.company_preferences.keys())
        
        if common_factors:
            for factor in common_factors:
                candidate_value = preferences.candidate_preferences.get(factor, 0)
                company_value = preferences.company_preferences.get(factor, 0)
                
                # Convert to percentage if not already
                if candidate_value <= 1.0:
                    candidate_value *= 100
                if company_value <= 1.0:
                    company_value *= 100
                
                # Calculate alignment
                alignment = 100 - abs(candidate_value - company_value)
                
                # Format factor name for display
                display_factor = factor.replace("_", " ").title()
                
                explanation += f"\n- **{display_factor}**: Candidate preference: {candidate_value:.0f}%, Company preference: {company_value:.0f}% (Alignment: {alignment:.0f}%)"
        else:
            explanation += "\nInsufficient preference data available for detailed alignment analysis."
        
        return explanation
    
    def _generate_summary(self, result: AdvancedMatchingResult) -> str:
        """
        Generate summary of all matching components.
        
        Args:
            result: Advanced matching result
            
        Returns:
            Summary text
        """
        components = [
            ("Skill Match", result.skill_match_score),
            ("Experience Match", result.experience_match_score),
            ("Education Match", result.education_match_score)
        ]
        
        if result.bi_directional_preferences:
            components.append(("Preference Alignment", 
                              result.bi_directional_preferences.preference_alignment_score))
        
        if result.team_fit:
            components.append(("Team Fit", result.team_fit.compatibility_score))
        
        if result.career_trajectory:
            components.append(("Growth Potential", 
                              result.career_trajectory.growth_potential_score))
        
        # Create summary text
        summary = "## Match Summary\n\n"
        summary += f"**Overall Match Score: {result.overall_score:.1f}%**\n\n"
        summary += "Component scores:\n"
        
        for component, score in components:
            summary += f"- {component}: {score:.1f}%\n"
        
        return summary
    
    def _generate_overall_recommendation(self, result: AdvancedMatchingResult) -> str:
        """
        Generate overall recommendation based on all factors.
        
        Args:
            result: Advanced matching result
            
        Returns:
            Recommendation text
        """
        # Calculate composite score with all factors
        composite_score = result.overall_score
        factor_count = 1
        
        if result.bi_directional_preferences:
            composite_score += result.bi_directional_preferences.preference_alignment_score
            factor_count += 1
        
        if result.team_fit:
            composite_score += result.team_fit.compatibility_score
            factor_count += 1
        
        if result.career_trajectory:
            composite_score += result.career_trajectory.growth_potential_score
            factor_count += 1
        
        composite_score /= factor_count
        
        # Generate recommendation based on composite score
        if composite_score >= 85:
            recommendation = "**Exceptional Match** - Strongly recommended for immediate interview. This candidate shows excellent alignment across all evaluation dimensions."
        elif composite_score >= 75:
            recommendation = "**Strong Match** - Recommended for interview. The candidate demonstrates strong compatibility with the position requirements and company preferences."
        elif composite_score >= 65:
            recommendation = "**Good Match** - Consider for interview. While some areas could be stronger, the overall profile indicates a good fit for the role."
        elif composite_score >= 55:
            recommendation = "**Moderate Match** - Potential interview candidate. There are some gaps to address, but the candidate may still be viable depending on the candidate pool."
        else:
            recommendation = "**Low Match** - Not recommended at this time. Significant gaps exist between the candidate profile and position requirements."
        
        return f"## Overall Recommendation\n\n{recommendation}\n\nComposite match score: {composite_score:.1f}%"
