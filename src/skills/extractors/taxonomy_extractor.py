"""
Taxonomy-aware skill extractor that uses the skills taxonomy manager.

This module provides a skill extractor that extracts skills from text
and enriches them with taxonomy information.
"""

import logging
from typing import List, Dict, Any, Optional, Set
import re
import spacy
from spacy.matcher import PhraseMatcher
from google.generativeai import GenerativeModel

from src.skills.extractors.base_extractor import SkillExtractor, Skill
from src.skills.taxonomy.taxonomy_manager import SkillsTaxonomyManager

# Configure logging
logger = logging.getLogger(__name__)


class TaxonomySkillExtractor(SkillExtractor):
    """Taxonomy-aware skill extractor that enriches skills with taxonomy data."""
    
    def __init__(
        self,
        taxonomy_manager: SkillsTaxonomyManager,
        domains: List[str] = ["tech", "soft_skills"],
        spacy_model: str = "en_core_web_sm",
        gemini_model: str = "gemini-pro",
        api_key: Optional[str] = None
    ):
        """
        Initialize the taxonomy-aware skill extractor.
        
        Args:
            taxonomy_manager: SkillsTaxonomyManager instance
            domains: List of taxonomy domains to use
            spacy_model: SpaCy model name to use for NER
            gemini_model: Gemini model name for LLM-based extraction
            api_key: Optional Gemini API key
        """
        super().__init__()
        self.taxonomy_manager = taxonomy_manager
        self.domains = domains
        
        # Check if domains are loaded
        for domain in domains:
            if domain not in taxonomy_manager.get_all_domains():
                logger.info(f"Loading taxonomy for domain: {domain}")
                # Try to load the domain, generate default if it doesn't exist
                if not taxonomy_manager.load_taxonomy(domain):
                    taxonomy_manager.generate_default_taxonomy(domain)
        
        # Initialize SpaCy
        try:
            self.nlp = spacy.load(spacy_model)
            self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
            self._update_matcher()
        except Exception as e:
            logger.error(f"Error loading SpaCy model: {e}")
            self.nlp = None
            self.matcher = None
        
        # Initialize Gemini
        try:
            self.gemini_model = GenerativeModel(gemini_model) if api_key else None
        except Exception as e:
            logger.error(f"Error initializing Gemini model: {e}")
            self.gemini_model = None
    
    def extract_skills(self, text: str, language: str = "en") -> List[Skill]:
        """
        Extract skills from text and enrich with taxonomy information.
        
        Args:
            text: Text to extract skills from
            language: Language of the text
            
        Returns:
            List of extracted skills with taxonomy information
        """
        # Use different extraction strategies
        skills_from_taxonomy = self._extract_skills_from_taxonomy(text, language)
        skills_from_gemini = self._extract_skills_from_gemini(text, language)
        
        # Merge skills (preferring taxonomy skills)
        # Combine skill lists first
        all_skills = skills_from_taxonomy + skills_from_gemini
        merged_skills = self.merge_skills(all_skills)
        
        # Enrich with taxonomy information
        for skill in merged_skills:
            self._enrich_with_taxonomy(skill)
        
        return merged_skills
    
    def _extract_skills_from_taxonomy(self, text: str, language: str) -> List[Skill]:
        """
        Extract skills based on the taxonomy using pattern matching.
        
        Args:
            text: Text to extract skills from
            language: Language of the text
            
        Returns:
            List of skills extracted from taxonomy
        """
        if not self.nlp or not self.matcher:
            logger.warning("SpaCy model not loaded, using fallback simple keyword extraction")
            return self._extract_skills_simple(text)
        
        skills = []
        doc = self.nlp(text)
        
        # Find matches using the phrase matcher
        matches = self.matcher(doc)
        skill_spans = {}  # Map span to skill to avoid duplicates
        
        # Process matches
        for match_id, start, end in matches:
            span = doc[start:end]
            skill_text = span.text
            
            # Get the skill name from the matcher
            skill_key = self.nlp.vocab.strings[match_id]
            domain, skill_name = skill_key.split(":", 1)
            
            # Convert span for this skill
            if span not in skill_spans or len(skill_text) > len(skill_spans[span][0]):
                skill_spans[span] = (skill_text, domain, skill_name)
        
        # Create Skill objects from spans
        for span, (skill_text, domain, skill_name) in skill_spans.items():
            # Create skill with taxonomy information
            skill = Skill(
                name=skill_name,
                confidence=0.9,  # High confidence for exact matches
                source="taxonomy",
                metadata={
                    "domain": domain,
                    "match_text": skill_text,
                    "taxonomy_validated": True
                }
            )
            skills.append(skill)
        
        return skills
    
    def _extract_skills_simple(self, text: str) -> List[Skill]:
        """
        Simple keyword-based skill extraction for testing or fallback.
        
        This method uses simple string matching against the taxonomy domains
        to extract skills when more sophisticated methods are unavailable.
        
        Args:
            text: Text to extract skills from
            
        Returns:
            List of skills extracted by keyword matching
        """
        skills = []
        text_lower = text.lower()
        
        # For each domain in the taxonomy
        for domain in self.domains:
            # Get flat taxonomy
            flat_taxonomy = self.taxonomy_manager.export_flat_taxonomy(domain)
            
            # For each skill, check if it's in the text
            for skill_name, skill_data in flat_taxonomy.items():
                if skill_name.lower() in text_lower:
                    # Create skill with taxonomy information
                    skill = Skill(
                        name=skill_name,
                        confidence=0.8,  # Lower confidence for simple matching
                        source="simple_match",
                        metadata={
                            "domain": domain,
                            "category": skill_data.get("category"),
                            "taxonomy_validated": True
                        }
                    )
                    skills.append(skill)
                    
                # Also check aliases
                for alias in skill_data.get("aliases", []):
                    if alias.lower() in text_lower and skill_name not in [s.name for s in skills]:
                        # Create skill with taxonomy information
                        skill = Skill(
                            name=skill_name,
                            confidence=0.75,  # Lower confidence for alias matching
                            source="simple_match_alias",
                            metadata={
                                "domain": domain,
                                "category": skill_data.get("category"),
                                "taxonomy_validated": True,
                                "matched_alias": alias
                            }
                        )
                        skills.append(skill)
                        break
        
        return skills
        
    def _extract_skills_from_gemini(self, text: str, language: str) -> List[Skill]:
        """
        Extract skills using Gemini API for unknown skills.
        
        Args:
            text: Text to extract skills from
            language: Language of the text
            
        Returns:
            List of skills extracted using Gemini
        """
        if not self.gemini_model:
            logger.warning("Gemini model not available, using fallback simple extraction")
            # We already extracted skills with the simple method in _extract_skills_from_taxonomy
            # if SpaCy was not available, so we can return empty list here
            return []
        
        try:
            # Define the prompt for skill extraction
            prompt = f"""
            Extract professional skills from the following text. Focus on technical skills, soft skills, 
            and domain expertise. For each skill, provide:
            1. The standardized skill name
            2. The skill category (technical, domain, or soft)
            3. A confidence score (0.0-1.0)
            
            Respond in JSON format like this:
            {{
              "skills": [
                {{"name": "Python", "category": "technical", "confidence": 0.95}},
                {{"name": "Project Management", "category": "soft", "confidence": 0.8}}
              ]
            }}
            
            TEXT:
            {text}
            """
            
            # Generate response from Gemini
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Extract JSON part from response
            import json
            import re
            
            # Try to find JSON block
            json_match = re.search(r'({.*})', response_text.replace('\n', ' '), re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    
                    # Convert to Skill objects
                    skills = []
                    for skill_data in data.get("skills", []):
                        skill = Skill(
                            name=skill_data.get("name"),
                            confidence=float(skill_data.get("confidence", 0.5)),
                            source="gemini",
                            metadata={
                                "category": skill_data.get("category"),
                                "taxonomy_validated": False
                            }
                        )
                        skills.append(skill)
                    
                    return skills
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse Gemini response as JSON: {response_text}")
            
            logger.warning("No valid JSON found in Gemini response")
            return []
            
        except Exception as e:
            logger.error(f"Error extracting skills with Gemini: {e}")
            return []
    
    def _enrich_with_taxonomy(self, skill: Skill) -> None:
        """
        Enrich a skill with taxonomy information.
        
        Args:
            skill: Skill to enrich
        """
        # Try to find the skill in all domains
        for domain in self.domains:
            taxonomy_skill = self.taxonomy_manager.find_skill(domain, skill.name)
            
            if taxonomy_skill:
                # Get taxonomy information
                hierarchy = self.taxonomy_manager.get_skill_hierarchy(domain, skill.name)
                related = self.taxonomy_manager.get_related_skills(domain, skill.name)
                
                # Update skill metadata
                skill.metadata.update({
                    "domain": domain,
                    "category": taxonomy_skill.category,
                    "taxonomy_validated": True,
                    "ancestors": hierarchy["ancestors"],
                    "descendants": hierarchy["descendants"],
                    "related_skills": related,
                    "aliases": taxonomy_skill.aliases
                })
                
                # Update confidence if from taxonomy
                if skill.source != "taxonomy":
                    skill.confidence = max(skill.confidence, 0.8)
                
                # Only process the first domain match
                break
    
    def _update_matcher(self) -> None:
        """Update the phrase matcher with skills from taxonomies."""
        if not self.nlp or not self.matcher:
            return
        
        # Clear existing patterns
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        
        # Add patterns from taxonomies
        for domain in self.domains:
            # Get flat taxonomy
            flat_taxonomy = self.taxonomy_manager.export_flat_taxonomy(domain)
            
            # Add each skill and its aliases as patterns
            for skill_name, skill_data in flat_taxonomy.items():
                # Create pattern for the skill name
                skill_pattern = self.nlp(skill_name)
                self.matcher.add(f"{domain}:{skill_name}", [skill_pattern])
                
                # Add alias patterns
                for alias in skill_data.get("aliases", []):
                    alias_pattern = self.nlp(alias)
                    self.matcher.add(f"{domain}:{skill_name}", [alias_pattern])
    
    def classify_skill(self, skill_name: str) -> Dict[str, Any]:
        """
        Classify a skill based on taxonomy.
        
        Args:
            skill_name: Name of the skill to classify
            
        Returns:
            Dictionary with classification information
        """
        for domain in self.domains:
            taxonomy_skill = self.taxonomy_manager.find_skill(domain, skill_name)
            
            if taxonomy_skill:
                hierarchy = self.taxonomy_manager.get_skill_hierarchy(domain, skill_name)
                related = self.taxonomy_manager.get_related_skills(domain, skill_name)
                
                return {
                    "name": taxonomy_skill.name,
                    "domain": domain,
                    "category": taxonomy_skill.category,
                    "ancestors": hierarchy["ancestors"],
                    "descendants": hierarchy["descendants"],
                    "related_skills": related,
                    "aliases": taxonomy_skill.aliases,
                    "metadata": taxonomy_skill.metadata
                }
        
        # Not found in taxonomy
        return {
            "name": skill_name,
            "domain": "unknown",
            "category": "unknown",
            "ancestors": [],
            "descendants": [],
            "related_skills": [],
            "aliases": [],
            "metadata": {}
        }
    
    def get_skill_suggestions(self, partial_text: str, max_suggestions: int = 10) -> List[Dict[str, Any]]:
        """
        Get skill suggestions based on partial text.
        
        Args:
            partial_text: Partial skill name
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of skill suggestions
        """
        suggestions = []
        
        for domain in self.domains:
            # Get flat taxonomy for this domain
            flat_taxonomy = self.taxonomy_manager.export_flat_taxonomy(domain)
            
            # Find matching skills
            partial_lower = partial_text.lower()
            
            for skill_name, skill_data in flat_taxonomy.items():
                # Check if skill matches
                if partial_lower in skill_name.lower():
                    suggestions.append({
                        "name": skill_name,
                        "domain": domain,
                        "category": skill_data.get("category", "unknown"),
                        "path": skill_data.get("path", []),
                        "aliases": skill_data.get("aliases", [])
                    })
                
                # Check aliases
                for alias in skill_data.get("aliases", []):
                    if partial_lower in alias.lower():
                        suggestions.append({
                            "name": skill_name,
                            "domain": domain,
                            "category": skill_data.get("category", "unknown"),
                            "path": skill_data.get("path", []),
                            "aliases": skill_data.get("aliases", []),
                            "matched_alias": alias
                        })
                        break
        
        # Sort by relevance and limit
        suggestions.sort(key=lambda x: len(x["name"]))
        return suggestions[:max_suggestions]
