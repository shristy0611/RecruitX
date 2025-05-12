"""
Sourcing Agent for RecruitPro AI.

This agent is responsible for discovering and retrieving candidate profiles
from the internal applicant tracking system (ATS) using privacy-first techniques.
It leverages semantic search and RAG to efficiently find suitable candidates.
"""
import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
from sentence_transformers import SentenceTransformer

from src.knowledge_base.vector_store import VectorStore
from src.orchestration.agent import Agent, Message, MessageType, MessagePriority
from src.utils.config import WEAVIATE_URL, EMBEDDING_MODEL

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class SourcingParams:
    """Parameters for candidate sourcing."""
    job_id: str
    keywords: List[str] = None
    min_skills_match: int = 3
    min_experience_years: float = 0
    education_level: str = ""
    location: str = ""
    max_results: int = 10
    similarity_threshold: float = 0.6


@dataclass
class CandidateProfile:
    """Candidate profile data."""
    id: str
    name: str
    skills: List[str]
    score: float
    email: str = ""
    phone: str = ""
    education: List[str] = None
    experience: List[Dict[str, Any]] = None
    resume_text: str = ""
    summary: str = ""
    location: str = ""
    timestamp: float = 0.0


class SourcingAgent(Agent):
    """
    Agent for discovering and retrieving candidate profiles.
    
    This agent:
    1. Searches the knowledge base for candidate profiles
    2. Ranks and filters candidates based on job requirements
    3. Provides detailed candidate information with matching scores
    """
    
    def __init__(
        self, 
        agent_id: str = "sourcing_agent",
        vector_store: Optional[VectorStore] = None
    ):
        """
        Initialize the sourcing agent.
        
        Args:
            agent_id: Unique ID for this agent
            vector_store: Optional pre-configured VectorStore
        """
        super().__init__(
            agent_id=agent_id,
            name="Sourcing Agent",
            description="Discovers and retrieves candidate profiles",
            capabilities=[
                "candidate_sourcing",
                "semantic_search",
                "profile_matching"
            ]
        )
        
        # Initialize components
        self.vector_store = vector_store or VectorStore(url=WEAVIATE_URL)
        
        # Initialize embeddings model
        try:
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info(f"Initialized embedding model: {EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            self.embedding_model = None
        
        # Track ongoing sourcing operations
        self.active_sourcing: Dict[str, Dict[str, Any]] = {}
    
    def initialize(self) -> None:
        """Initialize the agent."""
        logger.info("Initializing SourcingAgent")
        # Nothing special needed for initialization
    
    def handle_command(self, message: Message) -> None:
        """
        Handle command messages.
        
        Args:
            message: Command message
        """
        command = message.content.get("command")
        logger.info(f"SourcingAgent received command: {command}")
        
        if command == "source_candidates":
            self._handle_source_candidates(message)
        elif command == "get_sourcing_status":
            self._handle_get_sourcing_status(message)
        elif command == "get_candidate_details":
            self._handle_get_candidate_details(message)
        else:
            self._send_error_response(
                message,
                f"Unknown command: {command}"
            )
    
    def _handle_source_candidates(self, message: Message) -> None:
        """
        Handle a candidate sourcing request.
        
        Args:
            message: Message containing sourcing request
        """
        try:
            # Extract parameters
            job_id = message.content.get("job_id")
            params = message.content.get("params", {})
            
            if not job_id:
                self._send_error_response(
                    message,
                    "Missing required parameter: job_id"
                )
                return
            
            # Create sourcing parameters
            sourcing_params = SourcingParams(
                job_id=job_id,
                keywords=params.get("keywords", []),
                min_skills_match=params.get("min_skills_match", 3),
                min_experience_years=params.get("min_experience_years", 0),
                education_level=params.get("education_level", ""),
                location=params.get("location", ""),
                max_results=params.get("max_results", 10),
                similarity_threshold=params.get("similarity_threshold", 0.6)
            )
            
            # Generate a unique sourcing ID
            sourcing_id = str(uuid.uuid4())
            
            # Store in active sourcing
            self.active_sourcing[sourcing_id] = {
                "params": asdict(sourcing_params),
                "status": "processing",
                "start_time": time.time(),
                "message_id": message.message_id
            }
            
            # Start sourcing in a separate thread
            # For the simple implementation, we'll do it synchronously
            logger.info(f"Sourcing candidates for job {job_id}, sourcing ID: {sourcing_id}")
            results = self.source_candidates(sourcing_params)
            
            # Update sourcing status
            self.active_sourcing[sourcing_id]["status"] = "completed"
            self.active_sourcing[sourcing_id]["results"] = results
            self.active_sourcing[sourcing_id]["end_time"] = time.time()
            
            # Send success response
            self._send_simple_response(
                message,
                f"Found {len(results)} matching candidates",
                {
                    "sourcing_id": sourcing_id,
                    "candidates": [
                        {
                            "id": candidate.id,
                            "name": candidate.name,
                            "score": candidate.score,
                            "skills": candidate.skills[:10],  # Limit to first 10 skills
                            "education": candidate.education[:2] if candidate.education else [],  # Limit to top 2
                        }
                        for candidate in results
                    ],
                    "count": len(results)
                }
            )
        
        except Exception as e:
            logger.error(f"Error sourcing candidates: {e}")
            self._send_error_response(
                message,
                f"Error sourcing candidates: {str(e)}"
            )
    
    def _handle_get_sourcing_status(self, message: Message) -> None:
        """
        Handle a request for sourcing status.
        
        Args:
            message: Message containing sourcing status request
        """
        sourcing_id = message.content.get("sourcing_id")
        
        if not sourcing_id:
            self._send_error_response(
                message,
                "Missing required parameter: sourcing_id"
            )
            return
        
        if sourcing_id not in self.active_sourcing:
            self._send_error_response(
                message,
                f"Sourcing ID not found: {sourcing_id}"
            )
            return
        
        sourcing_data = self.active_sourcing[sourcing_id]
        
        # Prepare response data
        response_data = {
            "sourcing_id": sourcing_id,
            "status": sourcing_data["status"],
            "start_time": sourcing_data["start_time"],
            "params": sourcing_data["params"]
        }
        
        if sourcing_data["status"] == "completed":
            response_data["end_time"] = sourcing_data.get("end_time")
            response_data["count"] = len(sourcing_data.get("results", []))
        
        self._send_simple_response(
            message,
            f"Sourcing status: {sourcing_data['status']}",
            response_data
        )
    
    def _handle_get_candidate_details(self, message: Message) -> None:
        """
        Handle a request for detailed candidate information.
        
        Args:
            message: Message containing candidate details request
        """
        try:
            candidate_id = message.content.get("candidate_id")
            
            if not candidate_id:
                self._send_error_response(
                    message,
                    "Missing required parameter: candidate_id"
                )
                return
            
            # Get candidate from vector store
            candidate_data = self.vector_store.get_by_id("CandidateProfile", candidate_id)
            
            if not candidate_data:
                self._send_error_response(
                    message,
                    f"Candidate not found: {candidate_id}"
                )
                return
            
            # Send detailed candidate information
            self._send_simple_response(
                message,
                "Candidate details retrieved",
                {"candidate_data": candidate_data}
            )
        
        except Exception as e:
            logger.error(f"Error retrieving candidate details: {e}")
            self._send_error_response(
                message,
                f"Error retrieving candidate details: {str(e)}"
            )
    
    def source_candidates(self, params: SourcingParams) -> List[CandidateProfile]:
        """
        Source candidates based on job requirements.
        
        This is a synchronous implementation of candidate sourcing.
        
        Args:
            params: Sourcing parameters
            
        Returns:
            List of matching candidate profiles
        """
        try:
            # Get job data
            job_data = self.vector_store.get_by_id("JobDescription", params.job_id)
            
            if not job_data:
                logger.error(f"Job not found: {params.job_id}")
                return []
            
            # Create search query
            search_terms = []
            
            # Add job title
            if "title" in job_data:
                search_terms.append(job_data["title"])
            
            # Add specific keywords if provided
            if params.keywords:
                search_terms.extend(params.keywords)
            
            # Extract skills from requirements if available
            if "requirements" in job_data:
                # Simple skill extraction - in a real system we'd use NLP
                skills = self._extract_skills_from_text(job_data["requirements"])
                search_terms.extend(skills)
            
            # Combine terms into a single query
            search_query = " ".join(search_terms)
            logger.info(f"Searching for candidates with query: {search_query}")
            
            # Perform semantic search
            limit = max(params.max_results * 2, 20)  # Get more results for filtering
            results = self.vector_store.search(
                class_name="CandidateProfile",
                query=search_query,
                limit=limit
            )
            
            if not results:
                logger.info("No candidates found")
                return []
            
            # Convert to CandidateProfile objects
            candidates = []
            for item in results:
                try:
                    # Extract skills
                    skills = item.get("skills", [])
                    if isinstance(skills, str):
                        skills = skills.split(",")
                    
                    # Create candidate profile
                    candidate = CandidateProfile(
                        id=item.get("_additional", {}).get("id", ""),
                        name=item.get("name", "Unknown"),
                        skills=skills,
                        score=item.get("_additional", {}).get("certainty", 0) * 100,
                        email=item.get("email", ""),
                        phone=item.get("phone", ""),
                        education=item.get("education", []),
                        experience=item.get("experience", []),
                        resume_text=item.get("resume_text", ""),
                        location=item.get("location", ""),
                        timestamp=item.get("timestamp", 0)
                    )
                    

                    
                    # Apply filters
                    if self._apply_candidate_filters(candidate, params):
                        candidates.append(candidate)
                
                except Exception as e:
                    logger.error(f"Error processing candidate: {e}")
            
            # Sort by score
            candidates.sort(key=lambda c: c.score, reverse=True)
            
            # Limit to max_results
            candidates = candidates[:params.max_results]
            
            logger.info(f"Found {len(candidates)} matching candidates")
            return candidates
        
        except Exception as e:
            logger.error(f"Error in source_candidates: {e}")
            return []
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """
        Extract skills from text.
        
        Args:
            text: Text to extract skills from
            
        Returns:
            List of extracted skills
        """
        # This is a very basic implementation
        # In a real system, we'd use NLP and a skills taxonomy
        skills = []
        
        # Simple approach - look for common skill indicators
        lines = text.split("\n")
        for line in lines:
            if line.strip().startswith("-") or line.strip().startswith("*"):
                skill = line.strip("- *").strip()
                if skill and len(skill) > 2:
                    skills.append(skill)
        
        # If we didn't extract any skills, try splitting by commas
        if not skills and "," in text:
            skills = [s.strip() for s in text.split(",") if s.strip()]
        
        return skills
    
    def _apply_candidate_filters(self, candidate: CandidateProfile, params: SourcingParams) -> bool:
        """
        Apply filters to determine if a candidate meets the criteria.
        
        Args:
            candidate: Candidate profile
            params: Sourcing parameters
            
        Returns:
            True if candidate passes filters, False otherwise
        """
        # Check minimum score
        if candidate.score < (params.similarity_threshold * 100):
            return False
        
        # Check minimum skills match
        if params.min_skills_match > 0 and len(candidate.skills) < params.min_skills_match:
            return False
        
        # Check keywords if specified
        if params.keywords:
            found_keywords = 0
            for keyword in params.keywords:
                keyword_lower = keyword.lower()
                # Check in skills
                if any(keyword_lower in skill.lower() for skill in candidate.skills):
                    found_keywords += 1
                    continue
                
                # Check in resume text
                if candidate.resume_text and keyword_lower in candidate.resume_text.lower():
                    found_keywords += 1
                    continue
            
            # Require at least half of the keywords to match
            if found_keywords < len(params.keywords) / 2:
                return False
        
        # Check location if specified
        if params.location and candidate.location:
            if params.location.lower() not in candidate.location.lower():
                return False
        
        # Check minimum experience (this would need proper processing in a real system)
        # For now, we'll just check for the number of experience entries as a proxy
        if params.min_experience_years > 0 and candidate.experience:
            if len(candidate.experience) < params.min_experience_years:
                return False
        
        # All filters passed
        return True
    
    def cleanup(self) -> None:
        """Clean up resources."""
        # Clean up old sourcing operations (older than 24 hours)
        current_time = time.time()
        to_remove = []
        
        for sourcing_id, sourcing_data in self.active_sourcing.items():
            if current_time - sourcing_data.get("start_time", 0) > 86400:  # 24 hours
                to_remove.append(sourcing_id)
        
        for sourcing_id in to_remove:
            del self.active_sourcing[sourcing_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old sourcing operations")
