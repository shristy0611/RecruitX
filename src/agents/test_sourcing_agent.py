"""
Test script for the SourcingAgent.

This script demonstrates how the SourcingAgent integrates with
the agent orchestration system to discover candidates.
"""
import json
import logging
import time
from typing import Dict, Any, List

from src.agents.sourcing_agent import SourcingAgent, SourcingParams
from src.orchestration.agent_registry import get_agent_registry
from src.orchestration.message_broker import MessageType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Sample job description for testing
SAMPLE_JOB = {
    "title": "Senior Python Developer",
    "company": "TechCorp Inc.",
    "location": "San Francisco, CA",
    "description": "We are seeking an experienced Python Developer to join our growing team. The ideal candidate will have strong experience in web development, API design, and database optimization.",
    "requirements": """
    Requirements:
    - 5+ years of experience in Python development
    - Experience with web frameworks like Django or Flask
    - Strong knowledge of RESTful API design and implementation
    - Experience with SQL and NoSQL databases
    - Understanding of cloud platforms (AWS, GCP, or Azure)
    
    Preferred Qualifications:
    - Experience with containerization (Docker, Kubernetes)
    - Knowledge of front-end technologies (React, Vue.js)
    - Familiarity with CI/CD pipelines
    - Experience with microservices architecture
    
    Responsibilities:
    - Develop and maintain Python-based applications
    - Design and implement RESTful APIs
    - Optimize database queries and structure
    - Participate in code reviews and architectural decisions
    - Mentor junior developers
    """
}

# Sample candidate data for testing
SAMPLE_CANDIDATES = [
    {
        "name": "Alice Smith",
        "email": "alice.smith@example.com",
        "phone": "(123) 456-7890",
        "skills": ["Python", "Django", "Flask", "REST API", "PostgreSQL", "AWS", "Docker", "React"],
        "education": ["M.S. Computer Science, Stanford University"],
        "experience": [
            {
                "title": "Senior Developer",
                "company": "WebTech Inc.",
                "years": 3
            },
            {
                "title": "Python Developer",
                "company": "AppSolutions",
                "years": 4
            }
        ],
        "location": "San Francisco, CA",
        "resume_text": """
        ALICE SMITH
        Senior Python Developer
        alice.smith@example.com | (123) 456-7890
        
        SKILLS
        - Programming: Python, JavaScript, SQL, Java
        - Web Frameworks: Django, Flask, FastAPI
        - Databases: PostgreSQL, MongoDB, Redis
        - Cloud: AWS (EC2, S3, Lambda)
        - DevOps: Docker, Kubernetes, CI/CD
        - Front-end: React, HTML/CSS
        
        EXPERIENCE
        Senior Developer | WebTech Inc.
        2020 - Present (3 years)
        - Led development of scalable APIs serving 1M+ daily requests
        - Optimized database queries, reducing response time by 40%
        - Implemented CI/CD pipelines with GitHub Actions
        
        Python Developer | AppSolutions
        2016 - 2020 (4 years)
        - Developed Django-based web applications
        - Created RESTful APIs for mobile app integration
        - Managed PostgreSQL databases and optimized performance
        
        EDUCATION
        M.S. Computer Science, Stanford University
        """
    },
    {
        "name": "Bob Johnson",
        "email": "bob.johnson@example.com",
        "phone": "(234) 567-8901",
        "skills": ["Python", "Flask", "MongoDB", "AWS", "Microservices", "CI/CD", "DevOps"],
        "education": ["B.S. Computer Engineering, MIT"],
        "experience": [
            {
                "title": "Backend Developer",
                "company": "CloudSystems",
                "years": 5
            }
        ],
        "location": "New York, NY",
        "resume_text": """
        BOB JOHNSON
        Backend Developer
        bob.johnson@example.com | (234) 567-8901
        
        SKILLS
        - Python, Flask, FastAPI
        - MongoDB, DynamoDB
        - AWS (Lambda, ECS, S3)
        - Microservices architecture
        - CI/CD, DevOps practices
        
        EXPERIENCE
        Backend Developer | CloudSystems
        2018 - Present (5 years)
        - Designed and implemented microservices architecture
        - Created Flask-based RESTful APIs
        - Managed MongoDB clusters and optimized performance
        
        EDUCATION
        B.S. Computer Engineering, MIT
        """
    }
]


def test_sourcing_agent():
    """Test the SourcingAgent functionality."""
    logger.info("Testing SourcingAgent...")
    
    # Initialize registry
    registry = get_agent_registry()
    
    try:
        # Create and register sourcing agent
        sourcing_agent = SourcingAgent()
        registry.register_agent(sourcing_agent)
        
        # Start the agent
        registry.start_agent(sourcing_agent.agent_id)
        logger.info("SourcingAgent started")
        
        # Add job to the vector store
        job_id = sourcing_agent.vector_store.add_job_description(
            title=SAMPLE_JOB["title"],
            company=SAMPLE_JOB["company"],
            location=SAMPLE_JOB["location"],
            description=SAMPLE_JOB["description"],
            requirements=SAMPLE_JOB["requirements"]
        )
        logger.info(f"Added job with ID: {job_id}")
        
        # Add sample candidates to the vector store
        candidate_ids = []
        for candidate in SAMPLE_CANDIDATES:
            # Convert education and experience to strings for the API
            education_str = "\n".join([f"- {edu}" for edu in candidate["education"]])
            
            experience_str = ""
            for exp in candidate["experience"]:
                experience_str += f"- {exp['title']} at {exp['company']} ({exp['years']} years)\n"
            
            # Add candidate profile
            candidate_id = sourcing_agent.vector_store.add_candidate_profile(
                name=candidate["name"],
                email=candidate["email"],
                phone=candidate["phone"],
                resume_text=candidate["resume_text"],
                summary="",  # No summary in our test data
                skills=candidate["skills"],
                experience=experience_str,
                education=education_str
            )
            
            if candidate_id:
                candidate_ids.append(candidate_id)
                logger.info(f"Added candidate {candidate['name']} with ID: {candidate_id}")
        
        # Test direct candidate sourcing
        logger.info("Testing direct candidate sourcing...")
        
        # Create sourcing parameters
        params = SourcingParams(
            job_id=job_id,
            keywords=["Python", "Django", "API"],
            min_skills_match=3,
            min_experience_years=2,
            location="San Francisco",
            max_results=5
        )
        
        # Source candidates
        results = sourcing_agent.source_candidates(params)
        
        if results:
            logger.info(f"✅ Found {len(results)} matching candidates")
            for i, candidate in enumerate(results):
                logger.info(f"  {i+1}. {candidate.name} (Score: {candidate.score:.1f})")
                logger.info(f"     Skills: {', '.join(candidate.skills[:5])}")
        else:
            logger.warning("⚠️ No matching candidates found")
        
        # Clean up
        logger.info("Cleaning up...")
        
        # Delete job
        sourcing_agent.vector_store.delete_object("JobDescription", job_id)
        
        # Delete candidates
        for candidate_id in candidate_ids:
            sourcing_agent.vector_store.delete_object("CandidateProfile", candidate_id)
        
        # Stop agent
        registry.stop_agent(sourcing_agent.agent_id)
        registry.unregister_agent(sourcing_agent.agent_id)
        
        logger.info("✅ Test completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Test failed: {e}")
        # Try to clean up
        try:
            # Delete job
            if 'job_id' in locals():
                sourcing_agent.vector_store.delete_object("JobDescription", job_id)
            
            # Delete candidates
            if 'candidate_ids' in locals():
                for candidate_id in candidate_ids:
                    sourcing_agent.vector_store.delete_object("CandidateProfile", candidate_id)
            
            # Stop agent
            registry.stop_agent(sourcing_agent.agent_id)
            registry.unregister_agent(sourcing_agent.agent_id)
        except:
            pass
        return False


if __name__ == "__main__":
    success = test_sourcing_agent()
    exit(0 if success else 1)
