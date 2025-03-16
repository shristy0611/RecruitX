from typing import Dict, List, Optional
from pydantic import Field

from app.agent.planning import PlanningAgent
from app.tool import ToolCollection
from app.schema import Message
from ..tools.matching_tool import MatchingTool

class MatchingAgent(PlanningAgent):
    """Agent for matching resumes to job descriptions."""
    
    name: str = "matcher"
    description: str = "Match resumes to job descriptions using Gemini"
    
    # Configure available tools
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(MatchingTool())
    )
    
    # System prompt for matching
    system_prompt: str = """You are a recruitment matching agent that:
    1. Analyzes job descriptions and resumes using semantic matching
    2. Generates detailed insights about the match
    3. Provides actionable recommendations
    
    Follow these guidelines:
    - Consider both semantic similarity and specific requirements
    - Provide clear explanations for match scores
    - Highlight key matching points and potential gaps
    - Suggest specific improvements for candidates
    - Handle multiple resumes efficiently
    """
    
    async def match_documents(
        self,
        jd_text: str,
        jd_entities: List[Dict],
        resume_texts: List[str],
        resume_entities: List[List[Dict]]
    ) -> List[Dict]:
        """Match multiple resumes against a job description."""
        matches = []
        
        for resume_text, entities in zip(resume_texts, resume_entities):
            # Get match result
            match_result = await self.available_tools.execute(
                name="matcher",
                tool_input={
                    "jd_text": jd_text,
                    "resume_text": resume_text,
                    "jd_entities": jd_entities,
                    "resume_entities": entities
                }
            )
            
            if match_result.error:
                matches.append({
                    "error": match_result.error,
                    "score": 0.0,
                    "insights": None
                })
            else:
                matches.append(match_result.output)
        
        # Sort matches by score
        return sorted(matches, key=lambda x: x.get("score", 0), reverse=True)
    
    async def run(self, request: Optional[str] = None) -> str:
        """Run the agent with an optional initial request."""
        if not request:
            return "No matching request provided"
            
        # Add request to memory
        self.update_memory("user", request)
        
        try:
            # Parse the request (assuming JSON format)
            import json
            data = json.loads(request)
            
            # Match documents
            matches = await self.match_documents(
                data["jd_text"],
                data["jd_entities"],
                data["resume_texts"],
                data["resume_entities"]
            )
            
            # Format response
            response = "Matching Results:\n\n"
            
            for i, match in enumerate(matches, 1):
                if "error" in match:
                    response += f"Match {i}: Error - {match['error']}\n\n"
                    continue
                    
                response += f"""
                Match {i}:
                Score: {match['score']:.2f}
                Confidence: {match['insights']['confidence']:.2f}
                
                Summary: {match['insights']['summary']}
                
                Key Matches:
                """
                
                for point in match['insights']['key_matches']:
                    response += f"- {point}\n"
                    
                response += "\nGaps:\n"
                for gap in match['insights']['gaps']:
                    response += f"- {gap}\n"
                    
                response += "\nRecommendations:\n"
                for rec in match['insights']['recommendations']:
                    response += f"- {rec}\n"
                    
                response += "\n---\n"
            
            # Add response to memory
            self.update_memory("assistant", response)
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing matching request: {str(e)}"
            self.update_memory("assistant", error_msg)
            return error_msg
    
    async def step(self) -> str:
        """Execute a single step in the matching process."""
        # This agent uses planning for complex matching tasks
        return await super().step() 