"""
Team Fit Analyzer for Advanced Matching.

This module analyzes how well a candidate would fit with a specific team
using Gemini's comparative reasoning capabilities.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union

from src.llm.gemini_service import GeminiService
from src.knowledge_base.vector_store import VectorStore
from src.matching.models import TeamFitResult

# Configure logging
logger = logging.getLogger(__name__)


class TeamFitAnalyzer:
    """
    Team fit analyzer that evaluates candidate compatibility with existing teams.
    
    Uses Gemini's comparative reasoning to analyze:
    1. Cultural alignment
    2. Working style compatibility
    3. Skill complementarity
    4. Team dynamics impact
    """
    
    def __init__(
        self,
        gemini_service: Optional[GeminiService] = None,
        vector_store: Optional[VectorStore] = None
    ):
        """
        Initialize the team fit analyzer.
        
        Args:
            gemini_service: Pre-configured Gemini service
            vector_store: Pre-configured vector store
        """
        # Initialize Gemini service
        try:
            self.gemini_service = gemini_service or GeminiService()
            logger.info("Initialized Gemini service for team fit analysis")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {e}")
            self.gemini_service = None
            
        # Initialize vector store
        self.vector_store = vector_store or VectorStore()
    
    def predict_team_fit(
        self, 
        candidate_id: str, 
        team_id: str,
        detailed: bool = True
    ) -> TeamFitResult:
        """
        Predict how well a candidate would fit with a specific team.
        
        Args:
            candidate_id: ID of the candidate
            team_id: ID of the team
            detailed: Whether to generate detailed analysis
            
        Returns:
            Team fit analysis result
        """
        try:
            # Retrieve team and candidate data
            team_data = self._get_team_profile(team_id)
            candidate_data = self._get_candidate_profile(candidate_id)
            
            if not team_data or not candidate_data:
                logger.error(f"Missing data for team {team_id} or candidate {candidate_id}")
                return TeamFitResult(
                    team_id=team_id,
                    candidate_id=candidate_id,
                    compatibility_score=0.0,
                    detailed_analysis="Unable to analyze team fit due to missing data."
                )
            
            # Generate team fit analysis using LLM
            analysis_data = self._generate_team_fit_analysis(team_data, candidate_data, detailed)
            
            # Create TeamFitResult object
            result = TeamFitResult(
                team_id=team_id,
                candidate_id=candidate_id,
                compatibility_score=analysis_data.get("compatibility_score", 0.0),
                key_factors=analysis_data.get("key_factors", []),
                detailed_analysis=analysis_data.get("detailed_analysis", ""),
                cultural_fit_score=analysis_data.get("cultural_fit_score", 0.0),
                working_style_compatibility=analysis_data.get("working_style_compatibility", 0.0),
                skill_complementarity=analysis_data.get("skill_complementarity", 0.0),
                team_dynamics_impact=analysis_data.get("team_dynamics_impact", 0.0)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error predicting team fit: {e}")
            # Return basic result with error information
            return TeamFitResult(
                team_id=team_id,
                candidate_id=candidate_id,
                compatibility_score=0.0,
                detailed_analysis=f"Error analyzing team fit: {str(e)}"
            )
    
    def _get_team_profile(self, team_id: str) -> Dict[str, Any]:
        """
        Get team profile from database.
        
        Args:
            team_id: ID of the team
            
        Returns:
            Team profile data
        """
        try:
            # Check if team exists in vector store
            team_data = self.vector_store.get_by_id("TeamProfile", team_id)
            
            if team_data:
                return team_data
                
            # If not found, check for related team data in company profiles
            company_profiles = self.vector_store.query("CompanyProfile", {
                "team_id": team_id
            }, limit=1)
            
            if company_profiles and len(company_profiles) > 0:
                company_data = company_profiles[0]
                
                # Extract team data from company profile
                teams = company_data.get("teams", [])
                for team in teams:
                    if team.get("id") == team_id:
                        return team
            
            logger.warning(f"Team profile not found: {team_id}")
            return {}
                
        except Exception as e:
            logger.error(f"Error retrieving team profile: {e}")
            return {}
    
    def _get_candidate_profile(self, candidate_id: str) -> Dict[str, Any]:
        """
        Get candidate profile from database.
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            Candidate profile data
        """
        try:
            return self.vector_store.get_by_id("CandidateProfile", candidate_id) or {}
        except Exception as e:
            logger.error(f"Error retrieving candidate profile: {e}")
            return {}
    
    def _generate_team_fit_analysis(
        self,
        team_data: Dict[str, Any],
        candidate_data: Dict[str, Any],
        detailed: bool = True
    ) -> Dict[str, Any]:
        """
        Generate team fit analysis using Gemini API.
        
        Args:
            team_data: Team profile data
            candidate_data: Candidate profile data
            detailed: Whether to generate detailed analysis
            
        Returns:
            Team fit analysis results
        """
        if not self.gemini_service:
            logger.warning("Gemini service not available for team fit analysis")
            return self._generate_fallback_analysis(team_data, candidate_data)
            
        try:
            # Extract relevant team information
            team_name = team_data.get("name", "Unknown Team")
            team_size = team_data.get("size", "Unknown")
            team_composition = team_data.get("composition", "")
            team_culture = team_data.get("culture", "")
            team_working_style = team_data.get("working_style", "")
            team_skills = team_data.get("skills", [])
            
            # Extract relevant candidate information
            candidate_name = candidate_data.get("name", "Unknown Candidate")
            candidate_skills = candidate_data.get("skills", [])
            candidate_experience = candidate_data.get("experience", "")
            candidate_working_style = candidate_data.get("working_style", "")
            candidate_preferences = candidate_data.get("preferences", {})
            
            # Create prompt for Gemini
            prompt = f"""
            Analyze how well the candidate would fit with the specified team.
            
            Team Information:
            - Name: {team_name}
            - Size: {team_size}
            - Composition: {team_composition}
            - Culture: {team_culture}
            - Working Style: {team_working_style}
            - Skills: {', '.join(team_skills)}
            
            Candidate Information:
            - Name: {candidate_name}
            - Skills: {', '.join(candidate_skills)}
            - Experience: {candidate_experience}
            - Working Style: {candidate_working_style}
            - Preferences: {json.dumps(candidate_preferences)}
            
            Analyze the following aspects:
            1. Cultural Fit: How well the candidate's values align with the team's culture
            2. Working Style Compatibility: Alignment in work patterns, communication, and collaboration
            3. Skill Complementarity: How the candidate's skills complement or overlap with the team
            4. Team Dynamics Impact: How the candidate might affect existing team dynamics
            
            Provide scores for each aspect (0-100), an overall compatibility score (0-100),
            and identify key factors influencing the fit.
            
            Respond in JSON format:
            {{"compatibility_score": float,
              "cultural_fit_score": float,
              "working_style_compatibility": float,
              "skill_complementarity": float,
              "team_dynamics_impact": float,
              "key_factors": [
                {{"factor": string, "impact": string, "score": float}}
              ],
              "detailed_analysis": string
            }}
            """
            
            # Call Gemini API
            response = self.gemini_service.generate_content(prompt)
            
            # Parse response
            try:
                analysis_data = json.loads(response)
                return analysis_data
            except (json.JSONDecodeError, TypeError):
                # Try to extract JSON from text response
                import re
                json_pattern = r'{.*}'
                matches = re.search(json_pattern, response, re.DOTALL)
                if matches:
                    try:
                        analysis_data = json.loads(matches.group(0))
                        return analysis_data
                    except json.JSONDecodeError:
                        pass
                
                logger.warning("Failed to parse Gemini response as JSON, using fallback")
                return self._generate_fallback_analysis(team_data, candidate_data)
                
        except Exception as e:
            logger.error(f"Error generating team fit analysis with Gemini: {e}")
            return self._generate_fallback_analysis(team_data, candidate_data)
    
    def _generate_fallback_analysis(
        self,
        team_data: Dict[str, Any],
        candidate_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate fallback team fit analysis when Gemini is unavailable.
        
        Args:
            team_data: Team profile data
            candidate_data: Candidate profile data
            
        Returns:
            Basic team fit analysis
        """
        # Extract team and candidate skills for comparison
        team_skills = set([s.lower() for s in team_data.get("skills", [])])
        candidate_skills = set([s.lower() for s in candidate_data.get("skills", [])])
        
        # Calculate basic skill complementarity
        shared_skills = team_skills.intersection(candidate_skills)
        unique_candidate_skills = candidate_skills - team_skills
        
        if not team_skills:
            skill_comp_score = 50.0  # Default when no team skills available
        else:
            # Calculate complementarity - higher score when candidate brings unique skills
            skill_comp_score = min(
                (len(shared_skills) / max(1, len(team_skills)) * 50) +
                (len(unique_candidate_skills) / max(1, len(candidate_skills)) * 50),
                100.0
            )
        
        # Calculate basic working style compatibility
        working_style_score = 65.0  # Default moderate compatibility
        team_style = team_data.get("working_style", "").lower()
        candidate_style = candidate_data.get("working_style", "").lower()
        
        if team_style and candidate_style:
            # Check for keyword matches in working styles
            compatibility_terms = [
                ("collaborative", "team", "cooperat"),
                ("independent", "autonomy", "self-direct"),
                ("detail", "thorough", "meticulous"),
                ("big picture", "strategic", "overview"),
                ("agile", "fast-paced", "dynamic"),
                ("structured", "methodical", "organized")
            ]
            
            matches = 0
            for term_group in compatibility_terms:
                team_has = any(term in team_style for term in term_group)
                candidate_has = any(term in candidate_style for term in term_group)
                
                if team_has == candidate_has:
                    matches += 1
            
            working_style_score = (matches / len(compatibility_terms)) * 100
        
        # Calculate basic cultural fit score
        cultural_score = 70.0  # Default decent cultural fit
        
        # Calculate team dynamics impact (default to moderate positive)
        team_dynamics_score = 65.0
        
        # Calculate overall compatibility score
        compatibility_score = (
            skill_comp_score * 0.3 +
            working_style_score * 0.3 +
            cultural_score * 0.25 +
            team_dynamics_score * 0.15
        )
        
        # Create key factors
        key_factors = [
            {
                "factor": "Skill complementarity",
                "impact": f"Candidate shares {len(shared_skills)} skills with the team and brings {len(unique_candidate_skills)} unique skills",
                "score": skill_comp_score
            },
            {
                "factor": "Working style compatibility",
                "impact": "Moderate alignment in working patterns based on available information",
                "score": working_style_score
            }
        ]
        
        # Generate basic analysis text
        detailed_analysis = f"""
        # Team Fit Analysis
        
        ## Overall Compatibility: {compatibility_score:.1f}%
        
        The candidate appears to have a {'good' if compatibility_score >= 70 else 'moderate'} fit with the team.
        
        ### Skill Complementarity: {skill_comp_score:.1f}%
        The candidate shares {len(shared_skills)} skills with the team and brings {len(unique_candidate_skills)} unique skills, 
        creating a {'good' if skill_comp_score >= 70 else 'moderate'} balance between alignment and diversity.
        
        ### Working Style Compatibility: {working_style_score:.1f}%
        Based on available information, there appears to be a {'good' if working_style_score >= 70 else 'moderate'} 
        alignment in work patterns and collaboration style.
        
        ### Note
        This is a basic analysis based on limited information. For a more comprehensive assessment, 
        additional data about team culture and dynamics would be beneficial.
        """
        
        return {
            "compatibility_score": compatibility_score,
            "cultural_fit_score": cultural_score,
            "working_style_compatibility": working_style_score,
            "skill_complementarity": skill_comp_score,
            "team_dynamics_impact": team_dynamics_score,
            "key_factors": key_factors,
            "detailed_analysis": detailed_analysis
        }
