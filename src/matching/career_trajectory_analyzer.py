"""
Career Trajectory Analyzer for Advanced Matching.

This module predicts career trajectory and growth potential for candidates
based on their current profile and job opportunities.
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple, Union

from src.llm.gemini_service import GeminiService
from src.knowledge_base.vector_store import VectorStore
from src.matching.models import CareerTrajectoryResult
from src.skills.extractors.factory import SkillExtractorFactory

# Configure logging
logger = logging.getLogger(__name__)


class CareerTrajectoryAnalyzer:
    """
    Career trajectory analyzer that predicts growth potential and future roles.
    
    Uses historical data, market trends, and career progression patterns to:
    1. Predict growth potential in a role
    2. Identify future career paths
    3. Estimate timeline for career progression
    4. Analyze skill growth opportunities
    """
    
    def __init__(
        self,
        gemini_service: Optional[GeminiService] = None,
        vector_store: Optional[VectorStore] = None
    ):
        """
        Initialize the career trajectory analyzer.
        
        Args:
            gemini_service: Pre-configured Gemini service
            vector_store: Pre-configured vector store
        """
        # Initialize Gemini service
        try:
            self.gemini_service = gemini_service or GeminiService()
            logger.info("Initialized Gemini service for career trajectory analysis")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {e}")
            self.gemini_service = None
            
        # Initialize vector store
        self.vector_store = vector_store or VectorStore()
        
        # Initialize skill extractor for identifying development areas
        try:
            self.skill_extractor = SkillExtractorFactory.create_extractor("enhanced")
            logger.info("Initialized skill extractor for career trajectory analysis")
        except Exception as e:
            logger.error(f"Failed to initialize skill extractor: {e}")
            self.skill_extractor = None
        
        # Load career progression data
        self.career_paths = self._load_career_paths()
        self.skill_development_data = self._load_skill_development_data()
    
    def predict_career_trajectory(
        self, 
        candidate_id: str, 
        job_id: str,
        detailed: bool = True
    ) -> CareerTrajectoryResult:
        """
        Predict career trajectory and growth potential for a candidate in a specific job.
        
        Args:
            candidate_id: ID of the candidate
            job_id: ID of the job opportunity
            detailed: Whether to generate detailed analysis
            
        Returns:
            Career trajectory analysis result
        """
        try:
            # Retrieve job and candidate data
            job_data = self._get_job_data(job_id)
            candidate_data = self._get_candidate_data(candidate_id)
            
            if not job_data or not candidate_data:
                logger.error(f"Missing data for job {job_id} or candidate {candidate_id}")
                return CareerTrajectoryResult(
                    candidate_id=candidate_id,
                    job_id=job_id,
                    growth_potential_score=0.0,
                    detailed_analysis="Unable to analyze career trajectory due to missing data."
                )
            
            # Generate career trajectory analysis using LLM
            analysis_data = self._generate_trajectory_analysis(job_data, candidate_data, detailed)
            
            # Create CareerTrajectoryResult object
            result = CareerTrajectoryResult(
                candidate_id=candidate_id,
                job_id=job_id,
                growth_potential_score=analysis_data.get("growth_potential_score", 0.0),
                trajectory_alignment_score=analysis_data.get("trajectory_alignment_score", 0.0),
                skills_growth_opportunity=analysis_data.get("skills_growth_opportunity", 0.0),
                predicted_future_roles=analysis_data.get("predicted_future_roles", []),
                growth_timeline=analysis_data.get("growth_timeline", {}),
                detailed_analysis=analysis_data.get("detailed_analysis", ""),
                development_areas=analysis_data.get("development_areas", [])
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error predicting career trajectory: {e}")
            # Return basic result with error information
            return CareerTrajectoryResult(
                candidate_id=candidate_id,
                job_id=job_id,
                growth_potential_score=0.0,
                detailed_analysis=f"Error analyzing career trajectory: {str(e)}"
            )
    
    def _get_job_data(self, job_id: str) -> Dict[str, Any]:
        """
        Get job data from database.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Job data
        """
        try:
            return self.vector_store.get_by_id("JobDescription", job_id) or {}
        except Exception as e:
            logger.error(f"Error retrieving job data: {e}")
            return {}
    
    def _get_candidate_data(self, candidate_id: str) -> Dict[str, Any]:
        """
        Get candidate data from database.
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            Candidate data
        """
        try:
            return self.vector_store.get_by_id("CandidateProfile", candidate_id) or {}
        except Exception as e:
            logger.error(f"Error retrieving candidate data: {e}")
            return {}
    
    def _load_career_paths(self) -> Dict[str, Any]:
        """
        Load career progression path data.
        
        Returns:
            Dictionary of career paths by industry
        """
        try:
            # Check if career paths exist in the vector store
            results = self.vector_store.query(
                "CareerPathData",
                {"type": "career_paths"},
                limit=1
            )
            
            if results and len(results) > 0:
                return results[0].get("data", {})
            
            # Fallback to default career paths
            return {
                "software_engineering": {
                    "entry": ["Junior Developer", "Software Engineer I", "Associate Developer"],
                    "mid": ["Software Engineer II", "Full Stack Developer", "Backend Developer"],
                    "senior": ["Senior Software Engineer", "Tech Lead", "Software Architect"],
                    "leadership": ["Engineering Manager", "Director of Engineering", "VP of Engineering", "CTO"],
                    "specialty": ["DevOps Engineer", "Site Reliability Engineer", "Security Engineer"]
                },
                "data_science": {
                    "entry": ["Junior Data Analyst", "Data Scientist I", "Associate Data Scientist"],
                    "mid": ["Data Scientist II", "Machine Learning Engineer", "Analytics Engineer"],
                    "senior": ["Senior Data Scientist", "Lead Data Scientist", "ML Architect"],
                    "leadership": ["Data Science Manager", "Director of Data Science", "Chief Data Officer"],
                    "specialty": ["NLP Specialist", "Computer Vision Engineer", "Decision Science Expert"]
                },
                "product_management": {
                    "entry": ["Associate Product Manager", "Product Analyst", "Product Specialist"],
                    "mid": ["Product Manager", "Product Owner", "Technical Product Manager"],
                    "senior": ["Senior Product Manager", "Group Product Manager", "Product Lead"],
                    "leadership": ["Director of Product", "VP of Product", "Chief Product Officer"],
                    "specialty": ["UX Product Manager", "Data Product Manager", "Growth Product Manager"]
                }
            }
                
        except Exception as e:
            logger.error(f"Error loading career paths: {e}")
            return {}
    
    def _load_skill_development_data(self) -> Dict[str, Any]:
        """
        Load skill development data.
        
        Returns:
            Dictionary of skill development data
        """
        try:
            # Check if skill development data exists in the vector store
            results = self.vector_store.query(
                "SkillDevelopmentData",
                {"type": "skill_development"},
                limit=1
            )
            
            if results and len(results) > 0:
                return results[0].get("data", {})
            
            # Fallback to basic skill development data
            return {
                "hot_skills": [
                    "Machine Learning", "Python", "Data Science", "AI", "Cloud Computing",
                    "DevOps", "Kubernetes", "React", "Node.js", "TypeScript"
                ],
                "emerging_skills": [
                    "MLOps", "LLMOps", "AI Ethics", "Prompt Engineering", "Rust", 
                    "Web3", "Quantum Computing", "Edge Computing", "Green IT"
                ],
                "growth_rates": {
                    "Machine Learning": 0.25,
                    "Cloud Computing": 0.20,
                    "DevOps": 0.18,
                    "Data Science": 0.22,
                    "AI": 0.30
                }
            }
                
        except Exception as e:
            logger.error(f"Error loading skill development data: {e}")
            return {}
    
    def _generate_trajectory_analysis(
        self,
        job_data: Dict[str, Any],
        candidate_data: Dict[str, Any],
        detailed: bool = True
    ) -> Dict[str, Any]:
        """
        Generate career trajectory analysis using Gemini API.
        
        Args:
            job_data: Job data
            candidate_data: Candidate data
            detailed: Whether to generate detailed analysis
            
        Returns:
            Career trajectory analysis data
        """
        if not self.gemini_service:
            logger.warning("Gemini service not available for trajectory analysis")
            return self._generate_fallback_analysis(job_data, candidate_data)
            
        try:
            # Extract relevant job information
            job_title = job_data.get("title", "Unknown Position")
            job_description = job_data.get("description", "")
            job_requirements = job_data.get("requirements", "")
            job_company = job_data.get("company", {}).get("name", "Unknown Company")
            job_industry = job_data.get("industry", "Unknown")
            
            # Extract relevant candidate information
            candidate_name = candidate_data.get("name", "Unknown Candidate")
            candidate_skills = candidate_data.get("skills", [])
            candidate_experience = candidate_data.get("experience", "")
            candidate_education = candidate_data.get("education", "")
            candidate_current_role = candidate_data.get("current_role", "")
            
            # Find relevant career path based on job role
            relevant_career_path = {}
            career_path_industry = "software_engineering"  # Default
            
            # Determine industry from job title and description
            if job_industry:
                if "data" in job_industry.lower() or "analytics" in job_industry.lower():
                    career_path_industry = "data_science"
                elif "product" in job_industry.lower():
                    career_path_industry = "product_management"
            
            # Get the relevant career path
            relevant_career_path = self.career_paths.get(career_path_industry, {})
            
            # Create prompt for Gemini
            prompt = f"""
            Analyze the career trajectory and growth potential for this candidate in the specified job.
            
            Job Information:
            - Title: {job_title}
            - Company: {job_company}
            - Industry: {job_industry}
            - Description: {job_description[:500]}...
            - Requirements: {job_requirements[:500]}...
            
            Candidate Information:
            - Name: {candidate_name}
            - Current Role: {candidate_current_role}
            - Skills: {', '.join(candidate_skills[:20])}
            - Experience: {candidate_experience[:500]}...
            - Education: {candidate_education[:300]}...
            
            Career Path Information:
            {json.dumps(relevant_career_path, indent=2)}
            
            Skill Trends:
            - Hot Skills: {', '.join(self.skill_development_data.get('hot_skills', [])[:10])}
            - Emerging Skills: {', '.join(self.skill_development_data.get('emerging_skills', [])[:10])}
            
            Analyze the following aspects:
            1. Growth Potential: Likelihood of career growth in this role (0-100 score)
            2. Career Trajectory Alignment: How well this role aligns with candidate's apparent career path (0-100 score)
            3. Skills Growth Opportunity: Potential for developing valuable skills in this role (0-100 score)
            4. Predicted Future Roles: List of 3-5 potential future roles this position could lead to
            5. Growth Timeline: Estimated years to reach each future role
            6. Development Areas: Skills the candidate should develop for optimal career growth
            
            Respond in JSON format:
            {{"growth_potential_score": float,
              "trajectory_alignment_score": float,
              "skills_growth_opportunity": float,
              "predicted_future_roles": [string],
              "growth_timeline": {{"role": years}},
              "development_areas": [string],
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
                json_pattern = r'{.*}'
                matches = re.search(json_pattern, response, re.DOTALL)
                if matches:
                    try:
                        analysis_data = json.loads(matches.group(0))
                        return analysis_data
                    except json.JSONDecodeError:
                        pass
                
                logger.warning("Failed to parse Gemini response as JSON, using fallback")
                return self._generate_fallback_analysis(job_data, candidate_data)
                
        except Exception as e:
            logger.error(f"Error generating trajectory analysis with Gemini: {e}")
            return self._generate_fallback_analysis(job_data, candidate_data)
    
    def _generate_fallback_analysis(
        self,
        job_data: Dict[str, Any],
        candidate_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate fallback career trajectory analysis when Gemini is unavailable.
        
        Args:
            job_data: Job data
            candidate_data: Candidate data
            
        Returns:
            Basic career trajectory analysis
        """
        # Extract job and candidate information
        job_title = job_data.get("title", "Unknown Position").lower()
        job_description = job_data.get("description", "").lower()
        job_requirements = job_data.get("requirements", "").lower()
        
        candidate_skills = [s.lower() for s in candidate_data.get("skills", [])]
        candidate_experience = candidate_data.get("experience", "").lower()
        
        # Identify industry based on job title and description
        industry = "software_engineering"  # Default
        
        if "data" in job_title or "analytics" in job_title or "ml" in job_title:
            industry = "data_science"
        elif "product" in job_title or "product" in job_description:
            industry = "product_management"
        
        # Get career path for the identified industry
        career_path = self.career_paths.get(industry, {})
        
        # Determine current level based on job title
        current_level = "entry"
        if "senior" in job_title or "lead" in job_title or "principal" in job_title:
            current_level = "senior"
        elif ("junior" not in job_title) and ("associate" not in job_title):
            current_level = "mid"
        
        # Predict future roles based on career path
        future_roles = []
        growth_timeline = {}
        
        # Add roles from the next level
        if current_level == "entry":
            future_roles.extend(career_path.get("mid", [])[:2])
            # Add 1-2 roles from senior level
            future_roles.extend(career_path.get("senior", [])[:1])
            # Set timeline
            for i, role in enumerate(future_roles):
                growth_timeline[role] = (i + 1) * 2  # 2, 4, 6 years
                
        elif current_level == "mid":
            future_roles.extend(career_path.get("senior", [])[:2])
            # Add 1 role from leadership
            future_roles.extend(career_path.get("leadership", [])[:1])
            # Set timeline
            for i, role in enumerate(future_roles):
                growth_timeline[role] = (i + 1) * 2  # 2, 4, 6 years
                
        elif current_level == "senior":
            future_roles.extend(career_path.get("leadership", [])[:3])
            # Set timeline
            for i, role in enumerate(future_roles):
                growth_timeline[role] = (i + 1) * 2  # 2, 4, 6 years
        
        # Calculate growth potential score (default to moderate)
        growth_potential = 65.0
        
        # Adjust based on industry growth
        hot_industries = ["ai", "machine learning", "cloud", "security", "data"]
        for industry_keyword in hot_industries:
            if industry_keyword in job_title or industry_keyword in job_description:
                growth_potential += 10
                break
                
        # Cap at 100
        growth_potential = min(growth_potential, 100.0)
        
        # Calculate trajectory alignment score
        trajectory_alignment = 70.0  # Default moderate alignment
        
        # Calculate skills growth opportunity
        skill_growth = 75.0  # Default good opportunity
        
        # Identify development areas
        development_areas = []
        
        # Check for hot skills missing from candidate profile
        for hot_skill in self.skill_development_data.get("hot_skills", []):
            if hot_skill.lower() not in candidate_skills and (
                hot_skill.lower() in job_description or hot_skill.lower() in job_requirements
            ):
                development_areas.append(hot_skill)
        
        # Add some emerging skills
        for emerging_skill in self.skill_development_data.get("emerging_skills", [])[:3]:
            if emerging_skill.lower() not in candidate_skills:
                development_areas.append(emerging_skill)
        
        # Limit to 5 development areas
        development_areas = development_areas[:5]
        
        # Generate basic analysis text
        detailed_analysis = f"""
        # Career Trajectory Analysis
        
        ## Growth Potential: {growth_potential:.1f}%
        
        The role offers {'significant' if growth_potential >= 75 else 'moderate'} potential for career advancement.
        
        ## Predicted Career Path
        
        Based on industry trends and the nature of the position, this role could lead to:
        {', '.join([f"{role} (in {growth_timeline.get(role, 'unknown')} years)" for role in future_roles])}
        
        ## Development Recommendations
        
        To maximize growth potential, focus on developing these skills:
        {', '.join(development_areas)}
        
        ## Note
        This is a basic analysis based on limited information. For a more comprehensive assessment,
        additional data about industry trends and company-specific growth paths would be beneficial.
        """
        
        return {
            "growth_potential_score": growth_potential,
            "trajectory_alignment_score": trajectory_alignment,
            "skills_growth_opportunity": skill_growth,
            "predicted_future_roles": future_roles,
            "growth_timeline": growth_timeline,
            "development_areas": development_areas,
            "detailed_analysis": detailed_analysis
        }
