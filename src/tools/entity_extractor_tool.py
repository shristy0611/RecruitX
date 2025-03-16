from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from flair.data import Sentence
from flair.models import SequenceTagger
import numpy as np
from google.cloud import aiplatform

from app.tool.base import BaseTool, ToolResult
from ..utils.gemini_manager import GeminiKeyManager

class EntityExtractorInput(BaseModel):
    """Input schema for entity extraction."""
    text: str = Field(..., description="Text to extract entities from")
    entity_types: List[str] = Field(
        default=["SKILL", "EXPERIENCE", "EDUCATION", "COMPANY", "ROLE"],
        description="Types of entities to extract"
    )
    use_flair_validation: bool = Field(
        default=True,
        description="Whether to use FLAIR for validation"
    )

class EntityExtractorTool(BaseTool):
    """Tool for extracting entities using Gemini and FLAIR."""
    
    name: str = "entity_extractor"
    description: str = "Extract entities from text using Gemini and FLAIR"
    parameters: Dict = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to extract entities from"
            },
            "entity_types": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Types of entities to extract",
                "default": ["SKILL", "EXPERIENCE", "EDUCATION", "COMPANY", "ROLE"]
            },
            "use_flair_validation": {
                "type": "boolean",
                "description": "Whether to use FLAIR for validation",
                "default": True
            }
        },
        "required": ["text"]
    }
    
    def __init__(self):
        super().__init__()
        self.gemini_manager = GeminiKeyManager()
        self.pro_model = aiplatform.TextGenerationModel.from_pretrained("gemini-2.0-pro-exp-02-05")
        self.flair_tagger = SequenceTagger.load('flair/ner-english-large')
        
    async def execute(self, **kwargs) -> ToolResult:
        """Execute entity extraction."""
        try:
            input_data = EntityExtractorInput(**kwargs)
            
            # Extract entities using Gemini
            gemini_entities = await self._extract_with_gemini(
                input_data.text,
                input_data.entity_types
            )
            
            # Validate with FLAIR if requested
            if input_data.use_flair_validation:
                flair_entities = await self._extract_with_flair(input_data.text)
                entities = await self._merge_entities(gemini_entities, flair_entities)
            else:
                entities = gemini_entities
                
            return ToolResult(output=entities)
            
        except Exception as e:
            return ToolResult(error=f"Error extracting entities: {str(e)}")
    
    async def _extract_with_gemini(self, text: str, entity_types: List[str]) -> List[Dict[str, Any]]:
        """Extract entities using Gemini."""
        api_key = self.gemini_manager.get_next_key()
        if not api_key:
            raise ValueError("No available Gemini API key")
            
        try:
            prompt = f"""
            Extract entities from the following text. For each entity, provide:
            - Type (one of: {', '.join(entity_types)})
            - Value (the actual text)
            - Confidence (a float between 0 and 1)
            
            Format the response as a JSON array of objects with fields: type, value, confidence
            
            Text:
            {text}
            """
            
            response = await self.pro_model.predict(prompt)
            self.gemini_manager.log_api_call(api_key, "entity_extraction", True)
            
            # Parse JSON response
            entities = eval(response.text)  # Safe since we control the prompt format
            return entities
            
        except Exception as e:
            self.gemini_manager.log_api_call(api_key, "entity_extraction", False, str(e))
            raise
    
    async def _extract_with_flair(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using FLAIR."""
        sentence = Sentence(text)
        self.flair_tagger.predict(sentence)
        
        entities = []
        for entity in sentence.get_spans('ner'):
            entities.append({
                'type': entity.tag,
                'value': entity.text,
                'confidence': float(entity.score),
                'source': 'flair'
            })
            
        return entities
    
    async def _merge_entities(self, gemini_entities: List[Dict], flair_entities: List[Dict]) -> List[Dict]:
        """Merge and deduplicate entities from different sources."""
        merged = {}
        
        # Add Gemini entities
        for entity in gemini_entities:
            key = (entity['type'], entity['value'].lower())
            entity['source'] = 'gemini'
            merged[key] = entity
        
        # Add or update with FLAIR entities
        for entity in flair_entities:
            key = (entity['type'], entity['value'].lower())
            if key not in merged or entity['confidence'] > merged[key]['confidence']:
                merged[key] = entity
                
        return list(merged.values()) 