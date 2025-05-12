"""
Screening Orchestrator Agent for RecruitPro AI.

This agent coordinates the resume screening process, delegating tasks to the
ScreeningAgent and managing the workflow of candidate evaluation.
"""
import json
import logging
import time
import uuid
from typing import Dict, Any, List, Optional

from src.agents.screening_agent import ScreeningAgent
from src.knowledge_base.vector_store import VectorStore
from src.orchestration.agent import Agent, Message, MessageType, MessagePriority
from src.utils.config import WEAVIATE_URL

# Configure logging
logger = logging.getLogger(__name__)


class ScreeningOrchestrator(Agent):
    """
    Orchestrator agent for the resume screening process.
    
    This agent:
    1. Receives screening requests
    2. Delegates to the ScreeningAgent for resume parsing
    3. Stores results in the vector database
    4. Returns scoring and feedback
    """
    
    def __init__(
        self, 
        agent_id: str = "screening_orchestrator",
        screening_agent: Optional[ScreeningAgent] = None,
        vector_store: Optional[VectorStore] = None
    ):
        """
        Initialize the screening orchestrator.
        
        Args:
            agent_id: Unique ID for this agent
            screening_agent: Optional pre-configured ScreeningAgent
            vector_store: Optional pre-configured VectorStore
        """
        super().__init__(
            agent_id=agent_id,
            name="Screening Orchestrator",
            description="Coordinates the resume screening process",
            capabilities=[
                "resume_screening",
                "candidate_evaluation",
                "job_matching"
            ]
        )
        
        # Initialize components
        self.screening_agent = screening_agent or ScreeningAgent()
        self.vector_store = vector_store or VectorStore(url=WEAVIATE_URL)
        
        # Track ongoing screening operations
        self.active_screenings: Dict[str, Dict[str, Any]] = {}
    
    def initialize(self) -> None:
        """Initialize the agent."""
        logger.info("Initializing ScreeningOrchestrator")
        # Nothing special needed for initialization
    
    def handle_command(self, message: Message) -> None:
        """
        Handle command messages.
        
        Args:
            message: Command message
        """
        command = message.content.get("command")
        logger.info(f"ScreeningOrchestrator received command: {command}")
        
        if command == "screen_resume":
            self._handle_screen_resume(message)
        elif command == "get_screening_status":
            self._handle_get_screening_status(message)
        elif command == "store_candidate":
            self._handle_store_candidate(message)
        else:
            self._send_error_response(
                message,
                f"Unknown command: {command}"
            )
    
    def _handle_screen_resume(self, message: Message) -> None:
        """
        Handle a resume screening request.
        
        Args:
            message: Message containing resume screening request
        """
        try:
            # Extract parameters
            job_id = message.content.get("job_id")
            resume_text = message.content.get("resume_text")
            
            if not job_id or not resume_text:
                self._send_error_response(
                    message,
                    "Missing required parameters: job_id and resume_text"
                )
                return
            
            # Generate a unique screening ID
            screening_id = str(uuid.uuid4())
            
            # Store in active screenings
            self.active_screenings[screening_id] = {
                "job_id": job_id,
                "resume_text": resume_text,
                "status": "processing",
                "start_time": time.time(),
                "message_id": message.message_id
            }
            
            # Process the resume using the screening agent
            logger.info(f"Processing resume for job {job_id}, screening ID: {screening_id}")
            result = self.screening_agent.process_resume(resume_text, job_id)
            
            # Update screening status
            if "error" in result and result["error"]:
                self.active_screenings[screening_id]["status"] = "error"
                self.active_screenings[screening_id]["error"] = result["error"]
                
                self._send_error_response(
                    message,
                    f"Error processing resume: {result['error']}",
                    {"screening_id": screening_id}
                )
            else:
                self.active_screenings[screening_id]["status"] = "completed"
                self.active_screenings[screening_id]["result"] = result
                self.active_screenings[screening_id]["end_time"] = time.time()
                
                # Send success response
                self._send_simple_response(
                    message,
                    "Resume processed successfully",
                    {
                        "screening_id": screening_id,
                        "resume_data": result["resume_data"],
                        "job_data": result["job_data"],
                        "score_data": result["score_data"]
                    }
                )
        
        except Exception as e:
            logger.error(f"Error processing resume: {e}")
            self._send_error_response(
                message,
                f"Error processing resume: {str(e)}"
            )
    
    def _handle_get_screening_status(self, message: Message) -> None:
        """
        Handle a request for screening status.
        
        Args:
            message: Message containing screening status request
        """
        screening_id = message.content.get("screening_id")
        
        if not screening_id:
            self._send_error_response(
                message,
                "Missing required parameter: screening_id"
            )
            return
        
        if screening_id not in self.active_screenings:
            self._send_error_response(
                message,
                f"Screening ID not found: {screening_id}"
            )
            return
        
        screening_data = self.active_screenings[screening_id]
        
        self._send_simple_response(
            message,
            f"Screening status: {screening_data['status']}",
            {"screening_data": screening_data}
        )
    
    def _handle_store_candidate(self, message: Message) -> None:
        """
        Handle a request to store candidate data in the vector database.
        
        Args:
            message: Message containing candidate storage request
        """
        try:
            screening_id = message.content.get("screening_id")
            
            if not screening_id:
                self._send_error_response(
                    message,
                    "Missing required parameter: screening_id"
                )
                return
            
            if screening_id not in self.active_screenings:
                self._send_error_response(
                    message,
                    f"Screening ID not found: {screening_id}"
                )
                return
            
            screening_data = self.active_screenings[screening_id]
            
            if screening_data["status"] != "completed":
                self._send_error_response(
                    message,
                    f"Cannot store candidate - screening not completed. Status: {screening_data['status']}"
                )
                return
            
            # Extract data to store
            result = screening_data["result"]
            resume_data = result["resume_data"]
            job_id = screening_data["job_id"]
            
            # Store in vector database
            properties = {
                "name": resume_data.get("name", "Unknown Candidate"),
                "email": resume_data.get("email", ""),
                "phone": resume_data.get("phone", ""),
                "skills": resume_data.get("skills", []),
                "education": resume_data.get("education", []),
                "experience": resume_data.get("experience", []),
                "resume_text": screening_data["resume_text"],
                "job_id": job_id,
                "score": result["score_data"].get("overall_score", 0),
                "screening_id": screening_id,
                "screening_timestamp": time.time()
            }
            
            # Add to vector store
            candidate_id = self.vector_store.add_object(
                class_name="CandidateProfile",
                properties=properties
            )
            
            if candidate_id:
                # Update screening data with candidate ID
                screening_data["candidate_id"] = candidate_id
                
                self._send_simple_response(
                    message,
                    "Candidate stored successfully",
                    {
                        "screening_id": screening_id,
                        "candidate_id": candidate_id
                    }
                )
            else:
                self._send_error_response(
                    message,
                    "Failed to store candidate in vector database"
                )
        
        except Exception as e:
            logger.error(f"Error storing candidate: {e}")
            self._send_error_response(
                message,
                f"Error storing candidate: {str(e)}"
            )
    
    def screen_resume(self, resume_text: str, job_id: str) -> Dict[str, Any]:
        """
        Screen a resume against a job description.
        
        This is a synchronous wrapper around the asynchronous message-based screening.
        
        Args:
            resume_text: Text of the resume to screen
            job_id: ID of the job to screen against
            
        Returns:
            Screening results including resume data, job data, and score data
        """
        try:
            # Process directly using screening agent
            result = self.screening_agent.process_resume(resume_text, job_id)
            
            # Generate a unique screening ID
            screening_id = str(uuid.uuid4())
            
            # Store in active screenings
            self.active_screenings[screening_id] = {
                "job_id": job_id,
                "resume_text": resume_text,
                "status": "completed",
                "start_time": time.time(),
                "end_time": time.time(),
                "result": result
            }
            
            # Add screening ID to result
            result["screening_id"] = screening_id
            
            return result
        
        except Exception as e:
            logger.error(f"Error in screen_resume: {e}")
            return {
                "error": str(e),
                "resume_data": {},
                "job_data": {},
                "score_data": {"overall_score": 0}
            }
    
    def cleanup(self) -> None:
        """Clean up resources."""
        # Clean up old screenings (older than 24 hours)
        current_time = time.time()
        to_remove = []
        
        for screening_id, screening_data in self.active_screenings.items():
            if current_time - screening_data.get("start_time", 0) > 86400:  # 24 hours
                to_remove.append(screening_id)
        
        for screening_id in to_remove:
            del self.active_screenings[screening_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old screenings")
