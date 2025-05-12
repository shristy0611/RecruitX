"""
Engagement Agent for RecruitPro AI.

This agent implements conversational capabilities for interacting with candidates,
using a local LLM model and maintaining conversation state through Redis.
"""
import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

import redis
import requests
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

from src.orchestration.agent import Agent, Message, MessageType, MessagePriority
from src.utils.config import REDIS_HOST, REDIS_PORT, REDIS_DB, OLLAMA_BASE_URL, OLLAMA_MODEL
from src.knowledge_base.vector_store import VectorStore
from src.agents.matching_agent import MatchingAgent

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SYSTEM_PROMPT = """
You are an AI recruitment assistant for RecruitPro AI.
Your role is to engage with candidates in a professional, helpful manner.
When speaking with candidates:
- Be concise and direct but maintain a friendly tone
- Focus on collecting relevant information related to the job position
- Avoid making promises about job offers or interview outcomes
- Respect candidate privacy and only ask for job-relevant information
- Maintain a consistent conversation context

You have access to information about open positions and candidate profiles.
When discussing positions, mention key requirements and responsibilities.

Always be truthful about your capabilities and limitations as a recruitment assistant.
"""

CANDIDATE_INTERACTION_TEMPLATES = {
    "greeting": """
    Hello {candidate_name}, I'm the RecruitPro AI assistant. I'm here to discuss the {job_title} position at {company_name}. 
    Based on your profile, you seem to have relevant experience for this role. 
    Would you like to learn more about this opportunity?
    """,
    
    "job_description": """
    The {job_title} position at {company_name} involves:
    
    {job_description}
    
    Key requirements:
    {requirements}
    
    Location: {location}
    Job type: {job_type}
    {salary_info}
    
    Does this position align with your career interests?
    """,
    
    "skill_inquiry": """
    I see you have experience with {skills_list}. Could you tell me more about your experience with {specific_skill}? 
    Specifically, what kind of projects have you worked on that utilized this skill?
    """,
    
    "experience_inquiry": """
    Could you tell me about your most recent role as {recent_role}? 
    What were your primary responsibilities and key achievements?
    """,
    
    "availability": """
    What is your current notice period or availability to start a new position?
    """,
    
    "interview_scheduling": """
    {company_name} would like to schedule an interview for the {job_title} position. 
    Are you available for an interview on {proposed_date} at {proposed_time}?
    """,
    
    "feedback_request": """
    Thank you for your interest in the {job_title} position. 
    Our team has reviewed your profile and {feedback_message}.
    
    Would you like more specific feedback on your qualifications for this role?
    """,
    
    "closing": """
    Thank you for your time today. I'll pass your information to the hiring team at {company_name}.
    If you have any other questions about the {job_title} position, feel free to ask.
    """
}


@dataclass
class Conversation:
    """Data structure for storing conversation information."""
    conversation_id: str
    candidate_id: str
    job_id: Optional[str] = None
    messages: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    is_active: bool = True
    state: str = "initiated"  # initiated, active, paused, completed
    

@dataclass
class MessageRequest:
    """Request structure for sending messages to candidates."""
    conversation_id: Optional[str]
    candidate_id: str
    message: str
    job_id: Optional[str] = None
    template_key: Optional[str] = None
    template_vars: Dict[str, Any] = field(default_factory=dict)
    message_type: str = "text"  # text, template, scheduling, feedback


class EngagementAgent(Agent):
    """
    Agent for conversational interactions with candidates.
    
    This agent:
    1. Manages multi-turn conversations with candidates
    2. Provides job information and collects candidate details
    3. Maintains conversation history and context
    4. Generates contextually appropriate responses
    """
    
    def __init__(
        self, 
        agent_id: str = "engagement_agent",
        vector_store: Optional[VectorStore] = None,
        matching_agent: Optional[MatchingAgent] = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT
    ):
        """
        Initialize the engagement agent.
        
        Args:
            agent_id: Unique ID for this agent
            vector_store: Optional pre-configured VectorStore
            matching_agent: Optional pre-configured MatchingAgent
            system_prompt: System prompt for the conversation model
        """
        super().__init__(
            agent_id=agent_id,
            name="Engagement Agent",
            description="Provides conversational capabilities for candidate interactions",
            capabilities=[
                "candidate_engagement",
                "job_description",
                "interview_scheduling",
                "feedback_delivery"
            ]
        )
        
        # Initialize components
        self.vector_store = vector_store or VectorStore()
        self.matching_agent = matching_agent
        self.system_prompt = system_prompt
        
        # Initialize Redis for conversation storage
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
        
        # Active conversations
        self.active_conversations: Dict[str, Conversation] = {}
        
        # Templates
        self.templates = CANDIDATE_INTERACTION_TEMPLATES
    
    def initialize(self) -> None:
        """Initialize the agent."""
        logger.info("Initializing EngagementAgent")
        
        # Load active conversations from Redis
        self._load_active_conversations()
        
        # Initialize the LLM conversation chain
        self._initialize_conversation_chain()
    
    def _initialize_conversation_chain(self) -> None:
        """Initialize the LLM conversation chain for generating responses."""
        try:
            # Check if Ollama is available
            response = requests.get(f"{OLLAMA_BASE_URL}/api/health")
            if response.status_code == 200:
                logger.info("Ollama server is available")
                self.llm_available = True
            else:
                logger.warning("Ollama server health check failed")
                self.llm_available = False
        except Exception as e:
            logger.error(f"Failed to connect to Ollama server: {e}")
            self.llm_available = False
    
    def _load_active_conversations(self) -> None:
        """Load active conversations from Redis."""
        try:
            # Get all conversation keys
            conversation_keys = self.redis_client.keys("conversation:*")
            
            for key in conversation_keys:
                conversation_data = self.redis_client.get(key)
                if conversation_data:
                    try:
                        conversation_dict = json.loads(conversation_data)
                        conversation = Conversation(**conversation_dict)
                        
                        # Only load active conversations
                        if conversation.is_active:
                            self.active_conversations[conversation.conversation_id] = conversation
                    except Exception as e:
                        logger.error(f"Failed to parse conversation data for {key}: {e}")
            
            logger.info(f"Loaded {len(self.active_conversations)} active conversations from Redis")
        
        except Exception as e:
            logger.error(f"Failed to load conversations from Redis: {e}")
    
    def handle_command(self, message: Message) -> None:
        """
        Handle command messages.
        
        Args:
            message: Command message
        """
        command = message.content.get("command")
        logger.info(f"EngagementAgent received command: {command}")
        
        if command == "send_message":
            self._handle_send_message(message)
        elif command == "get_conversation":
            self._handle_get_conversation(message)
        elif command == "end_conversation":
            self._handle_end_conversation(message)
        else:
            self._send_error_response(
                message,
                f"Unknown command: {command}"
            )
    
    def _handle_send_message(self, message: Message) -> None:
        """
        Handle a request to send a message to a candidate.
        
        Args:
            message: Message containing the send request
        """
        try:
            # Extract parameters
            candidate_id = message.content.get("candidate_id")
            message_text = message.content.get("message")
            job_id = message.content.get("job_id")
            conversation_id = message.content.get("conversation_id")
            template_key = message.content.get("template_key")
            template_vars = message.content.get("template_vars", {})
            
            if not candidate_id:
                self._send_error_response(
                    message,
                    "Missing required parameter: candidate_id"
                )
                return
            
            # Create message request
            request = MessageRequest(
                conversation_id=conversation_id,
                candidate_id=candidate_id,
                message=message_text,
                job_id=job_id,
                template_key=template_key,
                template_vars=template_vars
            )
            
            # Process and send the message
            response = self.send_message(request)
            
            # Send success response
            self._send_simple_response(
                message,
                "Message sent successfully",
                {
                    "conversation_id": response.conversation_id,
                    "message_count": len(response.messages),
                    "state": response.state
                }
            )
        
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self._send_error_response(
                message,
                f"Error sending message: {str(e)}"
            )
    
    def _handle_get_conversation(self, message: Message) -> None:
        """
        Handle a request to retrieve a conversation.
        
        Args:
            message: Message containing the conversation request
        """
        try:
            # Extract parameters
            conversation_id = message.content.get("conversation_id")
            candidate_id = message.content.get("candidate_id")
            
            if not conversation_id and not candidate_id:
                self._send_error_response(
                    message,
                    "Missing required parameters: either conversation_id or candidate_id must be provided"
                )
                return
            
            # Get the conversation
            if conversation_id:
                conversation = self.get_conversation_by_id(conversation_id)
            else:
                conversation = self.get_conversation_by_candidate(candidate_id)
            
            if not conversation:
                self._send_error_response(
                    message,
                    f"No conversation found for {'conversation_id: ' + conversation_id if conversation_id else 'candidate_id: ' + candidate_id}"
                )
                return
            
            # Send success response
            self._send_simple_response(
                message,
                "Conversation retrieved successfully",
                asdict(conversation)
            )
        
        except Exception as e:
            logger.error(f"Error retrieving conversation: {e}")
            self._send_error_response(
                message,
                f"Error retrieving conversation: {str(e)}"
            )
    
    def _handle_end_conversation(self, message: Message) -> None:
        """
        Handle a request to end a conversation.
        
        Args:
            message: Message containing the end conversation request
        """
        try:
            # Extract parameters
            conversation_id = message.content.get("conversation_id")
            
            if not conversation_id:
                self._send_error_response(
                    message,
                    "Missing required parameter: conversation_id"
                )
                return
            
            # End the conversation
            success = self.end_conversation(conversation_id)
            
            if not success:
                self._send_error_response(
                    message,
                    f"Failed to end conversation: {conversation_id}"
                )
                return
            
            # Send success response
            self._send_simple_response(
                message,
                "Conversation ended successfully",
                {
                    "conversation_id": conversation_id,
                    "state": "completed"
                }
            )
        
        except Exception as e:
            logger.error(f"Error ending conversation: {e}")
            self._send_error_response(
                message,
                f"Error ending conversation: {str(e)}"
            )
    
    def send_message(self, request: MessageRequest) -> Conversation:
        """
        Send a message to a candidate and process the response.
        
        Args:
            request: Message request containing details
            
        Returns:
            Updated conversation object
        """
        # Get or create conversation
        conversation = None
        
        if request.conversation_id:
            conversation = self.get_conversation_by_id(request.conversation_id)
        
        if not conversation:
            conversation = self.get_conversation_by_candidate(request.candidate_id)
        
        if not conversation:
            # Create new conversation
            conversation_id = str(uuid.uuid4())
            conversation = Conversation(
                conversation_id=conversation_id,
                candidate_id=request.candidate_id,
                job_id=request.job_id,
                state="active"
            )
            
            # Add metadata
            if request.job_id:
                job_data = self.vector_store.get_by_id("JobDescription", request.job_id)
                if job_data:
                    conversation.metadata["job"] = {
                        "title": job_data.get("title", ""),
                        "company": job_data.get("company", ""),
                        "location": job_data.get("location", "")
                    }
            
            candidate_data = self.vector_store.get_by_id("CandidateProfile", request.candidate_id)
            if candidate_data:
                conversation.metadata["candidate"] = {
                    "name": candidate_data.get("name", ""),
                    "email": candidate_data.get("email", ""),
                    "phone": candidate_data.get("phone", "")
                }
        
        # Prepare message content
        message_content = request.message
        
        # Use template if specified
        if request.template_key and request.template_key in self.templates:
            template = self.templates[request.template_key]
            
            # Add default template variables
            template_vars = request.template_vars.copy()
            
            # Add job data if available
            if conversation.job_id:
                job_data = self.vector_store.get_by_id("JobDescription", conversation.job_id)
                if job_data:
                    template_vars.setdefault("job_title", job_data.get("title", ""))
                    template_vars.setdefault("company_name", job_data.get("company", ""))
                    template_vars.setdefault("job_description", job_data.get("description", ""))
                    template_vars.setdefault("requirements", job_data.get("requirements", ""))
                    template_vars.setdefault("location", job_data.get("location", ""))
                    template_vars.setdefault("job_type", job_data.get("job_type", "Full-time"))
                    
                    if job_data.get("salary_range"):
                        template_vars.setdefault("salary_info", f"Salary range: {job_data.get('salary_range')}")
                    else:
                        template_vars.setdefault("salary_info", "")
            
            # Add candidate data if available
            candidate_data = self.vector_store.get_by_id("CandidateProfile", conversation.candidate_id)
            if candidate_data:
                template_vars.setdefault("candidate_name", candidate_data.get("name", ""))
                
                skills = candidate_data.get("skills", [])
                if skills:
                    template_vars.setdefault("skills_list", ", ".join(skills[:5]))
                    template_vars.setdefault("specific_skill", skills[0] if skills else "")
                
                # Try to extract recent role from experience
                recent_role = ""
                experience = candidate_data.get("experience", "")
                if experience:
                    lines = experience.split("\n")
                    for line in lines[:10]:  # Check first 10 lines
                        if ":" in line or "|" in line:
                            role_parts = line.replace("|", ":").split(":")
                            if len(role_parts) >= 2:
                                recent_role = role_parts[0].strip()
                                break
                
                template_vars.setdefault("recent_role", recent_role or "your current role")
            
            # Format template
            try:
                message_content = template.format(**template_vars)
            except KeyError as e:
                logger.warning(f"Missing template variable: {e}")
                # Use original message if template formatting fails
                message_content = request.message or f"Error: Could not format template. Missing variable: {e}"
        
        # Add message to conversation
        conversation.messages.append({
            "role": "assistant",
            "content": message_content,
            "timestamp": time.time()
        })
        
        # Update conversation state and timestamp
        conversation.updated_at = time.time()
        conversation.state = "active"
        
        # Save conversation
        self._save_conversation(conversation)
        
        # Add to active conversations
        self.active_conversations[conversation.conversation_id] = conversation
        
        # Here we would normally send the message to the candidate
        # In a real system, this would interface with email, SMS, or a chat platform
        # For now, we'll simulate successful delivery
        logger.info(f"Message sent to candidate {request.candidate_id}: {message_content[:50]}...")
        
        return conversation
    
    def get_conversation_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Conversation if found, None otherwise
        """
        # Check active conversations first
        if conversation_id in self.active_conversations:
            return self.active_conversations[conversation_id]
        
        # Check Redis
        conversation_data = self.redis_client.get(f"conversation:{conversation_id}")
        if conversation_data:
            try:
                conversation_dict = json.loads(conversation_data)
                return Conversation(**conversation_dict)
            except Exception as e:
                logger.error(f"Failed to parse conversation data: {e}")
        
        return None
    
    def get_conversation_by_candidate(self, candidate_id: str) -> Optional[Conversation]:
        """
        Get the most recent active conversation for a candidate.
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            Most recent conversation if found, None otherwise
        """
        # Check active conversations first
        candidate_conversations = [
            conv for conv in self.active_conversations.values()
            if conv.candidate_id == candidate_id and conv.is_active
        ]
        
        if candidate_conversations:
            # Return the most recently updated conversation
            return max(candidate_conversations, key=lambda c: c.updated_at)
        
        # Check Redis
        # This is inefficient in a real system; we'd use secondary indexes or a relational DB
        # For now, we'll scan all conversations
        conversation_keys = self.redis_client.keys("conversation:*")
        
        candidate_conversations = []
        for key in conversation_keys:
            conversation_data = self.redis_client.get(key)
            if conversation_data:
                try:
                    conversation_dict = json.loads(conversation_data)
                    if conversation_dict.get("candidate_id") == candidate_id and conversation_dict.get("is_active", False):
                        candidate_conversations.append(Conversation(**conversation_dict))
                except Exception as e:
                    logger.error(f"Failed to parse conversation data for {key}: {e}")
        
        if candidate_conversations:
            # Return the most recently updated conversation
            return max(candidate_conversations, key=lambda c: c.updated_at)
        
        return None
    
    def end_conversation(self, conversation_id: str) -> bool:
        """
        End a conversation.
        
        Args:
            conversation_id: ID of the conversation to end
            
        Returns:
            True if successful, False otherwise
        """
        conversation = self.get_conversation_by_id(conversation_id)
        
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return False
        
        # Update conversation state
        conversation.is_active = False
        conversation.state = "completed"
        conversation.updated_at = time.time()
        
        # Save conversation
        self._save_conversation(conversation)
        
        # Remove from active conversations
        if conversation_id in self.active_conversations:
            del self.active_conversations[conversation_id]
        
        logger.info(f"Ended conversation: {conversation_id}")
        return True
    
    def _save_conversation(self, conversation: Conversation) -> None:
        """
        Save a conversation to Redis.
        
        Args:
            conversation: Conversation to save
        """
        try:
            # Convert to dict and save
            conversation_dict = asdict(conversation)
            self.redis_client.set(
                f"conversation:{conversation.conversation_id}",
                json.dumps(conversation_dict),
                ex=86400 * 30  # 30 days expiry
            )
        except Exception as e:
            logger.error(f"Failed to save conversation to Redis: {e}")
    
    def process_candidate_response(self, conversation_id: str, message_text: str) -> Optional[str]:
        """
        Process a response from a candidate and generate a reply.
        
        Args:
            conversation_id: ID of the conversation
            message_text: Message text from the candidate
            
        Returns:
            Response message or None if processing failed
        """
        # Get conversation
        conversation = self.get_conversation_by_id(conversation_id)
        
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return None
        
        # Add message to conversation
        conversation.messages.append({
            "role": "user",
            "content": message_text,
            "timestamp": time.time()
        })
        
        # Update conversation timestamp
        conversation.updated_at = time.time()
        
        # Generate response using LLM
        response = self._generate_llm_response(conversation)
        
        if response:
            # Add response to conversation
            conversation.messages.append({
                "role": "assistant",
                "content": response,
                "timestamp": time.time()
            })
            
            # Save conversation
            self._save_conversation(conversation)
            
            return response
        
        return None
    
    def _generate_llm_response(self, conversation: Conversation) -> Optional[str]:
        """
        Generate a response using the LLM.
        
        Args:
            conversation: Conversation object
            
        Returns:
            Generated response or None if generation failed
        """
        if not self.llm_available:
            # Return a fallback response if LLM is not available
            return "I'm currently experiencing technical difficulties. A human recruiter will follow up with you shortly."
        
        try:
            # Prepare conversation history
            history = []
            
            # Add system prompt
            system_prompt = self.system_prompt
            
            # Enhance system prompt with job and candidate information
            if conversation.metadata.get("job") or conversation.metadata.get("candidate"):
                job_info = ""
                candidate_info = ""
                
                if conversation.metadata.get("job"):
                    job = conversation.metadata["job"]
                    job_info = f"""
                    Job Information:
                    Title: {job.get('title', 'Unknown')}
                    Company: {job.get('company', 'Unknown')}
                    Location: {job.get('location', 'Unknown')}
                    """
                
                if conversation.metadata.get("candidate"):
                    candidate = conversation.metadata["candidate"]
                    candidate_info = f"""
                    Candidate Information:
                    Name: {candidate.get('name', 'Unknown')}
                    """
                
                system_prompt += f"\n\n{job_info}\n\n{candidate_info}"
            
            history.append(SystemMessage(content=system_prompt))
            
            # Add conversation messages
            for msg in conversation.messages:
                if msg["role"] == "user":
                    history.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    history.append(AIMessage(content=msg["content"]))
            
            # Make API call to Ollama
            messages_dicts = [{"role": m.type if hasattr(m, "type") else m.__class__.__name__.replace("Message", "").lower(), 
                               "content": m.content} 
                              for m in history]
            
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages_dicts,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "")
            else:
                logger.error(f"Failed to generate response: {response.status_code} {response.text}")
                return "I'm having trouble processing your request. Let me connect you with a human recruiter who can assist you."
        
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return "I apologize for the technical difficulties. A human recruiter will follow up with you shortly."
    
    def cleanup(self) -> None:
        """Clean up resources."""
        # Clean up inactive conversations (older than 24 hours)
        current_time = time.time()
        to_remove = []
        
        for conversation_id, conversation in self.active_conversations.items():
            if current_time - conversation.updated_at > 86400:  # 24 hours
                to_remove.append(conversation_id)
        
        for conversation_id in to_remove:
            # Mark as inactive but don't delete
            conversation = self.active_conversations[conversation_id]
            conversation.is_active = False
            self._save_conversation(conversation)
            
            # Remove from active conversations
            del self.active_conversations[conversation_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} inactive conversations")
