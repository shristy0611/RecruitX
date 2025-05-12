"""
Multilingual skill extractor for RecruitPro AI.

This module provides multilingual skill extraction capabilities using
Gemma 3's language capabilities for global talent pools.
"""

import logging
import json
import re
from typing import Dict, List, Set, Optional, Any, Union
import spacy
from spacy.language import Language

from src.skills.extractors.base_extractor import SkillExtractor, Skill
from src.skills.extractors.enhanced_extractor import EnhancedSkillExtractor
from src.llm.gemma_service import GemmaService

# Configure logging
logger = logging.getLogger(__name__)

# Supported languages with their SpaCy models
SUPPORTED_LANGUAGES = {
    "en": "en_core_web_sm",   # English
    "ja": "ja_core_news_lg",  # Japanese
    "de": "de_core_news_lg",  # German
    "fr": "fr_core_news_lg",  # French
    "es": "es_core_news_lg",  # Spanish
    "zh": "zh_core_web_lg",   # Chinese
}

# Language names for prompts
LANGUAGE_NAMES = {
    "en": "English",
    "ja": "Japanese",
    "de": "German",
    "fr": "French",
    "es": "Spanish", 
    "zh": "Chinese",
}


class MultilingualSkillExtractor(SkillExtractor):
    """
    Multilingual skill extractor using Gemma 3 for global talent pools.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        preload_languages: Optional[List[str]] = None
    ):
        """
        Initialize the multilingual skill extractor.
        
        Args:
            config: Optional configuration dictionary
            preload_languages: Optional list of language codes to preload
        """
        super().__init__(config)
        
        # Get configuration values
        if config:
            preload_languages = config.get("preload_languages", preload_languages)
        
        # Initialize Gemma service
        self.gemma_service = None
        try:
            self.gemma_service = GemmaService()
        except Exception as e:
            logger.warning(f"Failed to initialize GemmaService: {e}")
        
        # Initialize language-specific extractors
        self.extractors = {}
        
        # Preload English by default
        self._load_language("en")
        
        # Preload requested languages
        if preload_languages:
            for lang in preload_languages:
                if lang != "en":  # already loaded
                    self._load_language(lang)
    
    def extract_skills(
        self, 
        text: str, 
        language: str = "en"
    ) -> List[Skill]:
        """
        Extract skills from text in the specified language.
        
        Args:
            text: Text to extract skills from
            language: Language code (ISO 639-1)
            
        Returns:
            List of extracted Skill objects
        """
        # Normalize language code
        language = language.lower()
        
        # Default to English if language not specified or not supported
        if language not in SUPPORTED_LANGUAGES:
            logger.warning(f"Language '{language}' not supported. Falling back to English.")
            language = "en"
        
        # Preprocess text
        processed_text = self.preprocess_text(text)
        
        # Use language-specific extraction if available
        if language in self.extractors:
            spacy_skills = self._extract_skills_spacy(processed_text, language)
        else:
            # If SpaCy model isn't loaded, try to load it
            try:
                self._load_language(language)
                spacy_skills = self._extract_skills_spacy(processed_text, language)
            except Exception as e:
                logger.error(f"Error loading language model for {language}: {e}")
                spacy_skills = self._extract_skills_simple(processed_text)
        
        # LLM-based extraction works for all languages
        llm_skills = self._extract_skills_llm(processed_text, language)
        
        # Combine, merge and categorize skills
        all_skills = spacy_skills + llm_skills
        merged_skills = self.merge_skills(all_skills)
        
        # Translate skill names to English for consistency (if not already in English)
        if language != "en":
            merged_skills = self._translate_skills_to_english(merged_skills, language)
        
        return merged_skills
    
    def _load_language(self, language: str) -> bool:
        """
        Load language-specific resources.
        
        Args:
            language: Language code to load
            
        Returns:
            Boolean indicating success
        """
        if language in self.extractors:
            return True
            
        if language not in SUPPORTED_LANGUAGES:
            logger.warning(f"Language '{language}' not supported")
            return False
            
        model_name = SUPPORTED_LANGUAGES[language]
        
        try:
            # Try to load the SpaCy model
            try:
                nlp = spacy.load(model_name)
            except OSError:
                logger.warning(f"SpaCy model '{model_name}' not found. Downloading...")
                spacy.cli.download(model_name)
                nlp = spacy.load(model_name)
            
            # Store the model
            self.extractors[language] = nlp
            logger.info(f"Loaded SpaCy model for {language}: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading language model for {language}: {e}")
            return False
    
    def _extract_skills_simple(self, text: str) -> List[Skill]:
        """
        Simple keyword-based skill extraction for fallback when SpaCy isn't available.
        
        Args:
            text: Text to extract skills from
            
        Returns:
            List of skills extracted using simple keyword matching
        """
        skills = []
        text_lower = text.lower()
        
        # Common technical skills to look for
        common_skills = [
            "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
            "React", "Angular", "Vue", "Node.js", "Django", "Flask", "Spring",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "SQL", "MySQL", "PostgreSQL",
            "MongoDB", "Redis", "TensorFlow", "PyTorch", "Machine Learning", "AI"
        ]
        
        # Look for skills in text
        for skill_name in common_skills:
            if skill_name.lower() in text_lower:
                skills.append(Skill(
                    name=skill_name,
                    confidence=0.7,
                    category="technical",
                    source="simple_match"
                ))
        
        return skills
    
    def _extract_skills_spacy(
        self, 
        text: str, 
        language: str
    ) -> List[Skill]:
        """
        Extract skills using SpaCy NER.
        
        Args:
            text: Preprocessed text
            language: Language code
            
        Returns:
            List of skills extracted by SpaCy
        """
        if language not in self.extractors:
            return []
            
        nlp = self.extractors[language]
        doc = nlp(text)
        skills = []
        
        # Extract entities that might be skills
        for ent in doc.ents:
            # Entity types vary by language model, but we look for organizations,
            # products, and miscellaneous entities that might be skills
            relevant_labels = {"ORG", "PRODUCT", "MISC", "SKILL"}
            
            if ent.label_ in relevant_labels or (
                language == "ja" and ent.label_ in {"ARTIFACT"}
            ):
                # Adjust confidence based on entity type and length
                # Longer entity names (3+ tokens) are less likely to be skills
                base_confidence = 0.7
                if len(ent) > 2:
                    base_confidence -= 0.1 * min(len(ent) - 2, 3)  # Reduce confidence for longer entities
                
                # Create skill with context
                context_start = max(0, ent.start_char - 40)
                context_end = min(len(text), ent.end_char + 40)
                context = text[context_start:context_end]
                
                skill = Skill(
                    name=ent.text,
                    confidence=base_confidence,
                    source="spacy_" + language,
                    context=context,
                    metadata={"language": language, "entity_type": ent.label_}
                )
                skills.append(skill)
        
        # Also extract noun chunks as potential skills
        for chunk in doc.noun_chunks:
            # Skip if too long (likely not a skill)
            if len(chunk.text.split()) > 4:
                continue
            
            # Skip if already added from entities
            if any(s.name == chunk.text for s in skills):
                continue
            
            # Create skill
            skill = Skill(
                name=chunk.text,
                confidence=0.6,  # Lower confidence for noun chunks
                source="spacy_noun_chunk_" + language,
                context=chunk.text,
                metadata={"language": language}
            )
            skills.append(skill)
        
        return skills
    
    def _extract_skills_llm(
        self, 
        text: str, 
        language: str
    ) -> List[Skill]:
        """
        Extract skills using Gemma API with language-specific prompts.
        
        Args:
            text: Preprocessed text
            language: Language code
            
        Returns:
            List of skills extracted by Gemma
        """
        if not self.gemma_service:
            logger.warning("Gemma service not initialized, skipping LLM extraction")
            return []
        
        try:
            # Truncate text if too long
            max_chars = 5000
            if len(text) > max_chars:
                truncated_text = text[:max_chars] + "..."
                logger.info(f"Truncated text from {len(text)} to {max_chars} characters for LLM extraction")
            else:
                truncated_text = text
            
            # Get language name for prompt
            language_name = LANGUAGE_NAMES.get(language, language)
            
            # Create the prompt
            prompt = f"""
            Extract all professional skills from the following {language_name} text. 
            Focus on technical skills, soft skills, and domain expertise.
            
            For each skill you extract, provide:
            1. The original skill name as it appears in the text
            2. The translated skill name in English (if the original is not in English)
            3. The skill category (technical, domain, or soft)
            4. A confidence score (0.0-1.0)
            
            Respond in JSON format like this:
            {{
              "skills": [
                {{
                  "original_name": "Python",
                  "english_name": "Python",
                  "category": "technical",
                  "confidence": 0.95
                }},
                {{
                  "original_name": "リーダーシップ",
                  "english_name": "Leadership",
                  "category": "soft",
                  "confidence": 0.8
                }}
              ]
            }}
            
            TEXT:
            {truncated_text}
            """
            
            # Call Gemma API
            response = self.gemma_service.generate_content(prompt)
            skills_data = self._extract_json_from_response(response)
            
            # Convert to skill objects
            skills = []
            for skill_info in skills_data.get("skills", []):
                # Use English name if available, otherwise use original
                skill_name = skill_info.get("english_name") or skill_info.get("original_name", "")
                original_name = skill_info.get("original_name", "")
                
                # Skip if no name was extracted
                if not skill_name:
                    continue
                
                skill = Skill(
                    name=skill_name,
                    confidence=float(skill_info.get("confidence", 0.5)),
                    category=skill_info.get("category"),
                    source="gemma_" + language,
                    metadata={
                        "language": language,
                        "original_name": original_name,
                        "llm_extracted": True
                    }
                )
                skills.append(skill)
            
            return skills
            
        except Exception as e:
            logger.error(f"Error extracting skills with Gemma API: {e}")
            return []
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """
        Extract JSON object from LLM response.
        
        Args:
            response: LLM response text
            
        Returns:
            Parsed JSON object or empty dict on failure
        """
        try:
            # Try direct JSON parsing
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON pattern in the response
            json_pattern = r'({.*})'
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            if matches:
                for match in matches:
                    try:
                        return json.loads(match)
                    except json.JSONDecodeError:
                        continue
            
            logger.warning("Failed to extract JSON from LLM response")
            return {"skills": []}
    
    def _translate_skills_to_english(
        self, 
        skills: List[Skill], 
        source_language: str
    ) -> List[Skill]:
        """
        Translate skill names to English for consistency.
        
        Args:
            skills: List of skills to translate
            source_language: Source language code
            
        Returns:
            List of skills with translated names
        """
        # Skip if no Gemma service or source is already English
        if not self.gemma_service or source_language == "en":
            return skills
        
        translated_skills = []
        
        for skill in skills:
            # Skip if already in English or if already has a translation
            if skill.metadata.get("english_name") or skill.metadata.get("language") == "en":
                translated_skills.append(skill)
                continue
            
            try:
                # Get original name
                original_name = skill.metadata.get("original_name", skill.name)
                
                # Translate the skill name
                english_name = self.gemma_service.translate_text(
                    text=original_name,
                    source_language=source_language,
                    target_language="en"
                )
                
                # Update metadata with the translation info
                skill.metadata["original_name"] = original_name
                skill.metadata["english_name"] = english_name
                skill.metadata["original_language"] = source_language
                
                # Update the skill name to English
                skill.name = english_name
                
                translated_skills.append(skill)
                
            except Exception as e:
                logger.error(f"Error translating skill name: {e}")
                # Keep the original skill
                translated_skills.append(skill)
        
        return translated_skills
