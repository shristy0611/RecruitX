#!/usr/bin/env python
"""
Test script for the RecruitPro AI Knowledge Base.

This script validates the functionality of our vector database implementation
by creating a job description and performing a search with a sample query.
"""
import logging
import sys
from typing import Dict, Any

from src.knowledge_base.vector_store import get_vector_store
from src.utils.config import WEAVIATE_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_knowledge_base():
    """Run tests on the knowledge base implementation."""
    logger.info("Testing Knowledge Base with Weaviate URL: %s", WEAVIATE_URL)
    
    # Initialize vector store
    try:
        vector_store = get_vector_store()
        logger.info("Vector store initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize vector store: %s", e)
        return False
    
    # Test job description creation
    job_id = None
    try:
        logger.info("Creating test job description")
        job_id = vector_store.add_job_description(
            title="Senior Machine Learning Engineer",
            description="""
            We are looking for a Senior Machine Learning Engineer to join our AI team. 
            You will be responsible for developing and deploying machine learning models,
            working on cutting-edge AI applications, and collaborating with cross-functional teams.
            The ideal candidate has experience with deep learning, NLP, and productionizing ML models.
            """,
            requirements="""
            - 5+ years of experience in machine learning and data science
            - Strong programming skills in Python and PyTorch or TensorFlow
            - Experience with NLP, transformers, and large language models
            - Familiarity with MLOps and model deployment pipelines
            - Experience with cloud platforms (AWS, GCP, or Azure)
            - Strong communication and collaboration skills
            - MS or PhD in Computer Science, Machine Learning, or related field
            """,
            company="AI Innovations Inc.",
            location="San Francisco, CA (Remote)",
            salary_range="$150,000 - $200,000",
            job_type="Full-time"
        )
        logger.info("Job created with ID: %s", job_id)
    except Exception as e:
        logger.error("Error creating job description: %s", e)
        return False
    
    if not job_id:
        logger.error("Failed to create job description")
        return False
    
    # Test retrieval
    try:
        logger.info("Retrieving job by ID")
        job = vector_store.get_by_id("JobDescription", job_id)
        if not job:
            logger.error("Failed to retrieve job by ID")
            return False
        
        logger.info("Job retrieved successfully: %s", job.get("id"))
        logger.info("Job title: %s", job.get("properties", {}).get("title"))
    except Exception as e:
        logger.error("Error retrieving job: %s", e)
        return False
    
    # Test search
    try:
        logger.info("Testing semantic search")
        results = vector_store.search(
            class_name="JobDescription",
            query="machine learning engineer with Python and NLP experience",
            limit=5
        )
        
        logger.info("Search returned %d results", len(results))
        for i, result in enumerate(results):
            certainty = result.get("certainty", 0)
            title = result.get("properties", {}).get("title", "Unknown")
            logger.info("Result %d: %s (certainty: %.2f)", i+1, title, certainty)
    except Exception as e:
        logger.error("Error performing search: %s", e)
        return False
    
    logger.info("All tests completed successfully!")
    return True


if __name__ == "__main__":
    success = test_knowledge_base()
    sys.exit(0 if success else 1)
