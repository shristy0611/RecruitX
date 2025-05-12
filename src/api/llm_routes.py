"""
LLM Chat API routes for RecruitX.

This module provides FastAPI endpoints for chatting with both
local (Gemma) and cloud (Gemini) models.
"""
import logging
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from src.llm.gemma3_service import get_gemma3_service
from src.llm.gemma_service import get_gemma_service
from src.llm.gemini_service import get_gemini_service

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/llm", tags=["LLM"])

# Models for request and response
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Chat messages")
    temperature: Optional[float] = Field(0.7, description="Temperature for generation (0.0-1.0)")
    max_tokens: Optional[int] = Field(1024, description="Maximum tokens to generate")

class ChatCompletionResponse(BaseModel):
    message: ChatMessage = Field(..., description="Generated assistant message")
    model: str = Field(..., description="Model that generated the response")

# Initialize services
try:
    gemma3_service = get_gemma3_service()
    gemma_service = get_gemma_service()
    logger.info("LLM services initialized for chat routes")
except Exception as e:
    logger.error(f"Failed to initialize LLM services: {e}")
    gemma3_service = None
    gemma_service = None

@router.post(
    "/local/gemma/chat",
    response_model=ChatCompletionResponse,
    description="Generate a chat completion using the local Gemma 3 model"
)
async def gemma_chat(request: ChatCompletionRequest = Body(...)):
    """
    Generate a chat completion using the local Gemma 3 model.
    
    Args:
        request: Chat completion request with messages and parameters
        
    Returns:
        ChatCompletionResponse: Generated assistant message
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        if not gemma3_service or not gemma3_service.is_available:
            # Fallback to gemma service if gemma3 is not available
            if not gemma_service:
                raise HTTPException(
                    status_code=503,
                    detail="Local Gemma model service is not available"
                )
            
            # Convert messages to format expected by gemma_service
            prompt = ""
            for msg in request.messages:
                role_prefix = "User: " if msg.role.lower() == "user" else "Assistant: " if msg.role.lower() == "assistant" else ""
                prompt += f"{role_prefix}{msg.content}\n"
            
            prompt += "Assistant: "
            
            # Generate content
            generated_text = gemma_service.generate_content(
                prompt=prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            return ChatCompletionResponse(
                message=ChatMessage(role="assistant", content=generated_text),
                model="gemma-cloud-fallback"
            )
        else:
            # Convert messages to format expected by gemma3_service
            formatted_messages = []
            for msg in request.messages:
                formatted_messages.append({
                    "role": msg.role.lower(),
                    "content": msg.content
                })
            
            # Generate chat response
            response = gemma3_service.generate_chat_response(
                messages=formatted_messages,
                temperature=request.temperature,
                max_output_tokens=request.max_tokens
            )
            
            return ChatCompletionResponse(
                message=ChatMessage(role="assistant", content=response),
                model="gemma3-local"
            )
    
    except Exception as e:
        logger.error(f"Error generating Gemma chat completion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate chat completion: {str(e)}"
        )

@router.post(
    "/cloud/gemini/chat",
    response_model=ChatCompletionResponse,
    description="Generate a chat completion using the cloud Gemini model"
)
async def gemini_chat(request: ChatCompletionRequest = Body(...)):
    """
    Generate a chat completion using the cloud Gemini model.
    
    Args:
        request: Chat completion request with messages and parameters
        
    Returns:
        ChatCompletionResponse: Generated assistant message
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        # Initialize gemini service if needed
        gemini_service = get_gemini_service()
        
        if not gemini_service:
            # Fallback to Gemma3 if Gemini is not available
            if gemma3_service and gemma3_service.is_available:
                logger.warning("Falling back to local Gemma 3 model since Gemini is not available")
                # Convert messages to format expected by gemma3_service
                formatted_messages = []
                for msg in request.messages:
                    formatted_messages.append({
                        "role": msg.role.lower(),
                        "content": msg.content
                    })
                
                # Generate chat response
                response = gemma3_service.generate_chat_response(
                    messages=formatted_messages,
                    temperature=request.temperature,
                    max_output_tokens=request.max_tokens
                )
                
                return ChatCompletionResponse(
                    message=ChatMessage(role="assistant", content=response),
                    model="gemma3-local-fallback"
                )
            else:
                raise HTTPException(
                    status_code=503,
                    detail="Gemini model service is not available and no fallback is available"
                )
        
        # Convert messages to format expected by gemini_service
        formatted_messages = []
        for msg in request.messages:
            formatted_messages.append({
                "role": msg.role.lower(), 
                "content": msg.content
            })
        
        # Generate chat response
        response = gemini_service.generate_chat_response(
            messages=formatted_messages,
            temperature=request.temperature,
            max_output_tokens=request.max_tokens
        )
        
        return ChatCompletionResponse(
            message=ChatMessage(role="assistant", content=response),
            model="gemini-pro"
        )
    
    except Exception as e:
        logger.error(f"Error generating Gemini chat completion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate chat completion: {str(e)}"
        )
