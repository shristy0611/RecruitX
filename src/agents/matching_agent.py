"""
Matching Agent for RecruitPro AI.

This agent implements advanced job-candidate matching using RAG (Retrieval-Augmented Generation)
to provide explainable and transparent matching results.
"""
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
from sentence_transformers import SentenceTransformer

from src.knowledge_base.vector_store import VectorStore
from src.orchestration.agent import Agent, Message, MessageType, MessagePriority
from src.utils.config import WEAVIATE_URL, EMBEDDING_MODEL
from src.agents.sourcing_agent import SourcingAgent, SourcingParams, CandidateProfile
from src.xai.matching_explainer import MatchingExplainer

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MatchingResult:
    """Result of a job-candidate matching operation."""
    candidate_id: str
    job_id: str
    overall_score: float
    skill_match_score: float
    experience_match_score: float
    education_match_score: float
    explanation: str
    matching_id: str = ""
    skills_matched: List[str] = field(default_factory=list)
    skills_missing: List[str] = field(default_factory=list)
    timestamp: float = 0.0


@dataclass
class MatchingParams:
    """Parameters for job-candidate matching."""
    job_id: str
    candidate_ids: List[str] = field(default_factory=list)
    min_score: float = 60.0
    weights: Dict[str, float] = field(default_factory=lambda: {
        "skills": 0.5,
        "experience": 0.3,
        "education": 0.2
    })
    require_explanation: bool = True
    max_results: int = 10


class MatchingAgent(Agent):
    """
    Agent for advanced job-candidate matching with explainable results.
    
    This agent:
    1. Matches candidates to jobs using a hybrid approach
    2. Produces detailed explanations for matching decisions
    3. Integrates with SourcingAgent for candidate discovery
    """
    
    def __init__(
        self, 
        agent_id: str = "matching_agent",
        vector_store: Optional[VectorStore] = None,
        sourcing_agent: Optional[SourcingAgent] = None
    ):
        """
        Initialize the matching agent.
        
        Args:
            agent_id: Unique ID for this agent
            vector_store: Optional pre-configured VectorStore
            sourcing_agent: Optional pre-configured SourcingAgent
        """
        super().__init__(
            agent_id=agent_id,
            name="Matching Agent",
            description="Provides advanced job-candidate matching with explainable results",
            capabilities=[
                "advanced_matching",
                "explainable_results",
                "skill_analysis"
            ]
        )
        
        # Initialize components
        self.vector_store = vector_store or VectorStore(url=WEAVIATE_URL)
        self.sourcing_agent = sourcing_agent or SourcingAgent()
        
        # Initialize embeddings model
        try:
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info(f"Initialized embedding model: {EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            self.embedding_model = None
        
        # Track ongoing matching operations
        self.active_matching: Dict[str, Dict[str, Any]] = {}
        
        # Initialize XAI explainer
        self.explainer = MatchingExplainer()
    
    def initialize(self) -> None:
        """Initialize the agent."""
        logger.info("Initializing MatchingAgent")
        # Nothing special needed for initialization
    
    def handle_command(self, message: Message) -> None:
        """
        Handle command messages.
        
        Args:
            message: Command message
        """
        command = message.content.get("command")
        logger.info(f"MatchingAgent received command: {command}")
        
        if command == "match_candidates":
            self._handle_match_candidates(message)
        elif command == "get_matching_results":
            self._handle_get_matching_results(message)
        elif command == "get_match_explanation":
            self._handle_get_match_explanation(message)
        else:
            self._send_error_response(
                message,
                f"Unknown command: {command}"
            )
    
    def _handle_match_candidates(self, message: Message) -> None:
        """
        Handle a candidate matching request.
        
        Args:
            message: Message containing matching request
        """
        try:
            # Extract parameters
            job_id = message.content.get("job_id")
            candidate_ids = message.content.get("candidate_ids", [])
            params = message.content.get("params", {})
            
            if not job_id:
                self._send_error_response(
                    message,
                    "Missing required parameter: job_id"
                )
                return
            
            # Create matching parameters
            matching_params = MatchingParams(
                job_id=job_id,
                candidate_ids=candidate_ids,
                min_score=params.get("min_score", 60.0),
                weights=params.get("weights", {
                    "skills": 0.5,
                    "experience": 0.3,
                    "education": 0.2
                }),
                require_explanation=params.get("require_explanation", True),
                max_results=params.get("max_results", 10)
            )
            
            # Generate a unique matching ID
            matching_id = str(uuid.uuid4())
            
            # Store in active matching
            self.active_matching[matching_id] = {
                "params": asdict(matching_params),
                "status": "processing",
                "start_time": time.time(),
                "message_id": message.message_id
            }
            
            # If no candidate IDs provided, use SourcingAgent to find candidates
            if not candidate_ids:
                logger.info(f"No candidate IDs provided, sourcing candidates for job {job_id}")
                
                # Create basic sourcing parameters
                sourcing_params = SourcingParams(
                    job_id=job_id,
                    max_results=matching_params.max_results * 2  # Get more candidates than needed
                )
                
                # Source candidates
                candidates = self.sourcing_agent.source_candidates(sourcing_params)
                
                # Extract candidate IDs
                candidate_ids = [candidate.id for candidate in candidates]
                
                if not candidate_ids:
                    self._send_error_response(
                        message,
                        "No candidates found for the specified job"
                    )
                    return
            
            # Match candidates to job
            logger.info(f"Matching {len(candidate_ids)} candidates to job {job_id}")
            
            results = self.match_candidates(
                job_id=job_id,
                candidate_ids=candidate_ids,
                min_score=matching_params.min_score,
                weights=matching_params.weights,
                require_explanation=matching_params.require_explanation
            )
            
            # Update matching status
            self.active_matching[matching_id]["status"] = "completed"
            self.active_matching[matching_id]["results"] = [asdict(result) for result in results]
            self.active_matching[matching_id]["end_time"] = time.time()
            
            # Send success response
            self._send_simple_response(
                message,
                f"Matched {len(results)} candidates to job",
                {
                    "matching_id": matching_id,
                    "job_id": job_id,
                    "candidates": [
                        {
                            "id": result.candidate_id,
                            "overall_score": result.overall_score,
                            "skill_match_score": result.skill_match_score,
                            "experience_match_score": result.experience_match_score,
                            "education_match_score": result.education_match_score,
                            "skills_matched": result.skills_matched[:5],  # Limit to first 5 skills
                        }
                        for result in results
                    ],
                    "count": len(results)
                }
            )
        
        except Exception as e:
            logger.error(f"Error matching candidates: {e}")
            self._send_error_response(
                message,
                f"Error matching candidates: {str(e)}"
            )
    
    def _handle_get_matching_results(self, message: Message) -> None:
        """
        Handle a request for matching results.
        
        Args:
            message: Message containing matching results request
        """
        matching_id = message.content.get("matching_id")
        
        if not matching_id:
            self._send_error_response(
                message,
                "Missing required parameter: matching_id"
            )
            return
        
        if matching_id not in self.active_matching:
            self._send_error_response(
                message,
                f"Matching ID not found: {matching_id}"
            )
            return
        
        matching_data = self.active_matching[matching_id]
        
        # Prepare response data
        response_data = {
            "matching_id": matching_id,
            "status": matching_data["status"],
            "start_time": matching_data["start_time"],
            "params": matching_data["params"]
        }
        
        if matching_data["status"] == "completed":
            response_data["end_time"] = matching_data.get("end_time")
            response_data["results"] = matching_data.get("results", [])
            response_data["count"] = len(matching_data.get("results", []))
        
        self._send_simple_response(
            message,
            f"Matching status: {matching_data['status']}",
            response_data
        )
    
    def _handle_get_match_explanation(self, message: Message) -> None:
        """
        Handle a request for match explanation.
        
        Args:
            message: Message containing match explanation request
        """
        try:
            matching_id = message.content.get("matching_id")
            candidate_id = message.content.get("candidate_id")
            
            if not matching_id or not candidate_id:
                self._send_error_response(
                    message,
                    "Missing required parameters: matching_id and candidate_id"
                )
                return
            
            if matching_id not in self.active_matching:
                self._send_error_response(
                    message,
                    f"Matching ID not found: {matching_id}"
                )
                return
            
            matching_data = self.active_matching[matching_id]
            
            if matching_data["status"] != "completed":
                self._send_error_response(
                    message,
                    f"Matching operation not completed: {matching_id}"
                )
                return
            
            # Find matching result for the specified candidate
            results = matching_data.get("results", [])
            result = next((r for r in results if r["candidate_id"] == candidate_id), None)
            
            if not result:
                self._send_error_response(
                    message,
                    f"No matching result found for candidate: {candidate_id}"
                )
                return
            
            # Get candidate and job details
            candidate_data = self.vector_store.get_by_id("CandidateProfile", candidate_id)
            job_data = self.vector_store.get_by_id("JobDescription", matching_data["params"]["job_id"])
            
            if not candidate_data or not job_data:
                self._send_error_response(
                    message,
                    "Failed to retrieve candidate or job details"
                )
                return
            
            # Send detailed explanation
            self._send_simple_response(
                message,
                "Match explanation retrieved",
                {
                    "matching_id": matching_id,
                    "candidate_id": candidate_id,
                    "candidate_name": candidate_data.get("name", "Unknown"),
                    "job_title": job_data.get("title", "Unknown"),
                    "overall_score": result["overall_score"],
                    "skill_match_score": result["skill_match_score"],
                    "experience_match_score": result["experience_match_score"],
                    "education_match_score": result["education_match_score"],
                    "skills_matched": result["skills_matched"],
                    "skills_missing": result["skills_missing"],
                    "explanation": result["explanation"]
                }
            )
        
        except Exception as e:
            logger.error(f"Error retrieving match explanation: {e}")
            self._send_error_response(
                message,
                f"Error retrieving match explanation: {str(e)}"
            )
    
    def match_candidates(
        self,
        job_id: str,
        candidate_ids: List[str],
        min_score: float = 60.0,
        weights: Dict[str, float] = None,
        require_explanation: bool = True
    ) -> List[MatchingResult]:
        """
        Match candidates to a job with detailed scoring and explanations.
        
        Args:
            job_id: ID of the job
            candidate_ids: List of candidate IDs to match
            min_score: Minimum overall score required
            weights: Weight of each factor in the overall score
            require_explanation: Whether to generate explanations
            
        Returns:
            List of matching results
        """
        try:
            # Set default weights if not provided
            if weights is None:
                weights = {
                    "skills": 0.5,
                    "experience": 0.3,
                    "education": 0.2
                }
            
            # Get job data
            job_data = self.vector_store.get_by_id("JobDescription", job_id)
            
            if not job_data:
                logger.error(f"Job not found: {job_id}")
                return []
            
            # Extract job requirements
            job_title = job_data.get("title", "")
            job_description = job_data.get("description", "")
            job_requirements = job_data.get("requirements", "")
            
            # Extract skills from requirements
            required_skills = self._extract_skills(job_requirements)
            logger.info(f"Extracted {len(required_skills)} required skills: {required_skills}")
            
            # Match each candidate
            results = []
            
            for candidate_id in candidate_ids:
                # Get candidate data
                candidate_data = self.vector_store.get_by_id("CandidateProfile", candidate_id)
                
                if not candidate_data:
                    logger.warning(f"Candidate not found: {candidate_id}")
                    continue
                
                # Extract candidate information
                candidate_name = candidate_data.get("name", "Unknown")
                candidate_skills = candidate_data.get("skills", [])
                candidate_experience = candidate_data.get("experience", "")
                candidate_education = candidate_data.get("education", "")
                
                # Calculate skill match score
                skill_match_score, skills_matched, skills_missing = self._calculate_skill_match(
                    required_skills, candidate_skills
                )
                
                # Calculate experience match score
                experience_match_score = self._calculate_experience_match(
                    job_title, job_requirements, candidate_experience
                )
                
                # Calculate education match score
                education_match_score = self._calculate_education_match(
                    job_requirements, candidate_education
                )
                
                # Calculate overall score
                overall_score = (
                    skill_match_score * weights.get("skills", 0.5) +
                    experience_match_score * weights.get("experience", 0.3) +
                    education_match_score * weights.get("education", 0.2)
                )
                
                # Apply minimum score filter
                if overall_score < min_score:
                    continue
                
                # Generate explanation if required
                explanation = ""
                if require_explanation:
                    explanation = self._generate_match_explanation(
                        job_data=job_data,
                        candidate_data=candidate_data,
                        skill_match_score=skill_match_score,
                        experience_match_score=experience_match_score,
                        education_match_score=education_match_score,
                        overall_score=overall_score,
                        skills_matched=skills_matched,
                        skills_missing=skills_missing
                    )
                
                # Create matching result
                result = MatchingResult(
                    candidate_id=candidate_id,
                    job_id=job_id,
                    overall_score=overall_score,
                    skill_match_score=skill_match_score,
                    experience_match_score=experience_match_score,
                    education_match_score=education_match_score,
                    skills_matched=skills_matched,
                    skills_missing=skills_missing,
                    explanation=explanation,
                    matching_id=str(uuid.uuid4()),
                    timestamp=time.time()
                )
                
                results.append(result)
            
            # Sort results by overall score (descending)
            results.sort(key=lambda x: x.overall_score, reverse=True)
            
            logger.info(f"Matched {len(results)} candidates to job {job_id}")
            return results
        
        except Exception as e:
            logger.error(f"Error in match_candidates: {e}")
            return []
    
    def _extract_skills(self, text: str) -> List[str]:
        """
        Extract skills from text.
        
        Args:
            text: Text to extract skills from
            
        Returns:
            List of extracted skills
        """
        # Common technical skills to look for
        common_skills = [
            "python", "r", "java", "javascript", "c++", "c#", "ruby", "go", "rust",
            "sql", "mysql", "postgresql", "mongodb", "oracle", "cassandra",
            "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
            "hadoop", "spark", "kafka", "airflow", "nlp", "machine learning",
            "deep learning", "ai", "statistics", "data science", "data analysis",
            "data visualization", "tableau", "power bi", "excel", "html", "css",
            "react", "angular", "vue", "node.js", "flask", "django", "spring",
            "git", "ci/cd", "jenkins", "agile", "scrum", "jira", "confluence"
        ]
        
        # Extract skills from text
        skills = []
        text_lower = text.lower()
        
        # Look for common skills in the text
        for skill in common_skills:
            if skill in text_lower:
                # Check if it's a standalone word or part of a phrase
                # This helps prevent partial matches (e.g. 'go' in 'google')
                if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                    skills.append(skill.capitalize())
        
        # Extract potential skills from bullet points
        lines = text.split("\n")
        for line in lines:
            line = line.strip().lower()
            if line.startswith("-") or line.startswith("*"):
                # Extract the content after the bullet
                content = line.strip("- *").strip()
                
                # Look for technical terms in parentheses - often skills
                if "(" in content and ")" in content:
                    matches = re.findall(r'\(([^)]+)\)', content)
                    for match in matches:
                        # Split by commas or spaces if multiple items in parentheses
                        items = re.split(r'[,\s]+', match)
                        for item in items:
                            item = item.strip()
                            if item and len(item) > 1 and item not in skills:
                                skills.append(item.capitalize())
                
                # Check for standalone technical terms
                words = content.split()
                for word in words:
                    word = word.strip().strip(',.;:')
                    if word in common_skills and word.capitalize() not in skills:
                        skills.append(word.capitalize())
        
        # Deduplicate and sort
        skills = list(set(skills))
        skills.sort()
        
        return skills
    
    def _calculate_skill_match(
        self, 
        required_skills: List[str], 
        candidate_skills: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate skill match score and identify matched/missing skills.
        
        Args:
            required_skills: Skills required for the job
            candidate_skills: Skills possessed by the candidate
            
        Returns:
            Skill match score (0-100), matched skills, missing skills
        """
        if not required_skills:
            return 100.0, candidate_skills, []
        
        # Normalize skills for comparison
        normalized_required = [s.lower() for s in required_skills]
        normalized_candidate = [s.lower() for s in candidate_skills]
        
        # Find matched skills
        matched_skills = []
        for skill in candidate_skills:
            if skill.lower() in normalized_required:
                matched_skills.append(skill)
        
        # Find missing skills
        missing_skills = []
        for skill in required_skills:
            if skill.lower() not in normalized_candidate:
                missing_skills.append(skill)
        
        # Calculate score
        match_score = len(matched_skills) / len(required_skills) * 100
        
        return match_score, matched_skills, missing_skills
    
    def _calculate_experience_match(
        self, 
        job_title: str, 
        job_requirements: str, 
        candidate_experience: str
    ) -> float:
        """
        Calculate experience match score.
        
        Args:
            job_title: Job title
            job_requirements: Job requirements
            candidate_experience: Candidate's work experience
            
        Returns:
            Experience match score (0-100)
        """
        if not candidate_experience:
            return 0.0
        
        # Simple keyword-based scoring
        # In a real system, we'd use NLP and semantic matching
        
        # Extract key terms from job title and requirements
        key_terms = []
        if job_title:
            key_terms.extend(job_title.lower().split())
        
        if job_requirements:
            # Extract years of experience requirement
            years_required = 0
            for line in job_requirements.split("\n"):
                if "year" in line.lower() and any(c.isdigit() for c in line):
                    for word in line.split():
                        if word.isdigit() or (word[0].isdigit() and word[1] == "+"):
                            try:
                                if "+" in word:
                                    years_required = int(word.replace("+", ""))
                                else:
                                    years_required = int(word)
                                break
                            except ValueError:
                                pass
            
            # Extract other key terms
            for line in job_requirements.split("\n"):
                if "experience" in line.lower() or "work" in line.lower():
                    key_terms.extend([word.lower() for word in line.split() if len(word) > 3])
        
        # Count matches in candidate experience
        matches = 0
        for term in key_terms:
            if term.lower() in candidate_experience.lower():
                matches += 1
        
        # Calculate base score from keyword matches
        if not key_terms:
            base_score = 50.0  # Default if no key terms found
        else:
            base_score = min(matches / len(key_terms) * 100, 100.0)
        
        # Check years of experience (simple heuristic)
        years_mentioned = []
        for word in candidate_experience.split():
            if word.isdigit() and int(word) <= 30:  # Likely years
                years_mentioned.append(int(word))
        
        experience_bonus = 0.0
        if years_required > 0 and years_mentioned:
            if max(years_mentioned) >= years_required:
                experience_bonus = 20.0
            else:
                # Partial credit
                experience_bonus = (max(years_mentioned) / years_required) * 20.0
        
        # Calculate final score with bonus
        final_score = min(base_score + experience_bonus, 100.0)
        
        return final_score
    
    def _calculate_education_match(
        self, 
        job_requirements: str, 
        candidate_education: str
    ) -> float:
        """
        Calculate education match score.
        
        Args:
            job_requirements: Job requirements
            candidate_education: Candidate's education
            
        Returns:
            Education match score (0-100)
        """
        if not candidate_education:
            return 0.0
        
        # Education level mapping (higher is better)
        education_levels = {
            "high school": 1,
            "associate": 2,
            "bachelor": 3,
            "master": 4,
            "phd": 5,
            "doctorate": 5,
            "mba": 4,
            "bs": 3,
            "ba": 3,
            "ms": 4,
            "ma": 4,
        }
        
        # Extract required education level
        required_level = 0
        for level, value in education_levels.items():
            if level in job_requirements.lower():
                required_level = max(required_level, value)
        
        # Default to bachelor's if no specific requirement found
        if required_level == 0:
            required_level = 3
        
        # Extract candidate's education level
        candidate_level = 0
        for level, value in education_levels.items():
            if level in candidate_education.lower():
                candidate_level = max(candidate_level, value)
        
        # Calculate score based on education level match
        if candidate_level >= required_level:
            level_score = 100.0
        else:
            level_score = (candidate_level / required_level) * 100.0
        
        # Check for relevant fields (simple keyword matching)
        field_score = 0.0
        relevant_fields = [
            "computer science", "cs", "software", "information technology", 
            "it", "data science", "engineering", "mathematics", "math",
            "statistics", "business"
        ]
        
        for field in relevant_fields:
            if field in job_requirements.lower() and field in candidate_education.lower():
                field_score = 100.0
                break
        
        # Combine scores (weighted)
        final_score = level_score * 0.7 + field_score * 0.3
        
        return final_score
    
    def _generate_match_explanation(
        self,
        job_data: Dict[str, Any],
        candidate_data: Dict[str, Any],
        skill_match_score: float,
        experience_match_score: float,
        education_match_score: float,
        overall_score: float,
        skills_matched: List[str],
        skills_missing: List[str],
        detail_level: str = "standard"
    ) -> str:
        """
        Generate a human-readable explanation of the matching result using LLM services.
        
        Args:
            job_data: Job data
            candidate_data: Candidate data
            skill_match_score: Skill match score
            experience_match_score: Experience match score
            education_match_score: Education match score
            overall_score: Overall match score
            skills_matched: Skills matched
            skills_missing: Skills missing
            detail_level: Level of detail for the explanation ("brief", "standard", "detailed")
            
        Returns:
            Explanation text
        """
        try:
            # Create context for the explainer
            context = {
                "candidate_profile": candidate_data,
                "job_description": job_data,
                "match_result": {
                    "overall_score": overall_score,
                    "factors": {
                        "skills_score": skill_match_score,
                        "experience_score": experience_match_score,
                        "education_score": education_match_score
                    },
                    "matched_skills": skills_matched,
                    "missing_skills": skills_missing
                }
            }
            
            # Generate explanation using the XAI explainer
            explanation_data = self.explainer.generate_explanation(
                context=context,
                detail_level=detail_level
            )
            
            # Return the main explanation text
            return explanation_data["explanation"]
            
        except Exception as e:
            logger.error(f"Error generating explanation with XAI module: {e}")
            
            # Fallback to template-based explanation
            job_title = job_data.get("title", "the position")
            candidate_name = candidate_data.get("name", "The candidate")
            
            # Format scores
            skill_score_formatted = f"{skill_match_score:.1f}%"
            experience_score_formatted = f"{experience_match_score:.1f}%"
            education_score_formatted = f"{education_match_score:.1f}%"
            overall_score_formatted = f"{overall_score:.1f}%"
            
            # Create basic explanation
            explanation = (
                f"## Match Analysis for {candidate_name}\n\n"
                f"### Overall Match: {overall_score_formatted}\n\n"
                f"{candidate_name} has an overall match score of {overall_score_formatted} for {job_title}.\n\n"
                
                f"### Skills Match: {skill_score_formatted}\n"
            )
            
            # Skills breakdown
            if skills_matched:
                explanation += f"**Matching Skills:** {', '.join(skills_matched)}\n\n"
            else:
                explanation += "**No directly matching skills were found.**\n\n"
            
            if skills_missing:
                explanation += f"**Missing Skills:** {', '.join(skills_missing)}\n\n"
            
            # Experience analysis
            explanation += (
                f"### Experience Match: {experience_score_formatted}\n"
                f"The candidate's experience aligns with {experience_score_formatted} of the job requirements.\n\n"
            )
            
            # Education analysis
            explanation += (
                f"### Education Match: {education_score_formatted}\n"
                f"The candidate's education background matches {education_score_formatted} of the job requirements.\n\n"
            )
            
            # Recommendation
            if overall_score >= 80:
                explanation += "**Recommendation:** Strong match - Recommended for interview"
            elif overall_score >= 70:
                explanation += "**Recommendation:** Good match - Consider for interview"
            elif overall_score >= 60:
                explanation += "**Recommendation:** Moderate match - Potential fit with some gaps"
            else:
                explanation += "**Recommendation:** Low match - Significant gaps exist"
            
            return explanation
            
    def get_detailed_explanation(
        self,
        job_id: str,
        candidate_id: str,
        detail_level: str = "detailed"
    ) -> Dict[str, Any]:
        """
        Get a detailed explanation of a match with all factors and insights.
        
        Args:
            job_id: ID of the job
            candidate_id: ID of the candidate
            detail_level: Level of detail ("brief", "standard", "detailed")
            
        Returns:
            Dictionary with detailed explanation and metadata
        """
        # Retrieve job and candidate data
        job_data = self.vector_store.get_by_id(job_id)
        candidate_data = self.vector_store.get_by_id(candidate_id)
        
        if not job_data or not candidate_data:
            raise ValueError(f"Job or candidate not found: {job_id} / {candidate_id}")
        
        # Calculate match scores
        required_skills = self._extract_skills(job_data.get("description", ""))
        candidate_skills = self._extract_skills(candidate_data.get("resume", ""))
        
        skill_match_score, skills_matched, skills_missing = self._calculate_skill_match(
            required_skills,
            candidate_skills
        )
        
        experience_match_score = self._calculate_experience_match(
            job_data.get("title", ""),
            job_data.get("description", ""), 
            candidate_data.get("experience", "")
        )
        
        education_match_score = self._calculate_education_match(
            job_data.get("description", ""),
            candidate_data.get("education", "")
        )
        
        # Calculate overall score with default weights
        weights = {
            "skills": 0.5,
            "experience": 0.3,
            "education": 0.2
        }
        
        overall_score = (
            skill_match_score * weights["skills"] +
            experience_match_score * weights["experience"] +
            education_match_score * weights["education"]
        )
        
        # Create context for the explainer
        context = {
            "candidate_profile": candidate_data,
            "job_description": job_data,
            "match_result": {
                "overall_score": overall_score,
                "factors": {
                    "skills_score": skill_match_score,
                    "experience_score": experience_match_score,
                    "education_score": education_match_score
                },
                "matched_skills": skills_matched,
                "missing_skills": skills_missing
            }
        }
        
        # Generate detailed explanation
        try:
            explanation_data = self.explainer.generate_explanation(
                context=context,
                detail_level=detail_level
            )
            return explanation_data
        except Exception as e:
            logger.error(f"Error generating detailed explanation: {e}")
            # Return basic explanation format as fallback
            return {
                "score": overall_score,
                "explanation": self._generate_match_explanation(
                    job_data, 
                    candidate_data,
                    skill_match_score,
                    experience_match_score,
                    education_match_score,
                    overall_score,
                    skills_matched,
                    skills_missing,
                    "standard"
                ),
                "factors": {
                    "skills_score": skill_match_score,
                    "experience_score": experience_match_score,
                    "education_score": education_match_score
                }
            }
    
    def cleanup(self) -> None:
        """Clean up resources."""
        # Clean up old matching operations (older than 24 hours)
        current_time = time.time()
        to_remove = []
        
        for matching_id, matching_data in self.active_matching.items():
            if current_time - matching_data.get("start_time", 0) > 86400:  # 24 hours
                to_remove.append(matching_id)
        
        for matching_id in to_remove:
            del self.active_matching[matching_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old matching operations")
