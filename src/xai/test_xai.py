"""
Test script for the Explainable AI (XAI) module.

This script tests the functionality of the XAI module by generating
explanations for matching decisions using real data from the vector store.
"""
import os
import sys
import json
import logging
from typing import Dict, Any, List

# Add the parent directory to the path to allow importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.xai.matching_explainer import MatchingExplainer
from src.knowledge_base.vector_store import VectorStore
from src.agents.matching_agent import MatchingAgent
from src.llm import get_llm_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_matching_explanations():
    """Test the generation of explanations for matching decisions."""
    try:
        # Initialize the vector store
        vector_store = VectorStore()
        
        # Get a sample job and candidate
        logger.info("Finding a sample job and candidate...")
        jobs = vector_store.search(class_name="Job", properties=["title", "description"], limit=1)
        candidates = vector_store.search(class_name="Candidate", properties=["name", "resume"], limit=3)
        
        if not jobs or not candidates:
            logger.error("No jobs or candidates found in the vector store")
            return
        
        job = jobs[0]
        job_id = job.get("id")
        
        # Initialize the matching agent
        matching_agent = MatchingAgent(vector_store=vector_store)
        
        # Get candidate IDs
        candidate_ids = [candidate.get("id") for candidate in candidates]
        
        # Match candidates to the job
        logger.info(f"Matching candidates to job: {job.get('title', 'Unknown Job')}")
        matching_results = matching_agent.match_candidates(
            job_id=job_id,
            candidate_ids=candidate_ids,
            require_explanation=False  # Don't generate explanations during matching
        )
        
        if not matching_results:
            logger.error("No matching results returned")
            return
        
        # Generate detailed explanations for each match
        logger.info("Generating detailed explanations...")
        for match_result in matching_results:
            candidate_id = match_result.candidate_id
            logger.info(f"Generating explanation for candidate {candidate_id}...")
            
            # Get candidate details
            candidate = next((c for c in candidates if c.get("id") == candidate_id), None)
            if not candidate:
                logger.warning(f"Candidate {candidate_id} not found in vector store results")
                continue
                
            logger.info(f"Testing explanation for: {candidate.get('name', 'Unknown Candidate')}")
            
            # Test standard explanation
            detailed_explanation = matching_agent.get_detailed_explanation(
                job_id=job_id,
                candidate_id=candidate_id,
                detail_level="standard"
            )
            
            # Print the explanation
            logger.info(f"Match Score: {detailed_explanation.get('score', 0.0):.2f}")
            logger.info("Explanation:\n" + detailed_explanation.get("explanation", "No explanation generated"))
            
            # If the explanation has factor explanations, print them too
            if "factor_explanations" in detailed_explanation:
                logger.info("\nFactor Explanations:")
                for factor, explanation in detailed_explanation["factor_explanations"].items():
                    logger.info(f"\n{factor.replace('_score', '').capitalize()}:\n{explanation}")
            
            # Test brief explanation
            brief_explanation = matching_agent.get_detailed_explanation(
                job_id=job_id,
                candidate_id=candidate_id,
                detail_level="brief"
            )
            logger.info("\nBrief Explanation:\n" + brief_explanation.get("explanation", "No explanation generated"))
            
            # Only test one candidate to avoid too many API calls
            break
        
        logger.info("XAI testing completed successfully")
        
    except Exception as e:
        logger.error(f"Error testing XAI module: {e}", exc_info=True)


def test_raw_explainer():
    """Test the MatchingExplainer directly with sample data."""
    try:
        # Initialize the explainer
        explainer = MatchingExplainer()
        
        # Create sample context
        context = {
            "candidate_profile": {
                "name": "John Smith",
                "skills": ["Python", "Machine Learning", "Data Analysis", "SQL"],
                "experience": "5 years of experience as a Data Scientist at ABC Corp. Led multiple ML projects."
            },
            "job_description": {
                "title": "Senior Data Scientist",
                "company": "XYZ Tech",
                "description": "Looking for an experienced Data Scientist with Python, ML, and Big Data skills.",
                "requirements": "5+ years of experience in data science. Strong Python and ML skills required."
            },
            "match_result": {
                "overall_score": 85.5,
                "factors": {
                    "skills_score": 90.0,
                    "experience_score": 85.0,
                    "education_score": 75.0
                },
                "matched_skills": ["Python", "Machine Learning", "Data Analysis"],
                "missing_skills": ["Big Data", "Spark"]
            }
        }
        
        # Test different detail levels
        for detail_level in ["brief", "standard", "detailed"]:
            logger.info(f"\nTesting {detail_level.upper()} explanation:")
            
            explanation = explainer.generate_explanation(
                context=context,
                detail_level=detail_level
            )
            
            logger.info(f"Main explanation:\n{explanation['explanation']}")
            
            if "factor_explanations" in explanation:
                logger.info("\nFactor explanations:")
                for factor, factor_expl in explanation["factor_explanations"].items():
                    logger.info(f"\n{factor}:\n{factor_expl}")
            
            if "strengths" in explanation:
                logger.info("\nStrengths:")
                for strength in explanation["strengths"]:
                    logger.info(f"- {strength}")
            
            if "improvement_areas" in explanation:
                logger.info("\nImprovement areas:")
                for area in explanation["improvement_areas"]:
                    logger.info(f"- {area}")
        
    except Exception as e:
        logger.error(f"Error testing raw explainer: {e}", exc_info=True)


if __name__ == "__main__":
    # Choose which test to run (comment out the one you don't want to run)
    test_raw_explainer()  # Test the explainer with sample data
    # test_matching_explanations()  # Test with real data from vector store
