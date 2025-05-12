"""
Enhanced skill extractor for RecruitPro AI.

This module provides enhanced skill extraction using domain-specific NER
with Gemini API-powered analysis.
"""

import logging
import json
import re
from typing import Dict, List, Set, Optional, Any, Union
import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span

from src.skills.extractors.base_extractor import SkillExtractor, Skill
from src.llm.gemini_service import GeminiService

# Configure logging
logger = logging.getLogger(__name__)


class EnhancedSkillExtractor(SkillExtractor):
    """
    Enhanced skill extractor using hybrid approach with SpaCy NER and Gemini API.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        spacy_model: str = "en_core_web_sm",
        taxonomy_path: Optional[str] = None
    ):
        """
        Initialize the enhanced skill extractor.
        
        Args:
            config: Optional configuration dictionary
            spacy_model: SpaCy model to use for base NER
            taxonomy_path: Optional path to skills taxonomy JSON
        """
        super().__init__(config)
        
        # Get configuration values
        if config:
            spacy_model = config.get("spacy_model", spacy_model)
            taxonomy_path = config.get("taxonomy_path", taxonomy_path)
        
        self.gemini_service = None
        try:
            self.gemini_service = GeminiService()
        except Exception as e:
            logger.warning(f"Failed to initialize GeminiService: {e}")
        
        # Load SpaCy model
        try:
            self.nlp = spacy.load(spacy_model)
            logger.info(f"Loaded SpaCy model: {spacy_model}")
        except OSError:
            logger.warning(f"SpaCy model '{spacy_model}' not found. Downloading...")
            try:
                spacy.cli.download(spacy_model)
                self.nlp = spacy.load(spacy_model)
            except Exception as e:
                logger.error(f"Failed to download SpaCy model: {e}")
                self.nlp = None
        
        # Add custom skill entity type if SpaCy is loaded
        if self.nlp:
            self._add_skill_entity_type()
        
        # Load domain taxonomy if provided
        self.taxonomy = {}
        if taxonomy_path:
            self._load_taxonomy(taxonomy_path)
    
    def extract_skills(
        self, 
        text: str, 
        language: str = "en"
    ) -> List[Skill]:
        """
        Extract skills from text using a hybrid approach.
        
        Args:
            text: Text to extract skills from
            language: Language code (ISO 639-1)
            
        Returns:
            List of extracted Skill objects
        """
        if language != "en":
            logger.warning(f"Language '{language}' not supported by enhanced extractor. "
                          f"Use MultilingualSkillExtractor for non-English text.")
        
        # Preprocess text
        processed_text = self.preprocess_text(text)
        
        # If NLP isn't loaded, use a simple fallback approach
        if not self.nlp:
            logger.warning("SpaCy model not loaded, using simple keyword extraction")
            return self._extract_skills_simple(processed_text)
        
        # Extract skills using different methods
        spacy_skills = self._extract_skills_spacy(processed_text)
        keyword_skills = self._extract_skills_keywords(processed_text)
        llm_skills = self._extract_skills_llm(processed_text)
        
        # Combine all skills
        all_skills = spacy_skills + keyword_skills + llm_skills
        
        # Merge and categorize skills
        merged_skills = self.merge_skills(all_skills)
        categorized_skills = self._categorize_skills(merged_skills)
        
        return categorized_skills
    
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
    
    def _extract_skills_spacy(self, text: str) -> List[Skill]:
        """
        Extract skills using SpaCy NER.
        
        Args:
            text: Preprocessed text
            
        Returns:
            List of skills extracted by SpaCy
        """
        if not self.nlp:
            return []
            
        skills = []
        doc = self.nlp(text)
        
        # Extract entities recognized as skills
        for ent in doc.ents:
            if ent.label_ in ["SKILL", "PRODUCT", "ORG", "GPE"]:
                confidence = 0.7  # Base confidence for SpaCy entities
                
                # Adjust confidence based on entity type
                if ent.label_ == "SKILL":
                    confidence = 0.9
                elif ent.label_ == "PRODUCT":
                    confidence = 0.7
                elif ent.label_ == "ORG" or ent.label_ == "GPE":
                    confidence = 0.6
                
                # Create skill with context
                context_start = max(0, ent.start_char - 40)
                context_end = min(len(text), ent.end_char + 40)
                context = text[context_start:context_end]
                
                skill = Skill(
                    name=ent.text,
                    confidence=confidence,
                    category=self._guess_skill_category(ent.text),
                    source="spacy",
                    context=context
                )
                skills.append(skill)
        
        # Also extract noun chunks that might be skills
        for chunk in doc.noun_chunks:
            # Skip if too long (likely not a skill)
            if len(chunk.text.split()) > 4:
                continue
                
            # Skip if the chunk is a pronoun or determiner
            if chunk.root.pos_ in ["PRON", "DET"]:
                continue
                
            # Check if the chunk is likely a skill
            if self._is_likely_skill(chunk.text):
                confidence = 0.6  # Lower confidence for noun chunks
                
                # Create skill with context
                context_start = max(0, chunk.start_char - 30)
                context_end = min(len(text), chunk.end_char + 30)
                context = text[context_start:context_end]
                
                skill = Skill(
                    name=chunk.text,
                    confidence=confidence,
                    category=self._guess_skill_category(chunk.text),
                    source="spacy_noun_chunk",
                    context=context
                )
                skills.append(skill)
        
        return skills
    
    def _extract_skills_keywords(self, text: str) -> List[Skill]:
        """
        Extract skills using keyword matching with taxonomy.
        
        Args:
            text: Preprocessed text
            
        Returns:
            List of skills extracted by keyword matching
        """
        if not self.taxonomy:
            return []
            
        skills = []
        text_lower = text.lower()
        
        # For each skill in taxonomy, check if it exists in text
        for skill_name, skill_data in self.taxonomy.items():
            skill_lower = skill_name.lower()
            
            # Check for exact match with word boundaries
            pattern = r'\b' + re.escape(skill_lower) + r'\b'
            if re.search(pattern, text_lower):
                confidence = 0.85  # High confidence for exact matches
                
                # Find context
                match = re.search(pattern, text_lower)
                if match:
                    context_start = max(0, match.start() - 40)
                    context_end = min(len(text_lower), match.end() + 40)
                    context = text[context_start:context_end]
                else:
                    context = None
                
                # Create skill object
                skill = Skill(
                    name=skill_name,
                    confidence=confidence,
                    category=skill_data.get("category", self._guess_skill_category(skill_name)),
                    source="taxonomy",
                    context=context,
                    aliases=skill_data.get("aliases", [])
                )
                skills.append(skill)
                
            # Check for aliases
            if "aliases" in skill_data:
                for alias in skill_data["aliases"]:
                    alias_lower = alias.lower()
                    pattern = r'\b' + re.escape(alias_lower) + r'\b'
                    
                    if re.search(pattern, text_lower):
                        # Only add if the main skill name wasn't already added
                        if not any(s.name == skill_name for s in skills):
                            confidence = 0.8  # Slightly lower confidence for aliases
                            
                            # Find context
                            match = re.search(pattern, text_lower)
                            if match:
                                context_start = max(0, match.start() - 40)
                                context_end = min(len(text_lower), match.end() + 40)
                                context = text[context_start:context_end]
                            else:
                                context = None
                            
                            # Create skill object
                            skill = Skill(
                                name=skill_name,
                                confidence=confidence,
                                category=skill_data.get("category", self._guess_skill_category(skill_name)),
                                source="taxonomy_alias",
                                context=context,
                                aliases=skill_data.get("aliases", []),
                                metadata={"matched_alias": alias}
                            )
                            skills.append(skill)
                            break  # Only add once, even if multiple aliases match
        
        return skills
    
    def _extract_skills_llm(self, text: str) -> List[Skill]:
        """
        Extract skills using Gemini API.
        
        Args:
            text: Preprocessed text
            
        Returns:
            List of skills extracted by Gemini
        """
        if not self.gemini_service:
            logger.warning("Gemini service not initialized, skipping LLM extraction")
            return []
        
        try:
            # Truncate text if too long
            max_chars = 5000
            if len(text) > max_chars:
                truncated_text = text[:max_chars] + "..."
                logger.info(f"Truncated text from {len(text)} to {max_chars} characters for LLM extraction")
            else:
                truncated_text = text
            
            # Create the prompt
            prompt = f"""
            Extract all professional skills from the following text. 
            Focus on technical skills, soft skills, and domain expertise.
            
            For each skill, provide:
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
            {truncated_text}
            """
            
            # Call Gemini API
            response = self.gemini_service.generate_content(prompt)
            skills_data = self._extract_json_from_response(response)
            
            # Convert to skill objects
            skills = []
            for skill_info in skills_data.get("skills", []):
                skill = Skill(
                    name=skill_info.get("name", ""),
                    confidence=float(skill_info.get("confidence", 0.5)),
                    category=skill_info.get("category"),
                    source="gemini",
                    metadata={"llm_extracted": True}
                )
                skills.append(skill)
            
            return skills
            
        except Exception as e:
            logger.error(f"Error extracting skills with Gemini API: {e}")
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
    
    def _categorize_skills(self, skills: List[Skill]) -> List[Skill]:
        """
        Categorize skills that don't have a category yet.
        
        Args:
            skills: List of skills to categorize
            
        Returns:
            List of skills with categories
        """
        for skill in skills:
            if not skill.category:
                skill.category = self._guess_skill_category(skill.name)
        
        return skills
    
    def _guess_skill_category(self, skill_name: str) -> str:
        """
        Guess the category of a skill based on heuristics.
        
        Args:
            skill_name: Name of the skill to categorize
            
        Returns:
            Category string: "technical", "domain", or "soft"
        """
        skill_lower = skill_name.lower()
        
        # Check in taxonomy first if available
        if skill_name in self.taxonomy:
            return self.taxonomy[skill_name].get("category", "unknown")
        
        # Technical skills indicators
        technical_indicators = [
            "python", "java", "javascript", "c++", "c#", "ruby", "php", "go", "scala",
            "react", "angular", "vue", "node", "django", "flask", "spring", "laravel",
            "aws", "azure", "docker", "kubernetes", "sql", "database", "git", "api",
            "tensorflow", "pytorch", "ml", "ai", "cloud", "devops", "frontend", "backend"
        ]
        
        # Soft skills indicators
        soft_indicators = [
            "communication", "leadership", "teamwork", "management", "negotiation",
            "problem solving", "critical thinking", "creativity", "adaptability",
            "time management", "conflict resolution", "emotional intelligence"
        ]
        
        # Domain skills indicators
        domain_indicators = [
            "marketing", "finance", "accounting", "sales", "hr", "healthcare", 
            "legal", "consulting", "analysis", "research", "design", "planning"
        ]
        
        # Check for matches
        for indicator in technical_indicators:
            if indicator in skill_lower:
                return "technical"
                
        for indicator in soft_indicators:
            if indicator in skill_lower:
                return "soft"
                
        for indicator in domain_indicators:
            if indicator in skill_lower:
                return "domain"
        
        # Default to technical if unsure
        return "technical"
    
    def _is_likely_skill(self, text: str) -> bool:
        """
        Check if text is likely to be a skill.
        
        Args:
            text: Text to check
            
        Returns:
            True if likely a skill, False otherwise
        """
        text_lower = text.lower()
        
        # Check if it's in our taxonomy
        if text in self.taxonomy:
            return True
            
        # Check aliases in taxonomy
        for skill_name, skill_data in self.taxonomy.items():
            aliases = skill_data.get("aliases", [])
            if text_lower in [alias.lower() for alias in aliases]:
                return True
        
        # Check for indicators of skills
        skill_indicators = [
            "experience", "proficient", "knowledge", "skill", "expertise", "familiar", 
            "certified", "developer", "engineer", "specialist", "manager", "designer", 
            "analyst", "architect", "programming", "language", "framework", "platform", 
            "technology", "tool", "software"
        ]
        
        # If we have NLP loaded, use it for more sophisticated analysis
        if self.nlp:
            doc = self.nlp(text_lower)
            
            # Check if there's a clear NOUN phrase
            if any(token.pos_ == "NOUN" for token in doc):
                return True
                
        return False
    
    def _add_skill_entity_type(self):
        """Add custom skill entity type to the SpaCy pipeline."""
        # Define a simple skill entity recognizer that does nothing
        # This is just a placeholder to avoid errors when we don't have a proper skill recognizer
        @Language.component("skill_ner")
        def skill_ner(doc):
            """Placeholder skill NER component."""
            return doc
        
        # Add the component to the pipeline if not already present
        if "skill_ner" not in self.nlp.pipe_names:
            self.nlp.add_pipe("skill_ner", last=True)
    
    def _load_taxonomy(self, taxonomy_path: str):
        """
        Load skills taxonomy from JSON file.
        
        Args:
            taxonomy_path: Path to taxonomy JSON file
        """
        try:
            with open(taxonomy_path, 'r') as f:
                self.taxonomy = json.load(f)
            logger.info(f"Loaded skills taxonomy with {len(self.taxonomy)} entries")
        except Exception as e:
            logger.error(f"Failed to load skills taxonomy: {e}")
            self.taxonomy = {}
