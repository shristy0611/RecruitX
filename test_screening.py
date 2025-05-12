"""
Test script for RecruitPro AI resume screening capabilities.

This script demonstrates core functionality by:
1. Creating a job description in the Knowledge Base
2. Uploading and analyzing a resume against the job
3. Displaying the matching results with explanations
"""
import argparse
import json
import logging
import os
import sys
import requests
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8000")
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
API_URL = f"http://{API_HOST}:{API_PORT}{API_PREFIX}"


def create_job_description() -> str:
    """
    Create a sample job description in the Knowledge Base.
    
    Returns:
        str: Job ID if successful, empty string otherwise
    """
    job_data = {
        "title": "Senior Machine Learning Engineer",
        "description": """
        We are looking for a Senior Machine Learning Engineer to join our AI team. 
        You will be responsible for developing and deploying machine learning models,
        working on cutting-edge AI applications, and collaborating with cross-functional teams.
        The ideal candidate has experience with deep learning, NLP, and productionizing ML models.
        """,
        "requirements": """
        - 5+ years of experience in machine learning and data science
        - Strong programming skills in Python and PyTorch or TensorFlow
        - Experience with NLP, transformers, and large language models
        - Familiarity with MLOps and model deployment pipelines
        - Experience with cloud platforms (AWS, GCP, or Azure)
        - Strong communication and collaboration skills
        - MS or PhD in Computer Science, Machine Learning, or related field
        """,
        "company": "AI Innovations Inc.",
        "location": "San Francisco, CA (Remote option available)",
        "salary_range": "$150,000 - $200,000",
        "job_type": "Full-time"
    }
    
    try:
        logger.info("Creating job description")
        response = requests.post(f"{API_URL}/jobs", json=job_data)
        response.raise_for_status()
        job_id = response.json().get("id")
        logger.info(f"Job created with ID: {job_id}")
        return job_id
    except Exception as e:
        logger.error(f"Failed to create job description: {e}")
        return ""


def analyze_resume(job_id: str, resume_path: Path) -> Dict[str, Any]:
    """
    Analyze a resume against a job description.
    
    Args:
        job_id: Job ID to match against
        resume_path: Path to resume file
        
    Returns:
        Dict[str, Any]: Analysis results
    """
    try:
        logger.info(f"Analyzing resume against job ID: {job_id}")
        
        # Prepare multipart form data
        files = {"resume_file": open(resume_path, "rb")}
        data = {"job_id": job_id}
        
        # Send request
        response = requests.post(f"{API_URL}/candidates/analyze", 
                                files=files, 
                                data=data)
        response.raise_for_status()
        
        # Get results
        results = response.json()
        logger.info("Resume analysis complete")
        return results
    except Exception as e:
        logger.error(f"Failed to analyze resume: {e}")
        return {"error": str(e)}


def display_results(results: Dict[str, Any]) -> None:
    """
    Display resume analysis results in a user-friendly format.
    
    Args:
        results: Analysis results
    """
    if "error" in results:
        logger.error(f"Error in results: {results['error']}")
        return
    
    print("\n" + "="*80)
    print("RESUME ANALYSIS RESULTS")
    print("="*80)
    
    # Resume data
    resume_data = results.get("resume_data", {})
    candidate_name = resume_data.get("name", "Unknown Candidate")
    print(f"\nCandidate: {candidate_name}")
    
    # Display contact info
    contact_info = resume_data.get("contact_info", {})
    if contact_info:
        print(f"Email: {contact_info.get('email', 'N/A')}")
        print(f"Phone: {contact_info.get('phone', 'N/A')}")
    
    # Display skills
    skills = resume_data.get("skills", [])
    if skills:
        print("\nSkills:")
        for skill in skills:
            print(f"  - {skill}")
    
    # Display scores
    score_data = results.get("score_data", {})
    if score_data:
        print("\nMatch Scores:")
        print(f"  Overall Match: {score_data.get('overall_score', 0):.1f}/100")
        print(f"  Skills Match: {score_data.get('skills_score', 0):.1f}/100")
        print(f"  Experience Match: {score_data.get('experience_score', 0):.1f}/100")
        print(f"  Education Match: {score_data.get('education_score', 0):.1f}/100")
        print(f"  Final Score: {score_data.get('final_score', 0):.1f}/100")
    
    # Display explanation
    explanation = score_data.get("explanation", "")
    if explanation:
        print("\nAnalysis:")
        print(f"{explanation}")
    
    print("\n" + "="*80)


def main():
    """Main function to demonstrate resume screening."""
    parser = argparse.ArgumentParser(description="Test resume screening")
    parser.add_argument("--resume", type=str, required=True,
                        help="Path to resume file")
    parser.add_argument("--job-id", type=str,
                        help="Existing job ID (if not provided, a new job will be created)")
    args = parser.parse_args()
    
    # Validate resume path
    resume_path = Path(args.resume)
    if not resume_path.exists():
        logger.error(f"Resume file not found: {resume_path}")
        sys.exit(1)
    
    # Get or create job ID
    job_id = args.job_id
    if not job_id:
        job_id = create_job_description()
        if not job_id:
            logger.error("Failed to create job description")
            sys.exit(1)
    
    # Analyze resume
    results = analyze_resume(job_id, resume_path)
    
    # Display results
    display_results(results)


if __name__ == "__main__":
    main()
