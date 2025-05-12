"""
Advanced Engagement Agent for RecruitPro AI.

This agent extends the base EngagementAgent with advanced multi-turn dialogue,
context switching capabilities, and vision functionality for more sophisticated
candidate interactions.
"""

import logging
import json
import time
import uuid
import base64
from typing import Dict, List, Any, Optional, Tuple, Union

from src.agents.engagement_agent import EngagementAgent
from src.llm.gemini_service import GeminiService
from src.llm.gemma_service import GemmaService
from src.knowledge_base.vector_store import VectorStore
from src.orchestration.agent import Message, MessageType, MessagePriority

# Configure logging
logger = logging.getLogger(__name__)


class AdvancedEngagementAgent(EngagementAgent):
    """
    Advanced Engagement Agent with sophisticated conversation capabilities.
    
    This agent extends the base EngagementAgent with:
    1. Multi-turn dialogue with improved context management
    2. Context switching to adapt to candidate needs
    3. Vision capabilities for analyzing diagrams and visual content
    4. Multilingual support for global recruitment
    """
    
    def __init__(
        self,
        agent_id: str = "advanced_engagement_agent",
        vector_store: Optional[VectorStore] = None
    ):
        """
        Initialize the Advanced Engagement Agent.
        
        Args:
            agent_id: Unique ID for this agent
            vector_store: Optional VectorStore instance
        """
        super().__init__(agent_id, vector_store)
        
        # Update capabilities to reflect advanced features
        self.capabilities.extend([
            "vision_processing",
            "multilingual_dialogue",
            "context_switching",
            "adaptive_conversation"
        ])
        
        # Initialize Gemini service for advanced features
        try:
            self.gemini_service = GeminiService()
            logger.info("Initialized Gemini service for advanced dialogue capabilities")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini service: {e}")
            self.gemini_service = None
        
        # Initialize Gemma service for multilingual support
        try:
            self.gemma_service = GemmaService()
            logger.info("Initialized Gemma service for multilingual dialogue support")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemma service: {e}")
            self.gemma_service = None
        
        # Enhanced conversation state tracking
        self.context_history = {}  # Store richer context for conversations
        self.topic_tracking = {}   # Track conversation topics
        self.conversation_stages = {}  # Track stages in conversation flow
    
    def handle_command(self, message: Message) -> None:
        """
        Handle command messages with enhanced capabilities.
        
        Args:
            message: Command message
        """
        command = message.content.get("command")
        logger.info(f"AdvancedEngagementAgent received command: {command}")
        
        if command == "process_message_with_image":
            self._handle_message_with_image(message)
        elif command == "process_message_multilingual":
            self._handle_multilingual_message(message)
        elif command == "switch_conversation_context":
            self._handle_context_switch(message)
        else:
            # Fall back to base implementation for standard commands
            super().handle_command(message)
    
    def _handle_message_with_image(self, message: Message) -> None:
        """
        Handle messages that include image content.
        
        Args:
            message: Message with image content
        """
        try:
            candidate_id = message.content.get("candidate_id")
            conversation_id = message.content.get("conversation_id")
            text_content = message.content.get("text", "")
            image_url = message.content.get("image_url")
            image_data = message.content.get("image_data")  # Base64 encoded image
            
            if not candidate_id or not (image_url or image_data):
                self._send_error_response(
                    message,
                    "Missing required parameters: candidate_id and image data"
                )
                return
            
            # Create conversation if it doesn't exist
            if conversation_id not in self.conversations:
                conversation_id = self._create_conversation(candidate_id)
            
            # Process the image with the text using Gemini's multimodal capabilities
            if self.gemini_service:
                # Process image from URL or base64 data
                if image_url:
                    response = self.gemini_service.process_image_url(
                        image_url=image_url,
                        text=text_content or "What can you tell me about this image?",
                        conversation_history=self._get_conversation_history(conversation_id)
                    )
                elif image_data:
                    response = self.gemini_service.process_image_data(
                        image_data=image_data,
                        text=text_content or "What can you tell me about this image?",
                        conversation_history=self._get_conversation_history(conversation_id)
                    )
                else:
                    raise ValueError("No valid image source provided")
                
                # Update conversation history
                self._add_to_conversation(
                    conversation_id=conversation_id,
                    role="user",
                    content=f"[IMAGE] {text_content}"
                )
                
                self._add_to_conversation(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response
                )
                
                # Update context with image interaction
                self._update_conversation_context(
                    conversation_id=conversation_id,
                    context_update={
                        "last_image_timestamp": time.time(),
                        "image_content_discussed": True
                    }
                )
                
                # Send response
                self._send_simple_response(
                    message,
                    "Processed image and generated response",
                    {
                        "conversation_id": conversation_id,
                        "candidate_id": candidate_id,
                        "response": response
                    }
                )
            else:
                # Fall back to text-only processing if Gemini is not available
                fallback_response = "I'm unable to process images at the moment. Could you describe what's in the image instead?"
                
                self._add_to_conversation(
                    conversation_id=conversation_id,
                    role="user",
                    content=f"[IMAGE] {text_content}"
                )
                
                self._add_to_conversation(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=fallback_response
                )
                
                self._send_simple_response(
                    message,
                    "Used fallback text processing (image capability unavailable)",
                    {
                        "conversation_id": conversation_id,
                        "candidate_id": candidate_id,
                        "response": fallback_response
                    }
                )
        
        except Exception as e:
            logger.error(f"Error processing message with image: {e}")
            self._send_error_response(
                message,
                f"Error processing message with image: {str(e)}"
            )
    
    def _handle_multilingual_message(self, message: Message) -> None:
        """
        Handle messages in languages other than English.
        
        Args:
            message: Message in non-English language
        """
        try:
            candidate_id = message.content.get("candidate_id")
            conversation_id = message.content.get("conversation_id")
            text_content = message.content.get("text", "")
            language = message.content.get("language", "en")
            
            if not candidate_id or not text_content:
                self._send_error_response(
                    message,
                    "Missing required parameters: candidate_id and text"
                )
                return
            
            # Create conversation if it doesn't exist
            if conversation_id not in self.conversations:
                conversation_id = self._create_conversation(candidate_id)
            
            # Store the language preference in context
            self._update_conversation_context(
                conversation_id=conversation_id,
                context_update={"preferred_language": language}
            )
            
            # If language is English, use standard processing
            if language == "en":
                super()._handle_process_message(message)
                return
            
            # For non-English, use Gemma service if available
            if self.gemma_service:
                # Get conversation history
                history = self._get_conversation_history(conversation_id)
                
                # Process message in native language
                response = self.gemma_service.generate_multilingual_response(
                    text=text_content,
                    language=language,
                    conversation_history=history
                )
                
                # Add to conversation history
                self._add_to_conversation(
                    conversation_id=conversation_id,
                    role="user",
                    content=text_content
                )
                
                self._add_to_conversation(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response
                )
                
                # Send response
                self._send_simple_response(
                    message,
                    f"Processed multilingual message in {language}",
                    {
                        "conversation_id": conversation_id,
                        "candidate_id": candidate_id,
                        "response": response,
                        "language": language
                    }
                )
            else:
                # Try to translate with base methods or fall back
                # First try to translate to English
                try:
                    import translators as ts
                    translated_text = ts.google(text_content, from_language=language, to_language="en")
                    
                    # Process in English
                    english_response = self._generate_response(
                        conversation_id=conversation_id,
                        message=translated_text
                    )
                    
                    # Translate back to original language
                    response = ts.google(english_response, from_language="en", to_language=language)
                    
                    # Add original and response to conversation
                    self._add_to_conversation(
                        conversation_id=conversation_id,
                        role="user",
                        content=text_content
                    )
                    
                    self._add_to_conversation(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=response
                    )
                    
                    # Send response
                    self._send_simple_response(
                        message,
                        f"Processed message with fallback translation in {language}",
                        {
                            "conversation_id": conversation_id,
                            "candidate_id": candidate_id,
                            "response": response,
                            "language": language
                        }
                    )
                    
                except Exception as translation_error:
                    logger.error(f"Translation fallback failed: {translation_error}")
                    
                    # Ultimate fallback - English only response
                    fallback_response = "I'm sorry, but I'm currently unable to process messages in languages other than English. Could you please provide your message in English?"
                    
                    self._add_to_conversation(
                        conversation_id=conversation_id,
                        role="user",
                        content=text_content
                    )
                    
                    self._add_to_conversation(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=fallback_response
                    )
                    
                    self._send_simple_response(
                        message,
                        "Used English fallback (multilingual capability unavailable)",
                        {
                            "conversation_id": conversation_id,
                            "candidate_id": candidate_id,
                            "response": fallback_response,
                            "language": "en"
                        }
                    )
        
        except Exception as e:
            logger.error(f"Error processing multilingual message: {e}")
            self._send_error_response(
                message,
                f"Error processing multilingual message: {str(e)}"
            )
    
    def _handle_context_switch(self, message: Message) -> None:
        """
        Handle context switching in conversations.
        
        Args:
            message: Message requesting context switch
        """
        try:
            candidate_id = message.content.get("candidate_id")
            conversation_id = message.content.get("conversation_id")
            new_context = message.content.get("context")
            
            if not candidate_id or not conversation_id or not new_context:
                self._send_error_response(
                    message,
                    "Missing required parameters: candidate_id, conversation_id, and context"
                )
                return
            
            # Ensure conversation exists
            if conversation_id not in self.conversations:
                self._send_error_response(
                    message,
                    f"Conversation not found: {conversation_id}"
                )
                return
            
            # Update context
            self._update_conversation_context(
                conversation_id=conversation_id,
                context_update={"current_context": new_context}
            )
            
            # Add system message to conversation noting context change
            self._add_to_conversation(
                conversation_id=conversation_id,
                role="system",
                content=f"Context switched to: {new_context}"
            )
            
            # Generate transitional message based on new context
            transition_message = self._generate_context_transition(
                conversation_id=conversation_id,
                new_context=new_context
            )
            
            # Add transition message to conversation
            self._add_to_conversation(
                conversation_id=conversation_id,
                role="assistant",
                content=transition_message
            )
            
            # Send response
            self._send_simple_response(
                message,
                f"Switched conversation context to: {new_context}",
                {
                    "conversation_id": conversation_id,
                    "candidate_id": candidate_id,
                    "transition_message": transition_message
                }
            )
            
        except Exception as e:
            logger.error(f"Error switching conversation context: {e}")
            self._send_error_response(
                message,
                f"Error switching conversation context: {str(e)}"
            )
    
    def _update_conversation_context(
        self,
        conversation_id: str,
        context_update: Dict[str, Any]
    ) -> None:
        """
        Update the rich context for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            context_update: Dictionary of context updates
        """
        if conversation_id not in self.context_history:
            self.context_history[conversation_id] = {}
            
        self.context_history[conversation_id].update(context_update)
        
        # Update conversation stage if topic changes
        if "current_context" in context_update:
            self.topic_tracking[conversation_id] = context_update["current_context"]
            
            # Reset conversation stage for new topic
            self.conversation_stages[conversation_id] = "initial"
    
    def _get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """
        Get formatted conversation history for LLM context.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            List of message dictionaries with role and content
        """
        if conversation_id not in self.conversations:
            return []
            
        conversation = self.conversations[conversation_id]
        
        # Format history for LLM with roles and content
        history = []
        for msg in conversation:
            history.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
            
        return history
    
    def _generate_context_transition(
        self,
        conversation_id: str,
        new_context: str
    ) -> str:
        """
        Generate a transitional message for context switching.
        
        Args:
            conversation_id: ID of the conversation
            new_context: New context description
            
        Returns:
            Transitional message text
        """
        # Get conversation history
        history = self._get_conversation_history(conversation_id)
        
        # Create prompt for smooth transition
        if self.gemini_service:
            prompt = f"""
            The conversation is switching to a new context: {new_context}
            
            Based on the conversation history and this new context, 
            generate a natural transition message that acknowledges the change
            and helps move the conversation forward. The message should be
            friendly, professional, and maintain continuity.
            
            Previous conversation:
            {json.dumps(history[-5:], indent=2)}  # Use last 5 messages for context
            """
            
            transition = self.gemini_service.generate_content(prompt)
            
            # Clean up the response
            transition = transition.strip()
            if transition.startswith('"') and transition.endswith('"'):
                transition = transition[1:-1]
                
            return transition
            
        else:
            # Fallback transition templates
            transitions = {
                "job_details": "I'd be happy to discuss more about the job details. What specific aspects would you like to know about?",
                "application_process": "Let's switch gears and talk about the application process. What questions do you have about next steps?",
                "technical_questions": "I understand you'd like to discuss some technical aspects. I'm here to help with any questions you might have.",
                "compensation": "Regarding compensation, I can provide some general information about the package offered for this role.",
                "company_culture": "About our company culture, we pride ourselves on fostering an environment that values innovation and collaboration.",
                "feedback": "I'd be happy to provide feedback on your candidacy so far. Let me share some thoughts based on what we've discussed."
            }
            
            return transitions.get(
                new_context,
                "I understand you'd like to discuss something different. How can I help you with this new topic?"
            )
    
    def _process_message_with_context(
        self,
        conversation_id: str,
        text: str
    ) -> str:
        """
        Process a message with enhanced context awareness.
        
        Args:
            conversation_id: ID of the conversation
            text: Message text
            
        Returns:
            Response text
        """
        # Get conversation history and context
        history = self._get_conversation_history(conversation_id)
        context = self.context_history.get(conversation_id, {})
        
        # Detect current topic if not explicitly set
        if conversation_id not in self.topic_tracking:
            topic = self._detect_conversation_topic(text, history)
            self.topic_tracking[conversation_id] = topic
        else:
            topic = self.topic_tracking[conversation_id]
        
        # Update conversation stage
        stage = self._update_conversation_stage(conversation_id, text, history)
        
        # Use enhanced response generation with Gemini if available
        if self.gemini_service:
            # Create a context-aware prompt
            prompt = f"""
            You are an AI assistant for a recruitment company, having a conversation with a job candidate.
            
            Current conversation topic: {topic}
            Conversation stage: {stage}
            Preferred language: {context.get('preferred_language', 'en')}
            
            Respond to the candidate's message in a helpful, professional manner.
            Keep your response relevant to the current topic and stage.
            Be concise but thorough in your response.
            
            Candidate message: {text}
            """
            
            response = self.gemini_service.generate_content(
                prompt,
                conversation_history=history
            )
            
            return response
        else:
            # Fall back to base implementation
            return super()._generate_response(conversation_id, text)
    
    def _detect_conversation_topic(
        self,
        text: str,
        history: List[Dict[str, str]]
    ) -> str:
        """
        Detect the current conversation topic.
        
        Args:
            text: Current message text
            history: Conversation history
            
        Returns:
            Detected topic
        """
        # Common recruitment conversation topics
        topics = [
            "job_details",
            "application_process",
            "technical_questions",
            "compensation",
            "company_culture",
            "feedback"
        ]
        
        # Simple keyword-based detection
        topic_keywords = {
            "job_details": ["role", "position", "job", "responsibilities", "duties", "day to day"],
            "application_process": ["process", "next steps", "interview", "timeline", "application"],
            "technical_questions": ["technical", "skills", "experience", "project", "technology"],
            "compensation": ["salary", "compensation", "pay", "benefits", "package", "stock"],
            "company_culture": ["culture", "team", "environment", "values", "work life"],
            "feedback": ["feedback", "assessment", "evaluation", "chances", "improve"]
        }
        
        # Check for topic keywords in current message
        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return topic
        
        # If no topic detected from current message, check history
        combined_history = ""
        for message in history[-3:]:  # Check last 3 messages
            combined_history += message.get("content", "").lower() + " "
            
        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in combined_history:
                    return topic
        
        # Default to general inquiry if no topic detected
        return "general_inquiry"
    
    def _update_conversation_stage(
        self,
        conversation_id: str,
        text: str,
        history: List[Dict[str, str]]
    ) -> str:
        """
        Update and return the current conversation stage.
        
        Args:
            conversation_id: ID of the conversation
            text: Current message text
            history: Conversation history
            
        Returns:
            Current conversation stage
        """
        # Initialize stage if not present
        if conversation_id not in self.conversation_stages:
            self.conversation_stages[conversation_id] = "initial"
            
        current_stage = self.conversation_stages[conversation_id]
        
        # Define stage transitions
        stage_flow = {
            "initial": ["information_exchange", "deep_dive"],
            "information_exchange": ["deep_dive", "objection_handling", "conclusion"],
            "deep_dive": ["objection_handling", "information_exchange", "conclusion"],
            "objection_handling": ["deep_dive", "conclusion"],
            "conclusion": ["information_exchange"]  # Allow cycling back if new questions arise
        }
        
        # Stage detection keywords
        stage_keywords = {
            "initial": ["hello", "hi", "introduction", "start", "begin"],
            "information_exchange": ["what", "how", "tell me", "explain", "describe"],
            "deep_dive": ["specific", "detail", "example", "elaborate", "more about"],
            "objection_handling": ["concern", "worry", "issue", "problem", "not sure"],
            "conclusion": ["thank", "appreciate", "next steps", "follow up", "goodbye"]
        }
        
        # Check for stage transition based on message content
        text_lower = text.lower()
        for stage, keywords in stage_keywords.items():
            if stage in stage_flow.get(current_stage, []):  # Only consider valid transitions
                for keyword in keywords:
                    if keyword in text_lower:
                        self.conversation_stages[conversation_id] = stage
                        return stage
        
        # If no transition detected, keep current stage
        return current_stage


# Factory function to get advanced engagement agent
def get_advanced_engagement_agent(vector_store=None) -> AdvancedEngagementAgent:
    """
    Get an instance of the AdvancedEngagementAgent.
    
    Args:
        vector_store: Optional vector store instance
        
    Returns:
        AdvancedEngagementAgent instance
    """
    return AdvancedEngagementAgent(vector_store=vector_store)
