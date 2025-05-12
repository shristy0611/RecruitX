"""
API Routes for Advanced Agent Features in RecruitPro AI.

This module defines FastAPI endpoints for interacting with the enhanced
screening and engagement agents, providing advanced capabilities like
multilingual processing, vision analysis, and sophisticated dialogue management.
"""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Body, Query, UploadFile, File
from pydantic import BaseModel, Field

from src.agents.advanced.enhanced_screening_agent import get_enhanced_screening_agent
from src.agents.advanced.advanced_engagement_agent import get_advanced_engagement_agent
from src.agents.advanced.multilingual_support import get_multilingual_processor
from src.orchestration.agent import Message, MessageType, MessagePriority

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize agents and processors
try:
    enhanced_screening_agent = get_enhanced_screening_agent()
    logger.info("EnhancedScreeningAgent initialized successfully for API routes.")
except Exception as e:
    logger.error(f"Failed to initialize EnhancedScreeningAgent for API: {e}")
    enhanced_screening_agent = None

try:
    advanced_engagement_agent = get_advanced_engagement_agent()
    logger.info("AdvancedEngagementAgent initialized successfully for API routes.")
except Exception as e:
    logger.error(f"Failed to initialize AdvancedEngagementAgent for API: {e}")
    advanced_engagement_agent = None

try:
    multilingual_processor = get_multilingual_processor()
    logger.info("MultilingualProcessor initialized successfully for API routes.")
except Exception as e:
    logger.error(f"Failed to initialize MultilingualProcessor for API: {e}")
    multilingual_processor = None

# --- Pydantic Models for API Requests and Responses ---

class ResumeParseRequest(BaseModel):
    resume_text: str
    language: Optional[str] = Field("en", description="ISO 639-1 language code of the resume text")

class ResumeAnalysisRequest(BaseModel):
    resume_text: str
    job_description: str
    language: Optional[str] = Field("en", description="ISO 639-1 language code of the resume text")

class TextAnalysisRequest(BaseModel):
    text: str
    language: Optional[str] = Field(None, description="ISO 639-1 language code, auto-detect if None")
    analysis_type: str = Field("general", description="Type of analysis: general, skills, sentiment")

class TranslationRequest(BaseModel):
    text: str
    source_language: Optional[str] = Field(None, description="ISO 639-1 source language code, auto-detect if None")
    target_language: str = Field("en", description="ISO 639-1 target language code")

class EngagementMessageRequest(BaseModel):
    candidate_id: str
    conversation_id: Optional[str] = None
    text: str
    language: Optional[str] = Field("en", description="ISO 639-1 language code of the message")
    image_url: Optional[str] = None # For messages with images by URL
    # image_data: Optional[str] = None # For base64 encoded images, consider UploadFile instead for FastAPI

class ContextSwitchRequest(BaseModel):
    candidate_id: str
    conversation_id: str
    new_context: str = Field(..., description="The new context to switch the conversation to.")

# --- Enhanced Screening Agent Routes ---

@router.post("/agents/screen/enhanced/parse_resume", summary="Enhanced Resume Parsing")
async def enhanced_parse_resume(request: ResumeParseRequest):
    """
    Parses a resume using the Enhanced Screening Agent, supporting multilingual input
    and leveraging advanced models like Gemini for deeper understanding.
    """
    if not enhanced_screening_agent:
        raise HTTPException(status_code=503, detail="EnhancedScreeningAgent is not available.")
    try:
        parsed_data = enhanced_screening_agent.parse_resume(
            resume_text=request.resume_text,
            language=request.language
        )
        return parsed_data
    except Exception as e:
        logger.error(f"Error in enhanced_parse_resume: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/screen/enhanced/analyze_resume_job", summary="Enhanced Resume-Job Analysis")
async def enhanced_analyze_resume_job(request: ResumeAnalysisRequest):
    """
    Analyzes a resume against a job description using the Enhanced Screening Agent.
    Provides detailed matching scores, skill gap analysis, and qualitative assessments.
    """
    if not enhanced_screening_agent:
        raise HTTPException(status_code=503, detail="EnhancedScreeningAgent is not available.")
    try:
        analysis_result = enhanced_screening_agent.analyze_resume_with_job(
            resume_text=request.resume_text,
            job_description=request.job_description,
            language=request.language
        )
        return analysis_result
    except Exception as e:
        logger.error(f"Error in enhanced_analyze_resume_job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# --- Advanced Engagement Agent Routes ---

@router.post("/agents/engage/advanced/process_message", summary="Process Advanced Engagement Message")
async def advanced_process_engagement_message(
    request: EngagementMessageRequest = Body(...),
    image_file: Optional[UploadFile] = File(None, description="Optional image file to accompany the message")
):
    """
    Processes a candidate message using the Advanced Engagement Agent.
    Supports multilingual dialogues, context switching, and image-based interactions.
    
    If `image_file` is provided, it will be prioritized over `image_url`.
    """
    if not advanced_engagement_agent:
        raise HTTPException(status_code=503, detail="AdvancedEngagementAgent is not available.")
    
    message_content = {
        "candidate_id": request.candidate_id,
        "conversation_id": request.conversation_id,
        "text": request.text,
        "language": request.language
    }
    
    command_type = "process_message_multilingual" # Default to multilingual text processing

    if image_file:
        # Handle image_file (e.g., save temporarily, get path/URL, or convert to base64)
        # For simplicity, let's assume agent can handle base64 or a URL if saved.
        # This part needs careful implementation based on how GeminiService handles images.
        # For now, let's assume the agent's method can take a base64 string or file path.
        # Here, we'll signal it's an image message. The agent itself needs to handle the UploadFile.
        # image_data_base64 = base64.b64encode(await image_file.read()).decode('utf-8')
        # message_content["image_data"] = image_data_base64 # This might be too large for a direct message payload
        message_content["image_filename"] = image_file.filename # Pass filename, agent might need to read it
        command_type = "process_message_with_image"
        # NOTE: The agent's `_handle_message_with_image` might need adjustment to accept UploadFile or its content directly.
    elif request.image_url:
        message_content["image_url"] = request.image_url
        command_type = "process_message_with_image"

    # Create a message object (simplified, actual Message object might be more complex)
    agent_message = Message(
        message_id=f"api_msg_{request.candidate_id}_{request.conversation_id or 'new'}",
        sender_id="api_gateway",
        receiver_id=advanced_engagement_agent.agent_id,
        message_type=MessageType.COMMAND,
        content={"command": command_type, **message_content},
        priority=MessagePriority.HIGH
    )
    
    try:
        # The agent's handle_command is synchronous in the provided structure, 
        # but for FastAPI, it's better if it returns something or updates a shared state 
        # that can be queried. For now, we'll assume it processes and the result is logged 
        # or handled internally, and we return a confirmation.
        # A more robust solution would use a message queue and a way to get async results.
        
        # Direct call for simplicity based on current agent structure
        # This is a placeholder for how the agent's response would be retrieved.
        # Ideally, the agent.handle_command would trigger a process, and another endpoint
        # would fetch the result, or it would use websockets/callbacks.
        
        if command_type == "process_message_with_image":
            # This is a simplified mock response. Actual implementation would involve agent interaction.
            if advanced_engagement_agent.gemini_service:
                # Simulate image processing and response generation
                processed_text = f"Processed image '{message_content.get('image_filename', request.image_url)}' with text: '{request.text}'. Awaiting Gemini response."
                # In a real scenario, agent would store response to be fetched or sent via callback.
                # For now, just acknowledge. The agent's internal logging will show processing.
                response_text = "Image message received and is being processed."
            else:
                response_text = "Image received, but vision processing is currently unavailable."
            
            # Simulate adding to conversation history (agent would do this)
            if request.conversation_id:
                 advanced_engagement_agent._add_to_conversation(request.conversation_id, "user", f"[IMAGE] {request.text}")
                 advanced_engagement_agent._add_to_conversation(request.conversation_id, "assistant", response_text)
            
            return {
                "status": "Image message received for processing", 
                "conversation_id": request.conversation_id or "new_conversation_started",
                "mock_response": response_text
            }
        elif command_type == "process_message_multilingual":
            # This is a simplified mock response.
            # Simulate multilingual processing
            response_text = f"Processed multilingual message in {request.language}: '{request.text}'. Awaiting LLM response."
            if request.conversation_id:
                 advanced_engagement_agent._add_to_conversation(request.conversation_id, "user", request.text)
                 advanced_engagement_agent._add_to_conversation(request.conversation_id, "assistant", response_text)
            
            return {
                "status": "Multilingual message received for processing", 
                "conversation_id": request.conversation_id or "new_conversation_started", 
                "mock_response": response_text
            }
        else:
            # Fallback for other commands if any handled by agent's default path
            advanced_engagement_agent.handle_command(agent_message)
            return {"status": "Message sent to Advanced Engagement Agent for processing"}

    except Exception as e:
        logger.error(f"Error in advanced_process_engagement_message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/engage/advanced/switch_context", summary="Switch Conversation Context")
async def advanced_switch_conversation_context(request: ContextSwitchRequest):
    """
    Switches the context of an ongoing conversation handled by the Advanced Engagement Agent.
    """
    if not advanced_engagement_agent:
        raise HTTPException(status_code=503, detail="AdvancedEngagementAgent is not available.")

    message_content = {
        "candidate_id": request.candidate_id,
        "conversation_id": request.conversation_id,
        "context": request.new_context
    }
    
    agent_message = Message(
        message_id=f"api_ctx_switch_{request.conversation_id}",
        sender_id="api_gateway",
        receiver_id=advanced_engagement_agent.agent_id,
        message_type=MessageType.COMMAND,
        content={"command": "switch_conversation_context", **message_content},
        priority=MessagePriority.HIGH
    )

    try:
        # Similar to above, direct call for simplicity. Real system might be async.
        # The agent's _handle_context_switch will manage the state.
        # We need a way to return the transition message generated by the agent.
        
        # Mocking retrieval of transition message
        # In a real system, this would be part of the agent's response mechanism.
        transition_message = advanced_engagement_agent._generate_context_transition(
            request.conversation_id,
            request.new_context
        )
        # Agent updates its internal state.
        advanced_engagement_agent._update_conversation_context(
            request.conversation_id,
            {"current_context": request.new_context}
        )
        advanced_engagement_agent._add_to_conversation(
            request.conversation_id, "system", f"Context switched to: {request.new_context}"
        )
        advanced_engagement_agent._add_to_conversation(
            request.conversation_id, "assistant", transition_message
        )

        return {
            "status": f"Context switched to {request.new_context}",
            "conversation_id": request.conversation_id,
            "transition_message": transition_message
        }
    except Exception as e:
        logger.error(f"Error in advanced_switch_conversation_context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# --- Multilingual Processor Routes (Directly, if not via agents) ---

@router.post("/multilingual/detect_language", summary="Detect Language")
async def detect_language_api(text_request: Dict[str, str]):
    """
    Detects the language of the provided text using the Multilingual Processor.
    Request body: {"text": "Your text here"}
    """
    if not multilingual_processor:
        raise HTTPException(status_code=503, detail="MultilingualProcessor is not available.")
    try:
        text = text_request.get("text")
        if not text:
            raise HTTPException(status_code=400, detail="Text field is required.")
        result = multilingual_processor.detect_language(text)
        return result
    except Exception as e:
        logger.error(f"Error in detect_language_api: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/multilingual/translate", summary="Translate Text")
async def translate_text_api(request: TranslationRequest):
    """
    Translates text from a source language to a target language using the Multilingual Processor.
    """
    if not multilingual_processor:
        raise HTTPException(status_code=503, detail="MultilingualProcessor is not available.")
    try:
        translated_text = multilingual_processor.translate_text(
            text=request.text,
            source_language=request.source_language,
            target_language=request.target_language
        )
        return {
            "original_text": request.text,
            "source_language": request.source_language or "auto-detected",
            "target_language": request.target_language,
            "translated_text": translated_text
        }
    except Exception as e:
        logger.error(f"Error in translate_text_api: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/multilingual/analyze_text", summary="Analyze Multilingual Text")
async def analyze_multilingual_text_api(request: TextAnalysisRequest):
    """
    Performs language-aware analysis (general, skills, sentiment) on text using the Multilingual Processor.
    """
    if not multilingual_processor:
        raise HTTPException(status_code=503, detail="MultilingualProcessor is not available.")
    try:
        analysis_result = multilingual_processor.analyze_multilingual_text(
            text=request.text,
            language=request.language,
            analysis_type=request.analysis_type
        )
        return analysis_result
    except Exception as e:
        logger.error(f"Error in analyze_multilingual_text_api: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


logger.info("Advanced Agent API routes defined.")

