from typing import Dict, List, Optional
from pydantic import Field
import json

from app.agent.planning import PlanningAgent
from app.tool import ToolCollection, PlanningTool, Terminate
from app.schema import Message

from .document_processor import DocumentProcessorAgent
from .matching_agent import MatchingAgent

class OrchestratorAgent(PlanningAgent):
    """Agent for orchestrating the recruitment matching process."""
    
    name: str = "orchestrator"
    description: str = "Coordinate document processing and matching using multiple agents"
    
    # Configure available tools
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            PlanningTool(),
            Terminate()
        )
    )
    
    # System prompt for orchestration
    system_prompt: str = """You are an orchestrator agent that:
    1. Coordinates document processing and matching
    2. Manages the flow of information between agents
    3. Ensures efficient and reliable processing
    
    Follow these guidelines:
    - Process job descriptions and resumes in parallel when possible
    - Validate all inputs and outputs
    - Handle errors gracefully with appropriate fallbacks
    - Maintain state and context throughout the process
    - Provide clear progress updates
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.doc_processor = DocumentProcessorAgent()
        self.matcher = MatchingAgent()
        
    async def process_job_description(self, file_path: str) -> Dict:
        """Process a job description document."""
        return await self.doc_processor.process_document(file_path)
    
    async def process_resumes(self, file_paths: List[str]) -> List[Dict]:
        """Process multiple resume documents in parallel."""
        import asyncio
        tasks = [self.doc_processor.process_document(path) for path in file_paths]
        return await asyncio.gather(*tasks)
    
    async def match_candidates(self, jd_result: Dict, resume_results: List[Dict]) -> str:
        """Match processed resumes against a job description."""
        # Prepare matching request
        request = {
            "jd_text": jd_result["document"]["text"],
            "jd_entities": jd_result["entities"],
            "resume_texts": [r["document"]["text"] for r in resume_results],
            "resume_entities": [r["entities"] for r in resume_results]
        }
        
        # Execute matching
        return await self.matcher.run(json.dumps(request))
    
    async def run(self, request: Optional[str] = None) -> str:
        """Run the orchestrator with an optional initial request."""
        if not request:
            return "No request provided"
            
        try:
            # Parse request (expecting JSON with file paths)
            data = json.loads(request)
            jd_path = data.get("jd_path")
            resume_paths = data.get("resume_paths", [])
            
            if not jd_path or not resume_paths:
                return "Missing required file paths"
                
            # Create initial plan
            plan = f"""
            Plan: Process and match documents
            
            Steps:
            1. Process job description: {jd_path}
            2. Process resumes: {len(resume_paths)} files
            3. Match candidates
            4. Generate final report
            """
            
            self.update_memory("system", plan)
            
            # Step 1: Process job description
            self.update_memory("assistant", "Processing job description...")
            jd_result = await self.process_job_description(jd_path)
            
            if "error" in jd_result:
                return f"Error processing job description: {jd_result['error']}"
                
            # Step 2: Process resumes
            self.update_memory("assistant", "Processing resumes...")
            resume_results = await self.process_resumes(resume_paths)
            
            # Check for errors
            failed_resumes = [(i, r) for i, r in enumerate(resume_results) if "error" in r]
            if failed_resumes:
                error_msg = "Some resumes failed to process:\n"
                for idx, result in failed_resumes:
                    error_msg += f"- Resume {idx + 1}: {result['error']}\n"
                self.update_memory("assistant", error_msg)
                
            # Filter out failed resumes
            valid_results = [r for r in resume_results if "error" not in r]
            
            if not valid_results:
                return "No valid resumes to process"
                
            # Step 3: Match candidates
            self.update_memory("assistant", "Matching candidates...")
            matching_result = await self.match_candidates(jd_result, valid_results)
            
            # Step 4: Generate final report
            final_report = f"""
            Recruitment Matching Report
            -------------------------
            Job Description: {jd_path}
            Total Resumes: {len(resume_paths)}
            Successfully Processed: {len(valid_results)}
            Failed: {len(failed_resumes)}
            
            {matching_result}
            """
            
            self.update_memory("assistant", final_report)
            return final_report
            
        except Exception as e:
            error_msg = f"Error in orchestration: {str(e)}"
            self.update_memory("assistant", error_msg)
            return error_msg
    
    async def step(self) -> str:
        """Execute a single step in the orchestration process."""
        # This agent uses planning for complex orchestration
        return await super().step() 