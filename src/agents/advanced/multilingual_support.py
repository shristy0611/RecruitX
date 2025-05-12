"""
Multilingual Support for RecruitPro AI.

This module provides comprehensive multilingual capabilities for the recruitment system,
enabling processing of resumes and interactions in multiple languages.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union

from src.llm.gemma_service import GemmaService
from src.llm.gemini_service import GeminiService

# Configure logging
logger = logging.getLogger(__name__)


class MultilingualProcessor:
    """
    Multilingual processing capabilities for the RecruitPro AI system.
    
    This component enables:
    1. Language detection for input text
    2. Translation between languages
    3. Multilingual content analysis
    4. Language-specific processing adapters
    """
    
    def __init__(self):
        """Initialize the MultilingualProcessor with necessary services."""
        # Initialize Gemma service for translation and multilingual processing
        try:
            self.gemma_service = GemmaService()
            logger.info("Initialized Gemma service for multilingual processing")
            self.primary_service = "gemma"
        except Exception as e:
            logger.warning(f"Failed to initialize Gemma service: {e}")
            self.gemma_service = None
            
        # Initialize Gemini as fallback or for complex multilingual tasks
        try:
            self.gemini_service = GeminiService()
            logger.info("Initialized Gemini service for multilingual processing")
            if not self.gemma_service:
                self.primary_service = "gemini"
            else:
                self.primary_service = "gemma"  # Prefer Gemma for efficiency
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini service: {e}")
            self.gemini_service = None
            
        if not self.gemma_service and not self.gemini_service:
            logger.error("No language model services available for multilingual processing")
            self.primary_service = None
            
        # Initialize supported languages map with ISO codes
        self.supported_languages = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic",
            "hi": "Hindi"
        }
        
        # Special handling configurations for languages with unique requirements
        self.language_configs = {
            "zh": {"segmentation": "character", "direction": "ltr"},
            "ja": {"segmentation": "character", "direction": "ltr"},
            "ko": {"segmentation": "syllable", "direction": "ltr"},
            "ar": {"segmentation": "word", "direction": "rtl"},
            "hi": {"segmentation": "word", "direction": "ltr"}
        }
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the language of the provided text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with detected language code, name, and confidence
        """
        # First try to detect with Gemma if available (more efficient)
        if self.gemma_service:
            try:
                prompt = f"""
                Detect the language of the following text. Respond with just the ISO 639-1 
                language code (e.g., 'en' for English, 'es' for Spanish, etc.) and confidence 
                score (0-1).
                
                Text: {text[:500]}  # Use first 500 chars for efficiency
                
                Format: {{
                    "language_code": "XX",
                    "confidence": 0.XX
                }}
                """
                
                response = self.gemma_service.generate_content(prompt)
                
                # Parse JSON response
                try:
                    result = json.loads(response)
                    language_code = result.get("language_code", "en")
                    confidence = result.get("confidence", 0)
                    
                    return {
                        "language_code": language_code,
                        "language_name": self.supported_languages.get(language_code, "Unknown"),
                        "confidence": confidence,
                        "method": "gemma"
                    }
                except (json.JSONDecodeError, KeyError):
                    logger.warning("Failed to parse Gemma language detection response")
            except Exception as e:
                logger.error(f"Gemma language detection failed: {e}")
        
        # Try with Gemini if available
        if self.gemini_service:
            try:
                prompt = f"""
                Detect the language of the following text. Respond with just the ISO 639-1 
                language code (e.g., 'en' for English, 'es' for Spanish, etc.) and confidence 
                score (0-1).
                
                Text: {text[:500]}  # Use first 500 chars for efficiency
                
                Format: {{
                    "language_code": "XX",
                    "confidence": 0.XX
                }}
                """
                
                response = self.gemini_service.generate_content(prompt)
                
                # Parse JSON response
                try:
                    result = json.loads(response)
                    language_code = result.get("language_code", "en")
                    confidence = result.get("confidence", 0)
                    
                    return {
                        "language_code": language_code,
                        "language_name": self.supported_languages.get(language_code, "Unknown"),
                        "confidence": confidence,
                        "method": "gemini"
                    }
                except (json.JSONDecodeError, KeyError):
                    logger.warning("Failed to parse Gemini language detection response")
            except Exception as e:
                logger.error(f"Gemini language detection failed: {e}")
        
        # Fallback to simple heuristic language detection
        try:
            import langdetect
            language_code = langdetect.detect(text)
            
            return {
                "language_code": language_code,
                "language_name": self.supported_languages.get(language_code, "Unknown"),
                "confidence": 0.7,  # Approximate confidence for langdetect
                "method": "langdetect"
            }
        except Exception as e:
            logger.error(f"Fallback language detection failed: {e}")
            
            # Ultimate fallback - assume English
            return {
                "language_code": "en",
                "language_name": "English",
                "confidence": 0.5,
                "method": "fallback"
            }
    
    def translate_text(
        self,
        text: str,
        source_language: Optional[str] = None,
        target_language: str = "en"
    ) -> str:
        """
        Translate text from source language to target language.
        
        Args:
            text: Text to translate
            source_language: Source language code (auto-detect if None)
            target_language: Target language code
            
        Returns:
            Translated text
        """
        # Auto-detect source language if not provided
        if not source_language:
            detection = self.detect_language(text)
            source_language = detection["language_code"]
            
        # Skip translation if source and target are the same
        if source_language == target_language:
            return text
            
        # Use Gemma for translation if available
        if self.gemma_service:
            try:
                prompt = f"""
                Translate the following text from {self.supported_languages.get(source_language, source_language)} 
                to {self.supported_languages.get(target_language, target_language)}.
                
                Text: {text}
                
                Provide only the translated text without any explanations or comments.
                """
                
                translation = self.gemma_service.generate_content(prompt)
                
                # Clean up translation (remove quotes if present)
                translation = translation.strip()
                if translation.startswith('"') and translation.endswith('"'):
                    translation = translation[1:-1]
                    
                return translation
                
            except Exception as e:
                logger.error(f"Gemma translation failed: {e}")
                
        # Try Gemini as fallback
        if self.gemini_service:
            try:
                prompt = f"""
                Translate the following text from {self.supported_languages.get(source_language, source_language)} 
                to {self.supported_languages.get(target_language, target_language)}.
                
                Text: {text}
                
                Provide only the translated text without any explanations or comments.
                """
                
                translation = self.gemini_service.generate_content(prompt)
                
                # Clean up translation (remove quotes if present)
                translation = translation.strip()
                if translation.startswith('"') and translation.endswith('"'):
                    translation = translation[1:-1]
                    
                return translation
                
            except Exception as e:
                logger.error(f"Gemini translation failed: {e}")
        
        # External translation API fallback
        try:
            import translators as ts
            translation = ts.google(text, from_language=source_language, to_language=target_language)
            return translation
        except Exception as e:
            logger.error(f"External translation API failed: {e}")
            
            # If all translation methods fail, return original text with note
            if source_language != "en" and target_language == "en":
                return f"[UNTRANSLATED {source_language} TEXT]: {text}"
            else:
                return text
    
    def analyze_multilingual_text(
        self,
        text: str,
        language: Optional[str] = None,
        analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Perform language-aware analysis on text.
        
        Args:
            text: Text to analyze
            language: Language code (auto-detect if None)
            analysis_type: Type of analysis to perform ("general", "skills", "sentiment", etc.)
            
        Returns:
            Analysis results
        """
        # Auto-detect language if not provided
        if not language:
            detection = self.detect_language(text)
            language = detection["language_code"]
        
        # Apply language-specific preprocessing if needed
        processed_text = self._preprocess_for_language(text, language)
        
        # Translate to English for analysis if not English and translation is available
        analysis_text = processed_text
        was_translated = False
        if language != "en" and (self.gemma_service or self.gemini_service):
            try:
                analysis_text = self.translate_text(processed_text, language, "en")
                was_translated = True
            except Exception as e:
                logger.error(f"Failed to translate for analysis: {e}")
                # Continue with original text if translation fails
        
        # Perform requested analysis
        analysis_results = {}
        
        if analysis_type == "general":
            analysis_results = self._perform_general_analysis(analysis_text)
        elif analysis_type == "skills":
            analysis_results = self._extract_skills(analysis_text)
        elif analysis_type == "sentiment":
            analysis_results = self._analyze_sentiment(analysis_text)
        else:
            analysis_results = {"error": f"Unknown analysis type: {analysis_type}"}
        
        # Add metadata about the analysis
        analysis_results["language"] = {
            "code": language,
            "name": self.supported_languages.get(language, "Unknown"),
            "was_translated": was_translated
        }
        
        return analysis_results
    
    def _preprocess_for_language(self, text: str, language: str) -> str:
        """
        Apply language-specific preprocessing.
        
        Args:
            text: Input text
            language: Language code
            
        Returns:
            Preprocessed text
        """
        # Get language configuration if available
        config = self.language_configs.get(language, {"segmentation": "word", "direction": "ltr"})
        
        # Apply language-specific preprocessing
        if language in ["zh", "ja"]:
            # For Chinese and Japanese, ensure proper spacing for tokenization
            processed_text = " ".join(text)
            return processed_text
        
        # For now, return original text for other languages
        return text
    
    def _perform_general_analysis(self, text: str) -> Dict[str, Any]:
        """
        Perform general text analysis.
        
        Args:
            text: Text to analyze
            
        Returns:
            Analysis results
        """
        # Use primary service for analysis
        if self.primary_service == "gemma" and self.gemma_service:
            try:
                prompt = f"""
                Analyze the following text and provide:
                1. A summary (max 100 words)
                2. Main topics or themes (up to 5)
                3. Key entities mentioned
                
                Text: {text[:1000]}  # Limit to first 1000 chars for efficiency
                
                Format your response as JSON:
                {{
                    "summary": "...",
                    "topics": ["topic1", "topic2", ...],
                    "entities": ["entity1", "entity2", ...]
                }}
                """
                
                response = self.gemma_service.generate_content(prompt)
                
                # Parse JSON response
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Gemma analysis response as JSON")
                    # Extract JSON from text response
                    import re
                    json_pattern = r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}'
                    matches = re.search(json_pattern, response)
                    if matches:
                        try:
                            json_str = matches.group(1) or matches.group(0)
                            return json.loads(json_str)
                        except (json.JSONDecodeError, IndexError):
                            pass
            except Exception as e:
                logger.error(f"Gemma general analysis failed: {e}")
        
        # Try Gemini as alternative
        if self.gemini_service:
            try:
                prompt = f"""
                Analyze the following text and provide:
                1. A summary (max 100 words)
                2. Main topics or themes (up to 5)
                3. Key entities mentioned
                
                Text: {text[:1000]}  # Limit to first 1000 chars for efficiency
                
                Format your response as JSON:
                {{
                    "summary": "...",
                    "topics": ["topic1", "topic2", ...],
                    "entities": ["entity1", "entity2", ...]
                }}
                """
                
                response = self.gemini_service.generate_content(prompt)
                
                # Parse JSON response
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Gemini analysis response as JSON")
                    # Extract JSON from text response
                    import re
                    json_pattern = r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}'
                    matches = re.search(json_pattern, response)
                    if matches:
                        try:
                            json_str = matches.group(1) or matches.group(0)
                            return json.loads(json_str)
                        except (json.JSONDecodeError, IndexError):
                            pass
            except Exception as e:
                logger.error(f"Gemini general analysis failed: {e}")
        
        # Basic fallback analysis
        words = text.split()
        sentences = text.split('.')
        
        return {
            "summary": text[:200] + "..." if len(text) > 200 else text,
            "topics": ["Unable to extract topics without LLM"],
            "entities": ["Unable to extract entities without LLM"],
            "metrics": {
                "word_count": len(words),
                "sentence_count": len(sentences),
                "average_word_length": sum(len(w) for w in words) / max(1, len(words))
            }
        }
    
    def _extract_skills(self, text: str) -> Dict[str, Any]:
        """
        Extract skills from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Extracted skills information
        """
        # Use primary service for skill extraction
        if self.primary_service == "gemma" and self.gemma_service:
            try:
                prompt = f"""
                Extract professional skills from the following text. Include both technical skills and soft skills.
                
                Text: {text[:1500]}  # Limit to first 1500 chars for efficiency
                
                Format your response as JSON:
                {{
                    "technical_skills": ["skill1", "skill2", ...],
                    "soft_skills": ["skill1", "skill2", ...],
                    "skill_levels": [
                        {{"skill": "skill1", "level": "beginner|intermediate|expert", "evidence": "text evidence"}}
                    ]
                }}
                """
                
                response = self.gemma_service.generate_content(prompt)
                
                # Parse JSON response
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Gemma skill extraction response as JSON")
                    # Extract JSON from text response
                    import re
                    json_pattern = r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}'
                    matches = re.search(json_pattern, response)
                    if matches:
                        try:
                            json_str = matches.group(1) or matches.group(0)
                            return json.loads(json_str)
                        except (json.JSONDecodeError, IndexError):
                            pass
            except Exception as e:
                logger.error(f"Gemma skill extraction failed: {e}")
        
        # Try Gemini as alternative
        if self.gemini_service:
            try:
                prompt = f"""
                Extract professional skills from the following text. Include both technical skills and soft skills.
                
                Text: {text[:1500]}  # Limit to first 1500 chars for efficiency
                
                Format your response as JSON:
                {{
                    "technical_skills": ["skill1", "skill2", ...],
                    "soft_skills": ["skill1", "skill2", ...],
                    "skill_levels": [
                        {{"skill": "skill1", "level": "beginner|intermediate|expert", "evidence": "text evidence"}}
                    ]
                }}
                """
                
                response = self.gemini_service.generate_content(prompt)
                
                # Parse JSON response
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Gemini skill extraction response as JSON")
                    # Extract JSON from text response
                    import re
                    json_pattern = r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}'
                    matches = re.search(json_pattern, response)
                    if matches:
                        try:
                            json_str = matches.group(1) or matches.group(0)
                            return json.loads(json_str)
                        except (json.JSONDecodeError, IndexError):
                            pass
            except Exception as e:
                logger.error(f"Gemini skill extraction failed: {e}")
        
        # Basic fallback skill extraction using regex patterns
        import re
        
        # Define basic skill patterns
        tech_skill_pattern = r"\b(?:Python|Java|JavaScript|C\+\+|SQL|AWS|Azure|Docker|React|Angular|Node\.js|Machine Learning|AI|Data Science)\b"
        soft_skill_pattern = r"\b(?:Communication|Leadership|Team\s*work|Problem[\s-]*solving|Critical\s*thinking|Adaptability|Time\s*management)\b"
        
        # Find matches
        tech_skills = list(set(re.findall(tech_skill_pattern, text, re.IGNORECASE)))
        soft_skills = list(set(re.findall(soft_skill_pattern, text, re.IGNORECASE)))
        
        return {
            "technical_skills": tech_skills,
            "soft_skills": soft_skills,
            "skill_levels": [],  # Cannot determine levels with regex alone
            "note": "Basic fallback extraction used - limited accuracy"
        }
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment analysis results
        """
        # Use primary service for sentiment analysis
        if self.primary_service == "gemma" and self.gemma_service:
            try:
                prompt = f"""
                Analyze the sentiment of the following text. Consider factors like emotion, 
                tone, attitude, and confidence displayed.
                
                Text: {text[:1000]}  # Limit to first 1000 chars for efficiency
                
                Format your response as JSON:
                {{
                    "overall_sentiment": "positive|neutral|negative", 
                    "sentiment_score": 0.0 to 1.0,  # 0 = very negative, 0.5 = neutral, 1.0 = very positive
                    "emotions_detected": ["emotion1", "emotion2", ...],
                    "tone": "formal|informal|technical|casual|etc.",
                    "confidence_level": "high|medium|low"  # confidence in the sentiment analysis
                }}
                """
                
                response = self.gemma_service.generate_content(prompt)
                
                # Parse JSON response
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Gemma sentiment analysis response as JSON")
                    # Extract JSON from text response
                    import re
                    json_pattern = r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}'
                    matches = re.search(json_pattern, response)
                    if matches:
                        try:
                            json_str = matches.group(1) or matches.group(0)
                            return json.loads(json_str)
                        except (json.JSONDecodeError, IndexError):
                            pass
            except Exception as e:
                logger.error(f"Gemma sentiment analysis failed: {e}")
        
        # Try Gemini as alternative
        if self.gemini_service:
            try:
                prompt = f"""
                Analyze the sentiment of the following text. Consider factors like emotion, 
                tone, attitude, and confidence displayed.
                
                Text: {text[:1000]}  # Limit to first 1000 chars for efficiency
                
                Format your response as JSON:
                {{
                    "overall_sentiment": "positive|neutral|negative", 
                    "sentiment_score": 0.0 to 1.0,  # 0 = very negative, 0.5 = neutral, 1.0 = very positive
                    "emotions_detected": ["emotion1", "emotion2", ...],
                    "tone": "formal|informal|technical|casual|etc.",
                    "confidence_level": "high|medium|low"  # confidence in the sentiment analysis
                }}
                """
                
                response = self.gemini_service.generate_content(prompt)
                
                # Parse JSON response
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Gemini sentiment analysis response as JSON")
                    # Extract JSON from text response
                    import re
                    json_pattern = r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}'
                    matches = re.search(json_pattern, response)
                    if matches:
                        try:
                            json_str = matches.group(1) or matches.group(0)
                            return json.loads(json_str)
                        except (json.JSONDecodeError, IndexError):
                            pass
            except Exception as e:
                logger.error(f"Gemini sentiment analysis failed: {e}")
        
        # Very basic fallback sentiment analysis
        positive_words = ["good", "great", "excellent", "outstanding", "positive", "impressive", 
                         "skilled", "experienced", "qualified", "strong", "successful"]
        negative_words = ["bad", "poor", "inadequate", "limited", "lack", "insufficient", 
                         "weak", "problem", "issue", "concern", "negative"]
        
        text_lower = text.lower()
        
        positive_count = sum(text_lower.count(word) for word in positive_words)
        negative_count = sum(text_lower.count(word) for word in negative_words)
        total_count = positive_count + negative_count
        
        if total_count == 0:
            sentiment_score = 0.5  # Neutral if no sentiment words found
        else:
            sentiment_score = positive_count / total_count
            
        # Determine overall sentiment
        if sentiment_score > 0.6:
            overall_sentiment = "positive"
        elif sentiment_score < 0.4:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"
            
        return {
            "overall_sentiment": overall_sentiment,
            "sentiment_score": sentiment_score,
            "emotions_detected": [],  # Cannot detect emotions with this simple method
            "tone": "unknown",  # Cannot detect tone with this simple method
            "confidence_level": "low",
            "note": "Basic fallback sentiment analysis used - limited accuracy"
        }
        

# Factory function to get multilingual processor
def get_multilingual_processor() -> MultilingualProcessor:
    """
    Get an instance of the MultilingualProcessor.
    
    Returns:
        MultilingualProcessor instance
    """
    return MultilingualProcessor()
