"""
Test script for all XAI explainers.

This script demonstrates how to use the XAI module with each agent type.
"""
import os
import sys
import json
import logging
from typing import Dict, Any, List

# Add the parent directory to the path to allow importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.xai import get_explainer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_matching_explainer():
    """Test the MatchingExplainer with sample data."""
    logger.info("=== Testing MatchingExplainer ===")
    explainer = get_explainer("matching")
    
    # Sample context for matching explanation
    context = {
        "candidate_profile": {
            "name": "Emily Chen",
            "skills": ["Python", "JavaScript", "React", "Machine Learning", "Data Visualization"],
            "experience": "4 years of experience as a Full Stack Developer at TechCorp. Led frontend development for multiple projects."
        },
        "job_description": {
            "title": "Senior Full Stack Developer",
            "company": "InnovateTech",
            "description": "Looking for an experienced Full Stack Developer with JavaScript, React, and Python skills.",
            "requirements": "4+ years of experience in full stack development. Strong JavaScript and React skills required."
        },
        "match_result": {
            "overall_score": 88.0,
            "factors": {
                "skills_score": 92.0,
                "experience_score": 85.0,
                "education_score": 80.0
            },
            "matched_skills": ["Python", "JavaScript", "React"],
            "missing_skills": ["Node.js", "AWS"]
        }
    }
    
    # Generate explanation
    explanation = explainer.generate_explanation(context, detail_level="standard")
    
    # Print results
    logger.info(f"Explanation: {explanation['explanation']}")
    if "factor_explanations" in explanation:
        logger.info("\nFactor Explanations:")
        for factor, factor_explanation in explanation["factor_explanations"].items():
            logger.info(f"\n{factor}: {factor_explanation}")


def test_sourcing_explainer():
    """Test the SourcingExplainer with sample data."""
    logger.info("\n=== Testing SourcingExplainer ===")
    explainer = get_explainer("sourcing")
    
    # Sample context for sourcing explanation
    context = {
        "job_description": {
            "title": "Data Scientist",
            "company": "AnalyticsPro",
            "description": "Looking for a Data Scientist with Python, SQL, and machine learning experience."
        },
        "sourcing_query": {
            "keywords": ["Python", "SQL", "machine learning", "data science"],
            "experience_level": "mid-senior",
            "location": "San Francisco, CA"
        },
        "candidates": [
            {
                "name": "Alex Johnson",
                "score": 89.5,
                "skills": ["Python", "SQL", "Machine Learning", "TensorFlow"],
                "experience": "5 years as Data Scientist at DataCorp"
            },
            {
                "name": "Sarah Williams",
                "score": 84.2,
                "skills": ["Python", "SQL", "R", "Tableau"],
                "experience": "4 years as Data Analyst at AnalyticsInc"
            },
            {
                "name": "Michael Zhang",
                "score": 79.8,
                "skills": ["Python", "SQL", "Scikit-learn", "Pandas"],
                "experience": "3 years as Data Engineer at TechGlobal"
            }
        ],
        "search_strategy": "semantic search with vector embeddings",
        "filters": {
            "min_experience": 3,
            "location": "San Francisco Bay Area",
            "skills_required": ["Python", "SQL"]
        }
    }
    
    # Generate explanation
    explanation = explainer.generate_explanation(context, detail_level="standard")
    
    # Print results
    logger.info(f"Explanation: {explanation['explanation']}")
    logger.info(f"\nStrategy Used: {explanation['strategy']}")
    logger.info(f"Filters Applied: {explanation['filters_applied']}")


def test_screening_explainer():
    """Test the ScreeningExplainer with sample data."""
    logger.info("\n=== Testing ScreeningExplainer ===")
    explainer = get_explainer("screening")
    
    # Sample context for screening explanation
    context = {
        "candidate_profile": {
            "name": "David Lee",
            "summary": "Software Engineer with 6 years of experience in backend development",
            "skills": ["Java", "Spring Boot", "Kubernetes", "Docker", "Microservices"],
            "experience": "6 years of experience, including 4 years at EnterpriseApps and 2 years at CloudSolutions",
            "education": "Bachelor's in Computer Science from Stanford University"
        },
        "job_description": {
            "title": "Senior Backend Engineer",
            "company": "CloudTech Inc",
            "requirements": "5+ years of experience in backend development with Java. Experience with Kubernetes and microservices architecture required."
        },
        "screening_result": {
            "decision": "pass",
            "overall_score": 85.5,
            "criteria": {
                "skills_match": 90.0,
                "experience_match": 85.0,
                "education_match": 75.0,
                "culture_fit": 80.0
            }
        }
    }
    
    # Generate explanation
    explanation = explainer.generate_explanation(context, detail_level="detailed")
    
    # Print results
    logger.info(f"Decision: {explanation['decision']}")
    logger.info(f"Score: {explanation['score']}")
    logger.info(f"Explanation: {explanation['explanation']}")
    
    if "key_findings" in explanation:
        logger.info("\nKey Findings:")
        for finding in explanation["key_findings"]:
            logger.info(f"- {finding}")


if __name__ == "__main__":
    # Test all explainers
    test_matching_explainer()
    test_sourcing_explainer()
    test_screening_explainer()
