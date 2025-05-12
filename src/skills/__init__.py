"""
Skills extraction module for RecruitPro AI.

This module provides enhanced skill extraction capabilities with
domain-specific NER and multilingual support.
"""

from src.skills.extractors.base_extractor import SkillExtractor, Skill
from src.skills.extractors.enhanced_extractor import EnhancedSkillExtractor
from src.skills.extractors.multilingual_extractor import MultilingualSkillExtractor
from src.skills.extractors.taxonomy_extractor import TaxonomySkillExtractor
from src.skills.extractors.factory import SkillExtractorFactory
from src.skills.taxonomy.taxonomy_manager import SkillsTaxonomyManager

__all__ = [
    'Skill',
    'SkillExtractor',
    'EnhancedSkillExtractor',
    'MultilingualSkillExtractor',
    'TaxonomySkillExtractor',
    'SkillExtractorFactory',
    'SkillsTaxonomyManager'
]
