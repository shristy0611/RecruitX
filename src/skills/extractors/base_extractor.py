"""
Base skill extractor for RecruitPro AI.

This module defines the base interface for all skill extractors.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Set, Optional, Any, Union
import logging

# Configure logging
logger = logging.getLogger(__name__)


class Skill:
    """Represents a detected skill with metadata."""
    
    def __init__(
        self,
        name: str,
        confidence: float = 1.0,
        category: Optional[str] = None,
        source: Optional[str] = None,
        context: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a Skill object.
        
        Args:
            name: The name of the skill
            confidence: Confidence score (0.0-1.0) of the extraction
            category: Optional category of the skill (e.g., "technical", "soft")
            source: Optional source of extraction (e.g., "spacy", "llm")
            context: Optional surrounding context where the skill was found
            aliases: Optional list of alternative names for the skill
        """
        self.name = name
        self.confidence = confidence
        self.category = category
        self.source = source
        self.context = context
        self.aliases = aliases or []
        self.metadata = metadata or {}
    
    def __eq__(self, other):
        """Check if two skills are equal by name."""
        if isinstance(other, Skill):
            return self.name.lower() == other.name.lower()
        return False
    
    def __hash__(self):
        """Hash based on lowercase name for deduplication."""
        return hash(self.name.lower())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert skill to dictionary representation."""
        return {
            "name": self.name,
            "confidence": self.confidence,
            "category": self.category,
            "source": self.source,
            "context": self.context,
            "aliases": self.aliases,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        """Create a Skill object from a dictionary."""
        return cls(
            name=data["name"],
            confidence=data.get("confidence", 1.0),
            category=data.get("category"),
            source=data.get("source"),
            context=data.get("context"),
            aliases=data.get("aliases", []),
            metadata=data.get("metadata", {})
        )


class SkillExtractor(ABC):
    """Base class for skill extractors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the skill extractor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        logger.info(f"Initialized {self.__class__.__name__} with config: {self.config}")
    
    @abstractmethod
    def extract_skills(
        self, 
        text: str, 
        language: str = "en"
    ) -> List[Skill]:
        """
        Extract skills from text.
        
        Args:
            text: Text to extract skills from
            language: Language code (ISO 639-1)
            
        Returns:
            List of extracted Skill objects
        """
        pass
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text before skill extraction.
        
        Args:
            text: Text to preprocess
            
        Returns:
            Preprocessed text
        """
        # Basic preprocessing: strip and normalize whitespace
        processed_text = " ".join(text.strip().split())
        return processed_text
    
    def merge_skills(self, skills: List[Skill]) -> List[Skill]:
        """
        Merge duplicate skills preserving highest confidence.
        
        Args:
            skills: List of skills to merge
            
        Returns:
            Deduplicated list of skills
        """
        if not skills:
            return []
            
        # Use a dictionary to track the highest confidence for each skill name
        merged_skills = {}
        
        for skill in skills:
            skill_key = skill.name.lower()
            
            if skill_key in merged_skills:
                # Keep the higher confidence version
                if skill.confidence > merged_skills[skill_key].confidence:
                    merged_skills[skill_key] = skill
            else:
                merged_skills[skill_key] = skill
        
        return list(merged_skills.values())
    
    def filter_skills(
        self, 
        skills: List[Skill], 
        min_confidence: float = 0.0,
        categories: Optional[List[str]] = None
    ) -> List[Skill]:
        """
        Filter skills based on confidence and categories.
        
        Args:
            skills: List of skills to filter
            min_confidence: Minimum confidence threshold (0.0-1.0)
            categories: Optional list of categories to include
            
        Returns:
            Filtered list of skills
        """
        filtered_skills = [skill for skill in skills if skill.confidence >= min_confidence]
        
        if categories:
            filtered_skills = [
                skill for skill in filtered_skills 
                if skill.category and skill.category in categories
            ]
            
        return filtered_skills
