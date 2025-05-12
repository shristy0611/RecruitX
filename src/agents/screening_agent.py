"""
Screening Agent for RecruitPro AI.

This agent is responsible for parsing resumes, extracting key information
(skills, experience, education), and scoring candidates against job requirements.
It uses a combination of NLP techniques and LLM-based reasoning to perform
deep analysis of resume content.
"""
import logging
import os
import re
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import spacy
import numpy as np
from langchain.chains import RetrievalQA
from langchain.llms.base import BaseLLM
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.vectorstores import VectorStore as LangchainVectorStore
from langchain.embeddings.base import Embeddings
from langchain.embeddings import HuggingFaceEmbeddings
from sentence_transformers import util as st_util

from src.knowledge_base.vector_store import get_vector_store
from src.utils.config import (
    USE_LOCAL_LLM,
    LOCAL_LLM_URL,
    LOCAL_LLM_MODEL,
    EMBEDDING_MODEL,
)

logger = logging.getLogger(__name__)

# Load spaCy NLP model for entity recognition and text processing
try:
    nlp = spacy.load("en_core_web_md")
except:
    logger.warning("Could not load en_core_web_md, downloading...")
    spacy.cli.download("en_core_web_md")
    nlp = spacy.load("en_core_web_md")


class ScreeningAgent:
    """
    Screening Agent for candidate resume analysis and evaluation.
    
    This agent:
    1. Parses resumes to extract structured information
    2. Identifies key skills, experience, and qualifications
    3. Evaluates candidates against job requirements
    4. Provides explainable scoring and recommendations
    """

    def __init__(self, vector_store=None):
        """Initialize the Screening Agent with necessary components.
        
        Args:
            vector_store: Optional VectorStore instance. If not provided, a new instance will be created.
        """
        self.vector_store = vector_store if vector_store is not None else get_vector_store()
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Only initialize LLM when needed (lazy loading)
        self._llm = None
        
        # Initialize skill extraction patterns
        self._init_skill_patterns()

    def _init_skill_patterns(self):
        """Initialize patterns for skill extraction."""
        # Common skill-related tokens
        self.skill_patterns = [
            # Programming languages
            r"\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|Ruby|Go|Rust|PHP|Swift|Kotlin)\b",
            # Frameworks and libraries
            r"\b(?:React|Angular|Vue\.js|Django|Flask|Spring|Express|TensorFlow|PyTorch|Scikit-learn)\b",
            # Database technologies
            r"\b(?:SQL|MySQL|PostgreSQL|MongoDB|Oracle|Redis|Elasticsearch|Cassandra)\b",
            # Cloud platforms
            r"\b(?:AWS|Amazon Web Services|Azure|Google Cloud|GCP|Kubernetes|Docker|Terraform)\b",
            # Data science & ML
            r"\b(?:Machine Learning|Deep Learning|NLP|Computer Vision|Data Mining|Statistics|R|MATLAB)\b",
            # General skills (match with word boundaries to avoid partial matches)
            r"\b(?:Leadership|Project Management|Agile|Scrum|Communication|Teamwork|Problem-solving)\b"
        ]
        self.skill_regex = re.compile("|".join(self.skill_patterns), re.IGNORECASE)

    @property
    def llm(self) -> BaseLLM:
        """
        Get or initialize the LLM for the agent.
        Lazy loading to avoid initialization if not needed.
        
        Returns:
            BaseLLM: Language model instance
        """
        if self._llm is None:
            if USE_LOCAL_LLM:
                # Use local model via Ollama
                try:
                    from langchain.llms import Ollama
                    self._llm = Ollama(model=LOCAL_LLM_MODEL, base_url=LOCAL_LLM_URL)
                    logger.info(f"Initialized local LLM: {LOCAL_LLM_MODEL}")
                except Exception as e:
                    logger.error(f"Failed to initialize local LLM: {e}")
                    # Fall back to a simple local model
                    from langchain_community.llms import HuggingFacePipeline
                    import torch
                    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
                    
                    model_id = "TheBloke/Llama-2-7B-Chat-GGUF"
                    tokenizer = AutoTokenizer.from_pretrained(model_id)
                    model = AutoModelForCausalLM.from_pretrained(
                        model_id, 
                        device_map="auto",
                        torch_dtype=torch.float16,
                        load_in_8bit=True
                    )
                    pipe = pipeline(
                        "text-generation",
                        model=model,
                        tokenizer=tokenizer,
                        max_new_tokens=512
                    )
                    self._llm = HuggingFacePipeline(pipeline=pipe)
                    logger.info(f"Initialized fallback Hugging Face pipeline LLM")
            else:
                # Use cloud-based LLM (Gemini API or OpenAI)
                # Implement once we decide to use cloud LLMs
                logger.warning("Cloud LLM support not implemented yet. Using placeholder LLM.")
                from langchain.llms.fake import FakeListLLM
                self._llm = FakeListLLM(responses=["This is a placeholder LLM response."])
                
        return self._llm

    def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Parse raw resume text into structured information.
        
        Args:
            resume_text: Raw text of the resume
            
        Returns:
            Dictionary containing structured resume information
        """
        # Process with spaCy for entity recognition
        doc = nlp(resume_text)
        
        # Extract contact information using regex patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        
        emails = re.findall(email_pattern, resume_text)
        phones = re.findall(phone_pattern, resume_text)
        
        # Extract skills using predefined patterns
        skills = self._extract_skills(resume_text)
        
        # Extract education (look for common degrees and institutions)
        education_entities = []
        for ent in doc.ents:
            if ent.label_ == "ORG" and any(edu_term in ent.text.lower() for edu_term in 
                                         ["university", "college", "institute", "school"]):
                education_entities.append(ent.text)
        
        # Attempt to extract sections using common resume section headers
        sections = self._extract_resume_sections(resume_text)
        
        # Build structured resume data
        resume_data = {
            "contact_info": {
                "email": emails[0] if emails else "",
                "phone": phones[0] if phones else ""
            },
            "name": self._extract_name(doc),
            "skills": skills,
            "education": education_entities,
            "sections": sections,
            "raw_text": resume_text
        }
        
        return resume_data

    def _extract_name(self, doc) -> str:
        """
        Extract candidate name from spaCy doc.
        Looks for PERSON entities in the first paragraph.
        
        Args:
            doc: spaCy processed document
            
        Returns:
            Extracted name or empty string if not found
        """
        # Assume the first PERSON entity in the first few sentences is the candidate's name
        for sent_idx, sent in enumerate(doc.sents):
            if sent_idx > 3:  # Only check first few sentences
                break
            for ent in sent.ents:
                if ent.label_ == "PERSON":
                    return ent.text
        return ""

    def _extract_skills(self, text: str) -> List[str]:
        """
        Extract skills from resume text using regex patterns.
        
        Args:
            text: Resume text
            
        Returns:
            List of identified skills
        """
        # Find all matches
        matches = self.skill_regex.findall(text)
        
        # Normalize and deduplicate
        skills = []
        for match in matches:
            # Find which pattern matched
            for pattern in self.skill_patterns:
                pattern_regex = re.compile(pattern, re.IGNORECASE)
                if pattern_regex.search(match):
                    skill = match.strip()
                    if skill and skill.lower() not in [s.lower() for s in skills]:
                        skills.append(skill)
        
        return skills

    def _extract_resume_sections(self, text: str) -> Dict[str, str]:
        """
        Extract common resume sections based on headers.
        
        Args:
            text: Resume text
            
        Returns:
            Dictionary mapping section names to content
        """
        # Common section headers in resumes
        section_patterns = {
            "summary": r"(?:summary|professional summary|profile|objective)",
            "experience": r"(?:experience|work experience|employment|work history)",
            "education": r"(?:education|educational background|academic background|qualifications)",
            "skills": r"(?:skills|technical skills|competencies|expertise)",
            "projects": r"(?:projects|professional projects|personal projects)",
            "certifications": r"(?:certifications|certificates|licenses)",
            "awards": r"(?:awards|honors|achievements)",
            "languages": r"(?:languages|language proficiency)"
        }
        
        sections = {}
        
        # Split text by lines
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            matched_section = None
            for section, pattern in section_patterns.items():
                if re.search(pattern, line, re.IGNORECASE) and len(line) < 50:  # Assume headers are not too long
                    matched_section = section
                    break
                    
            if matched_section:
                # Save previous section if any
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                    
                # Start new section
                current_section = matched_section
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save the last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
            
        return sections

    def score_resume_against_job(
        self, 
        resume_data: Dict[str, Any], 
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score a resume against job requirements.
        
        Args:
            resume_data: Structured resume data from parse_resume
            job_data: Job description data
            
        Returns:
            Dictionary with scores and explanations
        """
        # Extract job requirements
        job_title = job_data.get("title", "")
        job_description = job_data.get("description", "")
        job_requirements = job_data.get("requirements", "")
        
        # Prepare text for embedding
        job_text = f"{job_title}. {job_description}. {job_requirements}"
        
        # Get resume text
        if isinstance(resume_data, dict) and "raw_text" in resume_data:
            resume_text = resume_data["raw_text"]
        else:
            resume_text = resume_data  # Assume it's the raw text if not a dict
            
        # Compute semantic similarity
        job_embedding = self.embeddings.embed_query(job_text)
        resume_embedding = self.embeddings.embed_query(resume_text)
        
        # Convert to numpy arrays and compute cosine similarity
        similarity = float(st_util.cos_sim(
            np.array(job_embedding).reshape(1, -1),
            np.array(resume_embedding).reshape(1, -1)
        )[0][0])
        
        # Scale similarity to a 0-100 score and build detailed scoring using LLM
        overall_score = min(100, max(0, int(similarity * 100)))
        
        # Compute component scores
        skills_score = self._calculate_skills_score(resume_data, job_data)
        experience_score = self._calculate_experience_score(resume_data, job_data)
        education_score = self._calculate_education_score(resume_data, job_data)
        
        # Calculate final weighted score
        final_score = (
            overall_score * 0.4 +
            skills_score * 0.3 +
            experience_score * 0.2 +
            education_score * 0.1
        )
        
        # Get explanation if LLM is available
        explanation = self._generate_score_explanation(
            resume_data, job_data, overall_score, skills_score, experience_score, education_score
        )
        
        return {
            "overall_score": overall_score,
            "skills_score": skills_score,
            "experience_score": experience_score,
            "education_score": education_score,
            "final_score": final_score,
            "explanation": explanation,
            "timestamp": str(datetime.now().isoformat()),
        }

    def _calculate_skills_score(
        self, 
        resume_data: Dict[str, Any], 
        job_data: Dict[str, Any]
    ) -> float:
        """
        Calculate skills match score.
        
        Args:
            resume_data: Structured resume data
            job_data: Job description data
            
        Returns:
            Skills score (0-100)
        """
        # Extract skills from resume
        resume_skills = resume_data.get("skills", [])
        if not resume_skills and "raw_text" in resume_data:
            # Try to extract skills if not already present
            resume_skills = self._extract_skills(resume_data["raw_text"])
            
        # Extract required skills from job description
        job_requirements = job_data.get("requirements", "")
        job_skills = self._extract_skills(job_requirements)
        
        if not job_skills or not resume_skills:
            return 50  # Default score if no skills found
        
        # Calculate match percentage
        matches = 0
        for job_skill in job_skills:
            if any(re.search(re.escape(job_skill), skill, re.IGNORECASE) for skill in resume_skills):
                matches += 1
                
        match_percentage = (matches / len(job_skills)) * 100 if job_skills else 0
        return min(100, max(0, match_percentage))

    def _calculate_experience_score(
        self, 
        resume_data: Dict[str, Any], 
        job_data: Dict[str, Any]
    ) -> float:
        """
        Calculate experience match score.
        
        Args:
            resume_data: Structured resume data
            job_data: Job description data
            
        Returns:
            Experience score (0-100)
        """
        # Default score
        default_score = 50
        
        # Check if we have the necessary sections
        sections = resume_data.get("sections", {})
        if "experience" not in sections:
            return default_score
            
        # Get experience text
        experience_text = sections["experience"]
        
        # Get job description and requirements
        job_title = job_data.get("title", "")
        job_requirements = job_data.get("requirements", "")
        
        # Use text similarity as proxy for experience match
        job_exp_text = f"{job_title} {job_requirements}"
        
        # Compute similarity
        job_embedding = self.embeddings.embed_query(job_exp_text)
        exp_embedding = self.embeddings.embed_query(experience_text)
        
        similarity = float(st_util.cos_sim(
            np.array(job_embedding).reshape(1, -1),
            np.array(exp_embedding).reshape(1, -1)
        )[0][0])
        
        # Scale to 0-100
        return min(100, max(0, int(similarity * 100)))

    def _calculate_education_score(
        self, 
        resume_data: Dict[str, Any], 
        job_data: Dict[str, Any]
    ) -> float:
        """
        Calculate education match score.
        
        Args:
            resume_data: Structured resume data
            job_data: Job description data
            
        Returns:
            Education score (0-100)
        """
        # Default score
        default_score = 50
        
        # Extract education information
        education_entities = resume_data.get("education", [])
        
        # If no education found in entities, try sections
        if not education_entities and "sections" in resume_data:
            sections = resume_data["sections"]
            if "education" in sections:
                education_text = sections["education"]
                # Look for degree keywords
                degree_keywords = [
                    "bachelor", "master", "phd", "doctorate", "mba",
                    "bs", "ba", "ms", "ma", "bsc", "msc", "b.s.", "m.s."
                ]
                
                if any(keyword in education_text.lower() for keyword in degree_keywords):
                    return 75  # Above average if degrees found
        
        # If we have entities, assume at least average match
        if education_entities:
            return 60
            
        return default_score

    def _generate_score_explanation(
        self,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any],
        overall_score: float,
        skills_score: float,
        experience_score: float,
        education_score: float
    ) -> str:
        """
        Generate an explanation for the scoring using the LLM.
        
        Args:
            resume_data: Structured resume data
            job_data: Job description data
            overall_score: Overall match score
            skills_score: Skills match score
            experience_score: Experience match score
            education_score: Education match score
            
        Returns:
            Explanation string
        """
        try:
            # Create prompt for LLM
            prompt_template = PromptTemplate(
                input_variables=["job_title", "job_requirements", "candidate_skills", 
                                "candidate_experience", "overall_score", "skills_score", 
                                "experience_score", "education_score"],
                template="""
                You are an AI recruitment assistant evaluating a candidate for a job.
                
                Job Title: {job_title}
                Job Requirements: {job_requirements}
                
                Candidate Skills: {candidate_skills}
                Candidate Experience: {candidate_experience}
                
                Scores:
                - Overall Match: {overall_score}/100
                - Skills Match: {skills_score}/100
                - Experience Match: {experience_score}/100
                - Education Match: {education_score}/100
                
                Provide a brief, objective assessment explaining these scores. Highlight strengths and potential gaps.
                Keep the response under 150 words and focus on actionable insights. Be factual, not encouraging or discouraging.
                """
            )
            
            # Prepare inputs
            candidate_skills = ", ".join(resume_data.get("skills", []))
            candidate_experience = resume_data.get("sections", {}).get("experience", "No detailed experience information")
            
            # Truncate long texts
            candidate_experience = candidate_experience[:500] + "..." if len(candidate_experience) > 500 else candidate_experience
            
            # Format prompt
            prompt = prompt_template.format(
                job_title=job_data.get("title", ""),
                job_requirements=job_data.get("requirements", "")[:500],
                candidate_skills=candidate_skills,
                candidate_experience=candidate_experience,
                overall_score=overall_score,
                skills_score=skills_score,
                experience_score=experience_score,
                education_score=education_score
            )
            
            # Get explanation from LLM
            explanation = self.llm.predict(prompt)
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating score explanation: {e}")
            # Fallback explanation if LLM fails
            return f"""
            Candidate scored {overall_score}/100 overall. Skills match: {skills_score}/100. 
            Experience match: {experience_score}/100. Education match: {education_score}/100.
            """

    def score_candidate_for_job(self, resume_text: str, job_id: str) -> Dict[str, Any]:
        """
        Score a candidate's resume against a specific job.
        This is the main method called by the API and tests.
        
        Args:
            resume_text: Raw resume text
            job_id: Job ID to match against
            
        Returns:
            Dictionary with score and explanation
        """
        # Parse the resume
        resume_data = self.parse_resume(resume_text)
        
        # Get job data
        job_data = self.vector_store.get_by_id("JobDescription", job_id)
        if not job_data:
            logger.error(f"Job not found: {job_id}")
            return {
                "score": 0,
                "explanation": "Error: Job not found"
            }
            
        # Score the resume against the job
        score_data = self.score_resume_against_job(resume_data, job_data)
        
        return {
            "score": score_data["final_score"],
            "explanation": score_data["explanation"],
            "skills_score": score_data["skills_score"],
            "experience_score": score_data["experience_score"],
            "education_score": score_data["education_score"]
        }

    def process_resume(self, resume_text: str, job_id: str) -> Dict[str, Any]:
        """
        Process a resume against a specific job.
        Main entry point for the screening agent.
        
        Args:
            resume_text: Raw resume text
            job_id: Job ID to match against
            
        Returns:
            Dictionary with structured resume data and job match scores
        """
        try:
            # Parse the resume
            resume_data = self.parse_resume(resume_text)
            
            # Get job data
            job_data = self.vector_store.get_by_id("JobDescription", job_id)
            if not job_data:
                raise ValueError(f"Job with ID {job_id} not found")
                
            # In our VectorStore implementation, properties are already at the top level
            # The get_by_id method already extracts properties from the Weaviate response
            job_properties = job_data
            
            # Score resume against job
            score_data = self.score_resume_against_job(resume_data, job_properties)
            
            # Combine results
            result = {
                "resume_data": resume_data,
                "job_data": job_properties,
                "score_data": score_data
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing resume: {e}")
            return {
                "error": str(e),
                "resume_data": None,
                "job_data": None,
                "score_data": None
            }


# Generate a singleton instance
_screening_agent: Optional[ScreeningAgent] = None


def get_screening_agent() -> ScreeningAgent:
    """
    Get or create the ScreeningAgent singleton instance.
    
    Returns:
        ScreeningAgent instance
    """
    global _screening_agent
    if _screening_agent is None:
        _screening_agent = ScreeningAgent()
    return _screening_agent
