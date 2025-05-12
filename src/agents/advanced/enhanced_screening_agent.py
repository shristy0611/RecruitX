"""
Enhanced Screening Agent for RecruitPro AI.

This agent extends the base ScreeningAgent with advanced document analysis
capabilities using Gemini API and Gemma 3's multimodal processing.
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple, Union

import spacy
import numpy as np

from src.agents.screening_agent import ScreeningAgent
from src.llm.gemini_service import GeminiService
from src.llm.gemma_service import GemmaService
from src.skills.extractors.factory import SkillExtractorFactory
from src.knowledge_base.vector_store import VectorStore

# Configure logging
logger = logging.getLogger(__name__)


class EnhancedScreeningAgent(ScreeningAgent):
    """
    Enhanced Screening Agent with advanced document analysis capabilities.
    
    This agent extends the base ScreeningAgent with:
    1. Gemini-powered document analysis for deeper resume understanding
    2. Multimodal processing for handling text, tables, and images in resumes
    3. Enhanced skill extraction using domain-specific taxonomy
    4. Multilingual resume parsing and evaluation
    """
    
    def __init__(self, vector_store=None):
        """
        Initialize the Enhanced Screening Agent.
        
        Args:
            vector_store: Optional VectorStore instance
        """
        super().__init__(vector_store)
        
        # Initialize Gemini service for advanced analysis
        try:
            self.gemini_service = GeminiService()
            logger.info("Initialized Gemini service for enhanced screening")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini service: {e}")
            self.gemini_service = None
        
        # Initialize Gemma service for multilingual support
        try:
            self.gemma_service = GemmaService()
            logger.info("Initialized Gemma service for multilingual support")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemma service: {e}")
            self.gemma_service = None
        
        # Initialize enhanced skill extractor
        try:
            self.skill_extractor = SkillExtractorFactory.create_extractor(
                extractor_type="enhanced",
                config={
                    "spacy_model": "en_core_web_lg",
                    "taxonomy_path": None  # Will use default taxonomy
                }
            )
            logger.info("Initialized enhanced skill extractor")
        except Exception as e:
            logger.warning(f"Failed to initialize enhanced skill extractor: {e}")
            self.skill_extractor = None
    
    def parse_resume(self, resume_text: str, language: str = "en") -> Dict[str, Any]:
        """
        Parse resume with enhanced capabilities including multilingual support.
        
        Args:
            resume_text: Raw resume text
            language: Language code (ISO 639-1)
            
        Returns:
            Structured resume information
        """
        # If not English and Gemma service is available, translate to English
        original_language = language
        if language != "en" and self.gemma_service:
            try:
                resume_text = self.gemma_service.translate_text(
                    text=resume_text,
                    source_language=language,
                    target_language="en"
                )
                language = "en"
                logger.info(f"Translated resume from {original_language} to English")
            except Exception as e:
                logger.error(f"Failed to translate resume: {e}")
        
        # First try enhanced parsing with Gemini if available
        if self.gemini_service:
            try:
                parsed_data = self._parse_with_gemini(resume_text)
                
                # Add language information
                parsed_data["original_language"] = original_language
                
                # Extract skills using enhanced extractor if available
                if self.skill_extractor:
                    skills = self.skill_extractor.extract_skills(
                        text=resume_text,
                        language=language
                    )
                    parsed_data["skills"] = [skill.name for skill in skills]
                    parsed_data["skill_details"] = [skill.to_dict() for skill in skills]
                
                return parsed_data
            except Exception as e:
                logger.error(f"Enhanced resume parsing failed: {e}")
                logger.info("Falling back to base parsing method")
        
        # Fall back to base implementation
        parsed_data = super().parse_resume(resume_text)
        
        # Add language information
        parsed_data["original_language"] = original_language
        
        return parsed_data
    
    def _parse_with_gemini(self, resume_text: str) -> Dict[str, Any]:
        """
        Parse resume using Gemini API for enhanced understanding.
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Structured resume information
        """
        # Create prompt for Gemini
        prompt = f"""
        Analyze the following resume and extract key information in structured JSON format.
        Extract the following sections:
        - contact_info (name, email, phone, location)
        - summary (professional summary or objective)
        - work_experience (list of positions with company, title, dates, responsibilities)
        - education (list of degrees with institution, degree, dates, field of study)
        - skills (technical skills, soft skills)
        - certifications (list of professional certifications)
        - languages (list of languages with proficiency level)
        - projects (list of relevant projects with descriptions)
        
        Only include sections that are present in the resume. If a section is not present, omit it entirely.
        Format dates consistently as YYYY-MM where possible. If only year is available, use YYYY.
        
        Resume text:
        {resume_text}
        
        Respond with only the parsed JSON. Do not include any other text.
        """
        
        # Get response from Gemini
        raw_response = self.gemini_service.generate_content(prompt)
        
        # Parse JSON response
        try:
            # Try to directly parse as JSON
            parsed_data = json.loads(raw_response)
            return parsed_data
        except json.JSONDecodeError:
            # Extract JSON from text response
            json_pattern = r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}'
            matches = re.search(json_pattern, raw_response)
            if matches:
                try:
                    json_str = matches.group(1) or matches.group(0)
                    return json.loads(json_str)
                except (json.JSONDecodeError, IndexError):
                    pass
            
            logger.error("Failed to parse Gemini response as JSON")
            raise ValueError("Invalid response format from Gemini")
    
    def analyze_resume_with_job(
        self,
        resume_text: str,
        job_description: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Perform deep analysis of resume against job description with enhanced capabilities.
        
        Args:
            resume_text: Raw resume text
            job_description: Job description text
            language: Language code (ISO 639-1)
            
        Returns:
            Analysis results with match scores and qualitative assessment
        """
        # Parse resume
        parsed_resume = self.parse_resume(resume_text, language)
        
        # If Gemini is available, use it for enhanced analysis
        if self.gemini_service:
            try:
                return self._analyze_with_gemini(parsed_resume, job_description)
            except Exception as e:
                logger.error(f"Enhanced resume analysis failed: {e}")
                logger.info("Falling back to base analysis method")
        
        # Fall back to base implementation with some enhancements
        analysis = super().analyze_resume_with_job(resume_text, job_description)
        
        # Add more detailed skill match information if available
        if "skill_details" in parsed_resume:
            skill_details = parsed_resume["skill_details"]
            analysis["detailed_skill_matches"] = self._analyze_skill_details(
                skill_details, job_description
            )
        
        return analysis
    
    def _analyze_with_gemini(
        self,
        parsed_resume: Dict[str, Any],
        job_description: str
    ) -> Dict[str, Any]:
        """
        Perform deep analysis using Gemini API.
        
        Args:
            parsed_resume: Structured resume data
            job_description: Job description text
            
        Returns:
            Enhanced analysis with detailed insights
        """
        # Convert parsed resume to string for prompt
        resume_json = json.dumps(parsed_resume, indent=2)
        
        # Create prompt for Gemini
        prompt = f"""
        Analyze the candidate's resume against the job description and provide a detailed assessment.
        
        Resume:
        {resume_json}
        
        Job Description:
        {job_description}
        
        Provide a detailed analysis including:
        1. Overall match score (0-100)
        2. Skill match details (matched skills, missing skills, skill match score)
        3. Experience match analysis (relevance, years, match score)
        4. Education match analysis (relevance, level, match score)
        5. Strengths of the candidate for this role
        6. Areas of concern or gaps
        7. Overall recommendation (Strongly Recommend, Recommend, Consider, Not Recommended)
        
        Format your response as structured JSON with the following fields:
        - overall_score: float
        - skill_match: {{score: float, matched_skills: list, missing_skills: list}}
        - experience_match: {{score: float, analysis: string}}
        - education_match: {{score: float, analysis: string}}
        - strengths: list of strings
        - gaps: list of strings
        - recommendation: string
        - detailed_analysis: string
        
        Respond with only the parsed JSON. Do not include any other text.
        """
        
        # Get response from Gemini
        raw_response = self.gemini_service.generate_content(prompt)
        
        # Parse JSON response
        try:
            # Try to directly parse as JSON
            analysis = json.loads(raw_response)
            return analysis
        except json.JSONDecodeError:
            # Extract JSON from text response
            json_pattern = r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}'
            matches = re.search(json_pattern, raw_response)
            if matches:
                try:
                    json_str = matches.group(1) or matches.group(0)
                    return json.loads(json_str)
                except (json.JSONDecodeError, IndexError):
                    pass
            
            logger.error("Failed to parse Gemini analysis response as JSON")
            raise ValueError("Invalid analysis response format from Gemini")
    
    def _analyze_skill_details(
        self,
        skill_details: List[Dict[str, Any]],
        job_description: str
    ) -> Dict[str, Any]:
        """
        Analyze detailed skill information against job description.
        
        Args:
            skill_details: List of detailed skill information
            job_description: Job description text
            
        Returns:
            Detailed skill match analysis
        """
        job_desc_lower = job_description.lower()
        
        # Categorize skills
        matched_skills = []
        for skill in skill_details:
            skill_name = skill["name"]
            skill_lower = skill_name.lower()
            
            # Check if skill is mentioned in job description
            is_matched = skill_lower in job_desc_lower
            
            # If skill has aliases, check those too
            if not is_matched and "aliases" in skill:
                for alias in skill["aliases"]:
                    if alias.lower() in job_desc_lower:
                        is_matched = True
                        break
            
            if is_matched:
                matched_skills.append({
                    "name": skill_name,
                    "category": skill.get("category", "unknown"),
                    "confidence": skill.get("confidence", 1.0),
                    "source": skill.get("source", "unknown")
                })
        
        # Calculate skill match score
        skills_count = len(skill_details)
        matched_count = len(matched_skills)
        
        if skills_count == 0:
            match_score = 0.0
        else:
            match_score = (matched_count / skills_count) * 100
        
        return {
            "matched_skills": matched_skills,
            "match_score": match_score,
            "total_skills": skills_count,
            "matched_count": matched_count
        }


# Factory function to get enhanced screening agent
def get_enhanced_screening_agent(vector_store=None) -> EnhancedScreeningAgent:
    """
    Get an instance of the EnhancedScreeningAgent.
    
    Args:
        vector_store: Optional vector store instance
        
    Returns:
        EnhancedScreeningAgent instance
    """
    return EnhancedScreeningAgent(vector_store)
