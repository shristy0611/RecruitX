#!/usr/bin/env python3
"""
End-to-end test for RecruitPro AI system.
Tests all components: infrastructure, knowledge base, screening agent, and API.
"""
import json
import logging
import os
import sys
import time
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Base URLs and endpoints
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
API_URL = f"http://{os.getenv('API_HOST', 'localhost')}:{os.getenv('API_PORT', '8000')}"
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

# Sample data for testing
SAMPLE_JOB = {
    "title": "Senior Machine Learning Engineer",
    "description": """
    We are seeking a Senior Machine Learning Engineer to join our AI team. 
    You will be responsible for designing and implementing machine learning models,
    collaborating with cross-functional teams, and deploying ML solutions at scale.
    """,
    "requirements": """
    - 5+ years of experience in machine learning or related field
    - Strong programming skills in Python
    - Experience with deep learning frameworks like PyTorch or TensorFlow
    - Knowledge of NLP, computer vision, or recommendation systems
    - Experience with cloud platforms (AWS, GCP, or Azure)
    - PhD or MS in Computer Science, Machine Learning, or related field
    """,
    "company": "RecruitPro AI",
    "location": "San Francisco, CA",
    "salary_range": "$150,000 - $200,000",
    "job_type": "Full-time"
}

SAMPLE_RESUME = """
JOHN SMITH
Data Scientist | Machine Learning Engineer
Email: john.smith@example.com | Phone: (555) 123-4567

SUMMARY
Passionate machine learning engineer with 6 years of experience building and deploying ML models at scale.
Expert in Python, PyTorch, and NLP. I've led projects that improved recommendation accuracy by 25%.

SKILLS
- Programming: Python, SQL, R
- Machine Learning: PyTorch, TensorFlow, Scikit-learn
- NLP: BERT, GPT, Transformers
- MLOps: Docker, Kubernetes, MLflow
- Cloud: AWS (SageMaker, Lambda, S3), GCP

EXPERIENCE
Senior Machine Learning Engineer | AI Innovations Inc. | 2020 - Present
- Developed and deployed production-ready NLP models for sentiment analysis
- Improved recommendation system accuracy by 25% using transformer-based models
- Mentored junior engineers and established ML best practices

Machine Learning Engineer | DataTech Solutions | 2017 - 2020
- Built computer vision models for object detection in retail settings
- Reduced inference time by 40% through model optimization techniques
- Implemented CI/CD pipeline for ML models

EDUCATION
MS in Computer Science, Stanford University, 2017
BS in Mathematics, MIT, 2015

PROJECTS
- Built an open-source NLP library for text summarization (10k+ GitHub stars)
- Created a real-time recommendation system for e-commerce (deployed to 1M+ users)
"""

SAMPLE_COMPANY = {
    "name": "RecruitPro AI",
    "description": "AI-powered recruitment solutions for modern enterprises",
    "culture": "Innovation-driven, remote-first company with focus on work-life balance",
    "benefits": "Competitive salary, health insurance, 401k matching, unlimited PTO",
    "industry": "Artificial Intelligence, HR Tech"
}


def test_infrastructure() -> None:
    """Test if all infrastructure components are running."""
    logger.info("Testing infrastructure...")
    
    # Test Weaviate
    try:
        response = requests.get(f"{WEAVIATE_URL}/v1/.well-known/ready")
        if response.status_code == 200:
            logger.info("✅ Weaviate is running")
        else:
            logger.error(f"❌ Weaviate is not ready: {response.status_code}")
            raise Exception("Weaviate infrastructure test failed")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Weaviate: {e}")
        raise
    
    # Test API
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            logger.info("✅ API is running")
        else:
            logger.error(f"❌ API is not ready: {response.status_code}")
            raise Exception("API infrastructure test failed")
    except Exception as e:
        logger.error(f"❌ Failed to connect to API: {e}")
        logger.info("   Note: API test will be skipped. Make sure the API is running with 'uvicorn src.api.app:app --host 0.0.0.0 --port 8000'")


def test_knowledge_base() -> None:
    """Test knowledge base operations: add, get, and search."""
    logger.info("Testing knowledge base operations...")
    
    # Import here to avoid circular imports
    from src.knowledge_base.vector_store import get_vector_store
    
    # Initialize vector store
    try:
        vector_store = get_vector_store()
        logger.info("✅ Vector store initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize vector store: {e}")
        raise
    
    # Test adding a job description
    try:
        job_id = vector_store.add_job_description(
            title=SAMPLE_JOB["title"],
            description=SAMPLE_JOB["description"],
            requirements=SAMPLE_JOB["requirements"],
            company=SAMPLE_JOB["company"],
            location=SAMPLE_JOB["location"],
            salary_range=SAMPLE_JOB["salary_range"],
            job_type=SAMPLE_JOB["job_type"]
        )
        logger.info(f"✅ Job added successfully with ID: {job_id}")
    except Exception as e:
        logger.error(f"❌ Failed to add job: {e}")
        raise
    
    # Test retrieving a job description
    try:
        job = vector_store.get_by_id("JobDescription", job_id)
        if job and job.get("title") == SAMPLE_JOB["title"]:
            logger.info(f"✅ Job retrieved successfully: {job.get('title')}")
        else:
            logger.error("❌ Retrieved job does not match the added job")
            raise Exception("Job retrieval test failed")
    except Exception as e:
        logger.error(f"❌ Failed to retrieve job: {e}")
        raise
    
    # Test semantic search
    try:
        search_results = vector_store.search(
            class_name="JobDescription",
            query="machine learning python deep learning",
            limit=3
        )
        if search_results and len(search_results) > 0:
            logger.info(f"✅ Search returned {len(search_results)} results")
            for i, result in enumerate(search_results, 1):
                logger.info(f"  Result {i}: {result.get('title')} (certainty: {result.get('_additional', {}).get('certainty', 0):.2f})")
        else:
            logger.error("❌ Search returned no results")
            raise Exception("Semantic search test failed")
    except Exception as e:
        logger.error(f"❌ Failed to perform search: {e}")
        raise
    
    # Clean up test data
    try:
        deleted = vector_store.delete_object("JobDescription", job_id)
        if deleted:
            logger.info(f"✅ Job deleted successfully: {job_id}")
        else:
            logger.warning(f"⚠️ Failed to delete job: {job_id}")
    except Exception as e:
        logger.warning(f"⚠️ Error during cleanup: {e}")
    
    return job_id  # Return for use in other tests


def test_screening_agent(job_id: str) -> None:
    """Test screening agent's resume parsing and job matching capabilities."""
    logger.info("Testing screening agent...")
    
    # Import here to avoid circular imports
    from src.agents.screening_agent import ScreeningAgent
    from src.knowledge_base.vector_store import get_vector_store
    
    try:
        vector_store = get_vector_store()
        screening_agent = ScreeningAgent(vector_store)
        logger.info("✅ Screening agent initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize screening agent: {e}")
        raise
    
    # Test resume parsing
    try:
        parsed_resume = screening_agent.parse_resume(SAMPLE_RESUME)
        if parsed_resume:
            logger.info("✅ Resume parsed successfully")
            logger.info(f"  Extracted {len(parsed_resume.get('skills', []))} skills")
            logger.info(f"  Education: {parsed_resume.get('education', 'Not found')[:50]}...")
            logger.info(f"  Experience: {parsed_resume.get('experience', 'Not found')[:50]}...")
        else:
            logger.error("❌ Failed to parse resume")
            raise Exception("Resume parsing test failed")
    except Exception as e:
        logger.error(f"❌ Failed to parse resume: {e}")
        raise
    
    # Test job matching
    try:
        match_score = screening_agent.score_candidate_for_job(
            resume_text=SAMPLE_RESUME,
            job_id=job_id
        )
        if match_score:
            logger.info(f"✅ Candidate matched successfully with score: {match_score.get('score', 0):.2f}")
            logger.info(f"  Explanation: {match_score.get('explanation', '')[:100]}...")
        else:
            logger.error("❌ Failed to match candidate")
            raise Exception("Job matching test failed")
    except Exception as e:
        logger.error(f"❌ Failed to match candidate: {e}")
        raise


def test_api() -> None:
    """Test API endpoints for job management and candidate screening."""
    logger.info("Testing API endpoints...")
    
    # Check if API is running
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code != 200:
            logger.error(f"❌ API is not ready: {response.status_code}")
            logger.info("   Skipping API tests")
            return
    except Exception:
        logger.info("   API is not running. Skipping API tests")
        return
    
    # Test creating a job
    job_id = None
    try:
        response = requests.post(
            f"{API_URL}{API_PREFIX}/jobs",
            json=SAMPLE_JOB
        )
        if response.status_code == 201:
            job_data = response.json()
            job_id = job_data.get("id")
            logger.info(f"✅ Job created via API with ID: {job_id}")
        else:
            logger.error(f"❌ Failed to create job via API: {response.status_code} {response.text}")
            raise Exception("Job creation API test failed")
    except Exception as e:
        logger.error(f"❌ Failed to create job via API: {e}")
        raise
    
    # Test retrieving a job
    try:
        response = requests.get(f"{API_URL}{API_PREFIX}/jobs/{job_id}")
        if response.status_code == 200:
            job_data = response.json()
            if job_data.get("title") == SAMPLE_JOB["title"]:
                logger.info(f"✅ Job retrieved via API: {job_data.get('title')}")
            else:
                logger.error("❌ Retrieved job does not match the added job")
                raise Exception("Job retrieval API test failed")
        else:
            logger.error(f"❌ Failed to retrieve job via API: {response.status_code} {response.text}")
            raise Exception("Job retrieval API test failed")
    except Exception as e:
        logger.error(f"❌ Failed to retrieve job via API: {e}")
        raise
    
    # Test upload and analyze resume
    try:
        response = requests.post(
            f"{API_URL}{API_PREFIX}/candidates/analyze_text",
            json={
                "resume_text": SAMPLE_RESUME,
                "job_id": job_id
            }
        )
        if response.status_code == 200:
            analysis_data = response.json()
            logger.info(f"✅ Resume analyzed via API with score: {analysis_data.get('score', 0)}")
            logger.info(f"  Explanation: {analysis_data.get('explanation', '')[:100]}...")
        else:
            logger.error(f"❌ Failed to analyze resume via API: {response.status_code} {response.text}")
            raise Exception("Resume analysis API test failed")
    except Exception as e:
        logger.error(f"❌ Failed to analyze resume via API: {e}")
        raise
    
    # Clean up test data
    try:
        response = requests.delete(f"{API_URL}{API_PREFIX}/jobs/{job_id}")
        if response.status_code == 204:
            logger.info(f"✅ Job deleted via API: {job_id}")
        else:
            logger.warning(f"⚠️ Failed to delete job via API: {response.status_code} {response.text}")
    except Exception as e:
        logger.warning(f"⚠️ Error during API cleanup: {e}")


def run_all_tests() -> None:
    """Run all end-to-end tests."""
    logger.info("Starting end-to-end tests for RecruitPro AI")
    logger.info("=" * 80)
    
    try:
        test_infrastructure()
        logger.info("=" * 80)
        
        job_id = test_knowledge_base()
        logger.info("=" * 80)
        
        test_screening_agent(job_id)
        logger.info("=" * 80)
        
        test_api()
        logger.info("=" * 80)
        
        logger.info("🎉 All tests completed successfully!")
    except Exception as e:
        logger.error(f"❌ Tests failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
