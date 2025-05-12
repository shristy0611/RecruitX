"""
API routes for skill extraction and taxonomy operations.

This module defines the FastAPI routes for accessing skill extraction
and skills taxonomy functionality.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from pydantic import BaseModel, Field
from src.skills.extractors.base_extractor import Skill
from src.skills.extractors.factory import SkillExtractorFactory

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/skills",
    tags=["skills"],
    responses={404: {"description": "Not found"}},
)

# Get factory references
taxonomy_manager = SkillExtractorFactory.get_taxonomy_manager()


# Request/response models
class ExtractSkillsRequest(BaseModel):
    """Request model for skill extraction."""
    text: str = Field(..., description="Text to extract skills from")
    language: str = Field("en", description="Language of the text")
    extractor_type: str = Field("taxonomy", description="Type of extractor to use (enhanced, multilingual, taxonomy)")


class SkillModel(BaseModel):
    """Response model for a skill."""
    name: str = Field(..., description="Skill name")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    source: str = Field(..., description="Source of the skill extraction")
    metadata: Dict[str, Any] = Field({}, description="Additional metadata about the skill")


class ExtractSkillsResponse(BaseModel):
    """Response model for skill extraction."""
    skills: List[SkillModel] = Field(..., description="List of extracted skills")
    count: int = Field(..., description="Number of skills extracted")
    language: str = Field(..., description="Language of the text")
    extractor_type: str = Field(..., description="Type of extractor used")


class SkillTaxonomyResponse(BaseModel):
    """Response model for skill taxonomy information."""
    name: str = Field(..., description="Skill name")
    domain: str = Field(..., description="Domain of the skill")
    category: str = Field(..., description="Category of the skill")
    ancestors: List[str] = Field(..., description="Ancestor skills in hierarchy")
    descendants: List[str] = Field(..., description="Descendant skills in hierarchy")
    related_skills: List[str] = Field(..., description="Related skills")
    aliases: List[str] = Field(..., description="Alternative names for the skill")
    metadata: Dict[str, Any] = Field({}, description="Additional metadata about the skill")


class SkillSuggestionResponse(BaseModel):
    """Response model for skill suggestions."""
    suggestions: List[Dict[str, Any]] = Field(..., description="List of skill suggestions")
    count: int = Field(..., description="Number of suggestions")
    partial_text: str = Field(..., description="Partial text used for suggestions")


class TaxonomyDomainResponse(BaseModel):
    """Response model for taxonomy domains."""
    domains: List[str] = Field(..., description="List of available taxonomy domains")


# Dependency for getting the appropriate extractor
def get_extractor(extractor_type: str = "taxonomy"):
    """Get the appropriate skill extractor based on type."""
    try:
        return SkillExtractorFactory.get_extractor(extractor_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/extract", response_model=ExtractSkillsResponse)
async def extract_skills(
    request: ExtractSkillsRequest,
    extractor=Depends(get_extractor)
):
    """
    Extract skills from text.
    
    Extracts skills from the provided text using the specified extractor type.
    """
    try:
        # Extract skills
        skills = extractor.extract_skills(
            text=request.text,
            language=request.language
        )
        
        # Convert to response model
        skill_models = [
            SkillModel(
                name=skill.name,
                confidence=skill.confidence,
                source=skill.source,
                metadata=skill.metadata
            )
            for skill in skills
        ]
        
        return ExtractSkillsResponse(
            skills=skill_models,
            count=len(skill_models),
            language=request.language,
            extractor_type=request.extractor_type
        )
        
    except Exception as e:
        logger.error(f"Error extracting skills: {e}")
        raise HTTPException(status_code=500, detail=f"Error extracting skills: {str(e)}")


@router.get("/taxonomy/domains", response_model=TaxonomyDomainResponse)
async def get_taxonomy_domains():
    """Get a list of available taxonomy domains."""
    try:
        domains = taxonomy_manager.get_all_domains()
        
        return TaxonomyDomainResponse(
            domains=domains
        )
        
    except Exception as e:
        logger.error(f"Error getting taxonomy domains: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting taxonomy domains: {str(e)}")


@router.get("/taxonomy/skill/{domain}/{skill_name}", response_model=SkillTaxonomyResponse)
async def get_skill_taxonomy(
    domain: str,
    skill_name: str
):
    """
    Get taxonomy information for a specific skill.
    
    Retrieves detailed taxonomy information for the specified skill.
    """
    try:
        # Get taxonomy extractor
        taxonomy_extractor = SkillExtractorFactory.get_extractor("taxonomy")
        
        # Classify the skill
        classification = taxonomy_extractor.classify_skill(skill_name)
        
        if classification["domain"] == "unknown":
            raise HTTPException(status_code=404, detail=f"Skill not found in taxonomy: {skill_name}")
        
        return SkillTaxonomyResponse(**classification)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill taxonomy: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting skill taxonomy: {str(e)}")


@router.get("/suggest", response_model=SkillSuggestionResponse)
async def suggest_skills(
    partial_text: str = Query(..., description="Partial skill name"),
    max_suggestions: int = Query(10, description="Maximum number of suggestions")
):
    """
    Get skill suggestions based on partial text.
    
    Returns a list of skills that match the partial text.
    """
    try:
        # Get taxonomy extractor
        taxonomy_extractor = SkillExtractorFactory.get_extractor("taxonomy")
        
        suggestions = taxonomy_extractor.get_skill_suggestions(
            partial_text=partial_text,
            max_suggestions=max_suggestions
        )
        
        return SkillSuggestionResponse(
            suggestions=suggestions,
            count=len(suggestions),
            partial_text=partial_text
        )
        
    except Exception as e:
        logger.error(f"Error getting skill suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting skill suggestions: {str(e)}")
