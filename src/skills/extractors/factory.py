"""
Skill extractor factory for RecruitPro AI.

This module provides a factory for creating skill extractors
based on specified types and configurations.
"""

import logging
from typing import Dict, Any, Optional, Type

from src.skills.extractors.base_extractor import SkillExtractor
from src.skills.extractors.enhanced_extractor import EnhancedSkillExtractor
from src.skills.extractors.multilingual_extractor import MultilingualSkillExtractor
from src.skills.extractors.taxonomy_extractor import TaxonomySkillExtractor
from src.skills.taxonomy.taxonomy_manager import SkillsTaxonomyManager

# Configure logging
logger = logging.getLogger(__name__)


class SkillExtractorFactory:
    """Factory for creating skill extractors."""
    
    # Static references to maintain singleton instances
    _extractors = {}
    _taxonomy_manager = None
    
    @classmethod
    def get_extractor(
        cls,
        extractor_type: str = "taxonomy",
        config: Optional[Dict[str, Any]] = None
    ) -> SkillExtractor:
        """
        Get a skill extractor instance.
        
        Args:
            extractor_type: Type of extractor (enhanced, multilingual, taxonomy)
            config: Optional configuration for the extractor
            
        Returns:
            SkillExtractor instance
            
        Raises:
            ValueError: If extractor_type is unknown
        """
        config = config or {}
        
        # Return cached instance if available
        if extractor_type in cls._extractors:
            return cls._extractors[extractor_type]
        
        # Create new instance
        if extractor_type == "enhanced":
            # Instead of passing specific parameters, create a config dictionary
            enhanced_config = config.copy()
            enhanced_config.update({
                "gemini_model": config.get("gemini_model", "gemini-pro"),
                "api_key": config.get("api_key"),
            })
            extractor = EnhancedSkillExtractor(config=enhanced_config)
        elif extractor_type == "multilingual":
            # Create a config dictionary for the multilingual extractor
            multilingual_config = config.copy()
            multilingual_config.update({
                "gemma_model": config.get("gemma_model", "gemma-3"),
                "api_key": config.get("api_key"),
                "preload_languages": config.get("preload_languages", None)
            })
            extractor = MultilingualSkillExtractor(config=multilingual_config)
        elif extractor_type == "taxonomy":
            # Ensure taxonomy manager exists
            if not cls._taxonomy_manager:
                cls._taxonomy_manager = SkillsTaxonomyManager(
                    taxonomies_dir=config.get("taxonomies_dir")
                )
            
            # Get required parameters
            domains = config.get("domains", ["tech", "soft_skills"])
            
            # Create a basic extractor with just the essential parameters
            extractor = TaxonomySkillExtractor(
                taxonomy_manager=cls._taxonomy_manager,
                domains=domains
            )
            
            # Manually set any additional parameters
            if "spacy_model" in config:
                extractor.spacy_model = config["spacy_model"]
            if "gemini_model" in config:
                extractor.gemini_model = config["gemini_model"]
            if "api_key" in config:
                extractor.api_key = config["api_key"]
        else:
            raise ValueError(f"Unknown extractor type: {extractor_type}")
        
        # Cache and return
        cls._extractors[extractor_type] = extractor
        return extractor
    
    @classmethod
    def get_taxonomy_manager(cls) -> SkillsTaxonomyManager:
        """
        Get the singleton taxonomy manager instance.
        
        Returns:
            SkillsTaxonomyManager instance
        """
        if not cls._taxonomy_manager:
            cls._taxonomy_manager = SkillsTaxonomyManager()
        
        return cls._taxonomy_manager
