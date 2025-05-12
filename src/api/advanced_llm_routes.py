"""
API Routes for Advanced LLM Integration in RecruitPro AI.

This module provides FastAPI endpoints for interacting with the Advanced LLM
Integration capabilities, including context-aware prompting, optimized model
selection, and specialized prompting techniques.
"""

import logging
from typing import Dict, List, Any, Optional, Union

from fastapi import APIRouter, HTTPException, Body, Query, Depends
from pydantic import BaseModel, Field

from src.llm.advanced.advanced_llm_service import (
    get_advanced_llm_service,
    ModelSelectionStrategy
)
from src.llm.advanced.prompt_manager import (
    get_prompt_manager,
    PromptTemplate
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
try:
    advanced_llm_service = get_advanced_llm_service()
    prompt_manager = get_prompt_manager()
    logger.info("Advanced LLM services initialized for API routes")
except Exception as e:
    logger.error(f"Failed to initialize Advanced LLM services: {e}")
    advanced_llm_service = None
    prompt_manager = None

# Define API models
class ContentGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Input prompt for content generation")
    model: Optional[str] = Field(None, description="Optional specific model to use")
    task_type: str = Field("reasoning", description="Task type for model selection")
    strategy: str = Field(ModelSelectionStrategy.BALANCED, description="Model selection strategy")
    use_cache: bool = Field(True, description="Whether to use result cache")
    max_output_tokens: int = Field(1024, description="Maximum tokens in output")
    temperature: float = Field(0.7, description="Temperature for sampling (0.0-1.0)")
    top_p: float = Field(0.95, description="Top-p sampling parameter (0.0-1.0)")
    top_k: int = Field(40, description="Top-k sampling parameter")

class TemplateGenerationRequest(BaseModel):
    template_id: str = Field(..., description="ID of prompt template to use")
    parameters: Dict[str, Any] = Field(..., description="Parameters for the template")
    model: Optional[str] = Field(None, description="Optional specific model to use")
    task_type: str = Field("reasoning", description="Task type for model selection")
    strategy: str = Field(ModelSelectionStrategy.BALANCED, description="Model selection strategy")
    use_cache: bool = Field(True, description="Whether to use result cache")

class ContextAwareGenerationRequest(BaseModel):
    query: str = Field(..., description="Query for context retrieval")
    template_id: str = Field(..., description="ID of prompt template to use")
    parameters: Dict[str, Any] = Field(..., description="Parameters for the template")
    domain: str = Field("recruitment", description="Domain for context filtering")
    model: Optional[str] = Field(None, description="Optional specific model to use")
    task_type: str = Field("reasoning", description="Task type for model selection")
    strategy: str = Field(ModelSelectionStrategy.BALANCED, description="Model selection strategy")
    use_cache: bool = Field(True, description="Whether to use result cache")

class ChainOfThoughtRequest(BaseModel):
    prompt: str = Field(..., description="Base prompt for chain-of-thought reasoning")
    num_steps: int = Field(5, description="Number of reasoning steps")
    context: Optional[str] = Field(None, description="Optional context information")
    model: Optional[str] = Field(None, description="Optional specific model to use")
    strategy: str = Field(ModelSelectionStrategy.QUALITY_OPTIMIZED, description="Model selection strategy")
    extraction_template: Optional[str] = Field(None, description="Optional template for extracting final answer")

class MultilingualGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Input prompt for content generation")
    language: str = Field(..., description="Target language code (ISO 639-1)")
    model: Optional[str] = Field(None, description="Optional specific model to use")
    use_cache: bool = Field(True, description="Whether to use result cache")

class ParallelQueryRequest(BaseModel):
    prompts: List[str] = Field(..., description="List of prompts to execute in parallel")
    combine_results: bool = Field(True, description="Whether to combine results")
    combination_prompt: Optional[str] = Field(None, description="Optional template for combining results")
    models: Optional[List[str]] = Field(None, description="Optional list of models to use")

class CreateTemplateRequest(BaseModel):
    name: str = Field(..., description="Template name")
    template: str = Field(..., description="Template text")
    description: Optional[str] = Field(None, description="Optional description")
    domain: str = Field("recruitment", description="Domain")
    tags: Optional[List[str]] = Field(None, description="Optional tags")
    parameters: Optional[List[str]] = Field(None, description="Optional list of required parameters")

class UpdateTemplateRequest(BaseModel):
    template_id: str = Field(..., description="Template ID to update")
    name: Optional[str] = Field(None, description="Updated template name")
    template: Optional[str] = Field(None, description="Updated template text")
    description: Optional[str] = Field(None, description="Updated description")
    domain: Optional[str] = Field(None, description="Updated domain")
    tags: Optional[List[str]] = Field(None, description="Updated tags")

# API Endpoints
@router.post("/generate/content", summary="Generate content with advanced LLM")
async def generate_content(request: ContentGenerationRequest):
    """
    Generate content using the optimal LLM with advanced capabilities.
    This endpoint automatically selects the best model for the task unless specified.
    """
    if not advanced_llm_service:
        raise HTTPException(status_code=503, detail="Advanced LLM Service is not available")
    
    try:
        result = advanced_llm_service.generate_content(
            prompt=request.prompt,
            model=request.model,
            use_cache=request.use_cache,
            strategy=request.strategy,
            task_type=request.task_type,
            max_output_tokens=request.max_output_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k
        )
        
        return {
            "content": result,
            "model": request.model or "auto-selected",
            "task_type": request.task_type,
            "strategy": request.strategy
        }
    except Exception as e:
        logger.error(f"Error in generate_content: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/template", summary="Generate content using a prompt template")
async def generate_with_template(request: TemplateGenerationRequest):
    """
    Generate content using a pre-defined prompt template from the library.
    """
    if not advanced_llm_service or not prompt_manager:
        raise HTTPException(status_code=503, detail="Advanced LLM Services are not available")
    
    # Check if template exists
    template = prompt_manager.get_template(request.template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {request.template_id}")
    
    try:
        result = advanced_llm_service.generate_with_prompt_template(
            template_id=request.template_id,
            params=request.parameters,
            model=request.model,
            use_cache=request.use_cache,
            strategy=request.strategy,
            task_type=request.task_type
        )
        
        return {
            "content": result,
            "template_id": request.template_id,
            "template_name": template.name,
            "model": request.model or "auto-selected"
        }
    except KeyError as e:
        # Missing template parameter
        logger.error(f"Template parameter error: {e}")
        raise HTTPException(status_code=400, detail=f"Missing required parameter: {str(e)}")
    except Exception as e:
        logger.error(f"Error in generate_with_template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/context_aware", summary="Generate with context-aware prompting")
async def generate_with_context(request: ContextAwareGenerationRequest):
    """
    Generate content with context-enhanced prompting for more informed responses.
    Automatically retrieves relevant context based on the query.
    """
    if not advanced_llm_service or not prompt_manager:
        raise HTTPException(status_code=503, detail="Advanced LLM Services are not available")
    
    # Check if template exists
    template = prompt_manager.get_template(request.template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {request.template_id}")
    
    try:
        result = advanced_llm_service.generate_with_context(
            query=request.query,
            template_id=request.template_id,
            params=request.parameters,
            domain=request.domain,
            model=request.model,
            use_cache=request.use_cache,
            strategy=request.strategy,
            task_type=request.task_type
        )
        
        return {
            "content": result["content"],
            "context_info": {
                "sources": result["context_info"]["sources"],
                "relevance_score": result["context_info"]["relevance_score"],
                "token_count": result["context_info"]["token_count"],
                "cached": result["context_info"]["cached"]
            },
            "model": result["model"],
            "cache_hit": result["cache_hit"]
        }
    except KeyError as e:
        logger.error(f"Parameter error: {e}")
        raise HTTPException(status_code=400, detail=f"Missing required parameter: {str(e)}")
    except Exception as e:
        logger.error(f"Error in generate_with_context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/chain_of_thought", summary="Generate with chain-of-thought reasoning")
async def generate_chain_of_thought(request: ChainOfThoughtRequest):
    """
    Generate a response using chain-of-thought reasoning for complex questions.
    Returns both the step-by-step reasoning and the final conclusion.
    """
    if not advanced_llm_service:
        raise HTTPException(status_code=503, detail="Advanced LLM Service is not available")
    
    try:
        result = advanced_llm_service.generate_chain_of_thought(
            prompt=request.prompt,
            num_steps=request.num_steps,
            context=request.context,
            model=request.model,
            strategy=request.strategy,
            extraction_template=request.extraction_template
        )
        
        return {
            "reasoning": result["reasoning"],
            "steps": result["steps"],
            "conclusion": result["conclusion"],
            "model": result["model"]
        }
    except Exception as e:
        logger.error(f"Error in generate_chain_of_thought: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/multilingual", summary="Generate content in a specific language")
async def generate_multilingual(request: MultilingualGenerationRequest):
    """
    Generate content optimized for a specific language.
    """
    if not advanced_llm_service:
        raise HTTPException(status_code=503, detail="Advanced LLM Service is not available")
    
    try:
        result = advanced_llm_service.generate_multilingual(
            prompt=request.prompt,
            language=request.language,
            model=request.model,
            use_cache=request.use_cache
        )
        
        return {
            "content": result,
            "language": request.language,
            "model": request.model or "auto-selected"
        }
    except Exception as e:
        logger.error(f"Error in generate_multilingual: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/parallel", summary="Execute multiple prompts in parallel")
async def parallel_query(request: ParallelQueryRequest):
    """
    Execute multiple prompts in parallel and optionally combine results.
    Useful for gathering multiple perspectives or breaking down complex tasks.
    """
    if not advanced_llm_service:
        raise HTTPException(status_code=503, detail="Advanced LLM Service is not available")
    
    try:
        result = advanced_llm_service.parallel_query(
            prompts=request.prompts,
            combine_results=request.combine_results,
            combination_prompt=request.combination_prompt,
            models=request.models
        )
        
        return {
            "result": result,
            "combined": request.combine_results,
            "prompt_count": len(request.prompts)
        }
    except Exception as e:
        logger.error(f"Error in parallel_query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Prompt Template Management
@router.get("/templates", summary="List all prompt templates")
async def list_templates(
    domain: Optional[str] = None,
    tag: Optional[str] = None
):
    """
    List all prompt templates, optionally filtered by domain or tag.
    """
    if not prompt_manager:
        raise HTTPException(status_code=503, detail="Prompt Manager is not available")
    
    templates = prompt_manager.templates.values()
    
    # Apply filters if provided
    if domain:
        templates = [t for t in templates if t.domain == domain]
    if tag:
        templates = [t for t in templates if tag in t.tags]
    
    # Convert to dict for response
    template_list = [t.to_dict() for t in templates]
    
    return {"templates": template_list, "count": len(template_list)}

@router.get("/templates/{template_id}", summary="Get a specific template")
async def get_template(template_id: str):
    """
    Get a specific prompt template by ID.
    """
    if not prompt_manager:
        raise HTTPException(status_code=503, detail="Prompt Manager is not available")
    
    template = prompt_manager.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
    
    return template.to_dict()

@router.post("/templates", summary="Create a new prompt template")
async def create_template(request: CreateTemplateRequest):
    """
    Create a new prompt template.
    """
    if not prompt_manager:
        raise HTTPException(status_code=503, detail="Prompt Manager is not available")
    
    try:
        template = prompt_manager.create_template(
            name=request.name,
            template=request.template,
            description=request.description,
            domain=request.domain,
            tags=request.tags,
            parameters=request.parameters
        )
        
        return template.to_dict()
    except Exception as e:
        logger.error(f"Error creating template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/templates/{template_id}", summary="Update a prompt template")
async def update_template(template_id: str, request: UpdateTemplateRequest):
    """
    Update an existing prompt template.
    """
    if not prompt_manager:
        raise HTTPException(status_code=503, detail="Prompt Manager is not available")
    
    # Validate template exists
    if not prompt_manager.get_template(template_id):
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
    
    # Create updates dict (only non-None values)
    updates = {k: v for k, v in request.dict().items() if v is not None and k != "template_id"}
    
    try:
        updated_template = prompt_manager.update_template(template_id, **updates)
        if not updated_template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
        
        return updated_template.to_dict()
    except Exception as e:
        logger.error(f"Error updating template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/templates/{template_id}", summary="Delete a prompt template")
async def delete_template(template_id: str):
    """
    Delete a prompt template.
    """
    if not prompt_manager:
        raise HTTPException(status_code=503, detail="Prompt Manager is not available")
    
    success = prompt_manager.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
    
    return {"status": "success", "message": f"Template {template_id} deleted"}

# Metrics and Diagnostics
@router.get("/metrics", summary="Get Advanced LLM service metrics")
async def get_metrics():
    """
    Get metrics for the Advanced LLM service.
    """
    if not advanced_llm_service:
        raise HTTPException(status_code=503, detail="Advanced LLM Service is not available")
    
    metrics = advanced_llm_service.get_metrics()
    
    return metrics

logger.info("Advanced LLM API routes defined")
