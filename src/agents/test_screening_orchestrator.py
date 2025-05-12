"""
Test script for the ScreeningOrchestrator agent.

This script demonstrates how the ScreeningOrchestrator agent integrates with
the agent orchestration system to manage resume screening.
"""
import json
import logging
import time
from typing import Dict, Any

from src.agents.screening_orchestrator import ScreeningOrchestrator
from src.orchestration.agent_registry import get_agent_registry
from src.orchestration.message_broker import MessageType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Sample resume for testing
SAMPLE_RESUME = """
JOHN SMITH
Data Scientist & Machine Learning Engineer
john.smith@email.com | (123) 456-7890 | linkedin.com/in/johnsmith

SUMMARY
Experienced Data Scientist with 5+ years of expertise in machine learning, deep learning, and statistical analysis. Proficient in Python, TensorFlow, PyTorch, and SQL. Strong background in developing and deploying ML models at scale.

SKILLS
- Programming: Python, R, SQL, Java
- ML/DL: TensorFlow, PyTorch, Keras, scikit-learn
- Data Processing: Pandas, NumPy, PySpark
- Cloud: AWS (SageMaker, EC2, S3), GCP, Azure
- DevOps: Docker, Kubernetes, CI/CD
- Visualization: Tableau, PowerBI, matplotlib, seaborn

EDUCATION
Stanford University
M.S. in Computer Science, Specialization in Machine Learning
2016 - 2018

University of California, Berkeley
B.S. in Mathematics and Computer Science
2012 - 2016

WORK EXPERIENCE
Senior Data Scientist | TechCorp Inc.
April 2020 - Present
- Led the development of a recommendation system that increased user engagement by 35%
- Implemented NLP models for sentiment analysis with 92% accuracy
- Managed a team of 3 junior data scientists on various ML projects
- Optimized data pipelines, reducing processing time by 40%

Machine Learning Engineer | AI Solutions
January 2018 - March 2020
- Developed computer vision models for object detection with 88% mAP
- Created and deployed ML models for fraud detection, saving the company $2M annually
- Collaborated with product teams to integrate ML features into the main product
- Implemented A/B testing framework for model performance evaluation

PROJECTS
Autonomous Drone Navigation System
- Developed reinforcement learning algorithms for drone path optimization
- Achieved 95% navigation accuracy in complex environments

Healthcare Prediction System
- Built a system to predict patient readmission risk using electronic health records
- Achieved 87% accuracy, improving on previous models by 15%

CERTIFICATIONS
- AWS Certified Machine Learning Specialist
- TensorFlow Developer Certificate
- Deep Learning Specialization, Coursera
"""

# Sample job description for testing
SAMPLE_JOB = {
    "title": "Senior Machine Learning Engineer",
    "company": "AI Innovations Inc.",
    "location": "San Francisco, CA",
    "description": "We are seeking an experienced Machine Learning Engineer to join our growing team. The ideal candidate will have strong experience in deep learning, neural networks, and deploying models to production.",
    "requirements": [
        "5+ years of experience in machine learning",
        "Proficiency in Python, TensorFlow, and PyTorch",
        "Experience with NLP and computer vision",
        "Strong understanding of deep learning architectures",
        "Experience with cloud platforms (AWS, GCP, or Azure)"
    ],
    "preferred": [
        "PhD in Computer Science, Machine Learning, or related field",
        "Experience with reinforcement learning",
        "Publications in top-tier ML conferences",
        "Experience with distributed ML systems"
    ],
    "responsibilities": [
        "Develop and optimize machine learning models",
        "Deploy models to production environments",
        "Collaborate with data scientists and engineers",
        "Research and implement state-of-the-art ML techniques",
        "Mentor junior ML engineers"
    ]
}


def test_screening_orchestrator():
    """Test the ScreeningOrchestrator agent functionality."""
    logger.info("Testing ScreeningOrchestrator agent...")
    
    # Initialize registry
    registry = get_agent_registry()
    
    try:
        # Create and register orchestrator agent
        orchestrator = ScreeningOrchestrator()
        registry.register_agent(orchestrator)
        
        # Start the agent
        registry.start_agent(orchestrator.agent_id)
        logger.info("ScreeningOrchestrator started")
        
        # Add a job to the vector store
        # Combine requirements, preferred and responsibilities for the requirements parameter
        all_requirements = (
            "\nRequirements:\n- " + "\n- ".join(SAMPLE_JOB["requirements"]) +
            "\n\nPreferred Qualifications:\n- " + "\n- ".join(SAMPLE_JOB["preferred"]) +
            "\n\nResponsibilities:\n- " + "\n- ".join(SAMPLE_JOB["responsibilities"])
        )
        
        job_id = orchestrator.vector_store.add_job_description(
            title=SAMPLE_JOB["title"],
            company=SAMPLE_JOB["company"],
            location=SAMPLE_JOB["location"],
            description=SAMPLE_JOB["description"],
            requirements=all_requirements
        )
        logger.info(f"Added job with ID: {job_id}")
        
        # Test synchronous resume screening
        logger.info("Testing synchronous resume screening...")
        result = orchestrator.screen_resume(SAMPLE_RESUME, job_id)
        
        if "error" in result and result["error"]:
            logger.error(f"Error in screening: {result['error']}")
        else:
            screening_id = result.get("screening_id")
            logger.info(f"✅ Resume screened successfully with ID: {screening_id}")
            logger.info(f"Overall score: {result['score_data'].get('overall_score', 0)}")
            
            # Print top skills matched
            skills_matched = result["score_data"].get("skills_matched", [])
            if skills_matched:
                logger.info("Top skills matched:")
                for skill in skills_matched[:5]:
                    logger.info(f"- {skill}")
        
        # Clean up
        logger.info("Cleaning up...")
        orchestrator.vector_store.delete_object("JobDescription", job_id)
        registry.stop_agent(orchestrator.agent_id)
        registry.unregister_agent(orchestrator.agent_id)
        logger.info("✅ Test completed successfully")
        
        return True
    
    except Exception as e:
        logger.error(f"Test failed: {e}")
        # Try to clean up
        try:
            registry.stop_agent(orchestrator.agent_id)
            registry.unregister_agent(orchestrator.agent_id)
        except:
            pass
        return False


if __name__ == "__main__":
    success = test_screening_orchestrator()
    exit(0 if success else 1)
