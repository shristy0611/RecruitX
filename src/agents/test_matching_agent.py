"""
Test script for the MatchingAgent.

This script demonstrates how the MatchingAgent provides advanced matching
between candidates and jobs with explainable results.
"""
import json
import logging
import time
from typing import Dict, Any, List

from src.agents.matching_agent import MatchingAgent, MatchingParams
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
    "title": "Senior Data Scientist",
    "company": "AI Research Labs",
    "location": "San Francisco, CA",
    "description": "We are seeking a talented Senior Data Scientist to join our growing team. The ideal candidate will have strong experience in machine learning, statistical analysis, and deploying models to production.",
    "requirements": """
    Requirements:
    - 5+ years of experience in data science or related field
    - Strong programming skills in Python, R, or similar languages
    - Experience with machine learning frameworks (TensorFlow, PyTorch, scikit-learn)
    - Proficiency in SQL and data manipulation
    - Experience with cloud platforms (AWS, GCP, or Azure)
    - Excellent communication skills
    
    Preferred Qualifications:
    - PhD or MS in Computer Science, Statistics, or related field
    - Experience with deep learning techniques
    - Experience with natural language processing
    - Knowledge of big data technologies (Spark, Hadoop)
    - Publications in top-tier conferences or journals
    
    Responsibilities:
    - Develop and implement machine learning models
    - Analyze large datasets to extract insights
    - Create data visualizations and reports
    - Collaborate with cross-functional teams
    - Present findings to technical and non-technical stakeholders
    """
}

# Sample candidate data for testing
SAMPLE_CANDIDATES = [
    {
        "name": "Dr. Alex Chen",
        "email": "alex.chen@example.com",
        "phone": "(123) 456-7890",
        "skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Deep Learning", "NLP", "SQL", "AWS", "Data Visualization"],
        "education": ["PhD in Computer Science, Stanford University", "MS in Statistics, UCLA"],
        "experience": """
        - Lead Data Scientist at TechCorp (4 years)
          Developed deep learning models for recommendation systems
          Led a team of 5 data scientists on various ML projects
          Implemented NLP models with 90% accuracy
        
        - Machine Learning Engineer at AI Solutions (3 years)
          Created predictive models for financial forecasting
          Worked with big data technologies (Spark, Hadoop)
          Optimized SQL queries for improved performance
        """,
        "location": "San Francisco, CA",
        "resume_text": """
        DR. ALEX CHEN
        Senior Data Scientist
        alex.chen@example.com | (123) 456-7890
        
        SKILLS
        - Programming: Python, R, SQL, Java
        - ML/DL: TensorFlow, PyTorch, scikit-learn, deep learning
        - Data Processing: Pandas, NumPy, PySpark, Hadoop
        - Cloud: AWS (SageMaker, EC2, S3), GCP
        - NLP: BERT, Word2Vec, Transformers
        
        EXPERIENCE
        Lead Data Scientist | TechCorp
        2018 - Present (4 years)
        - Developed deep learning models for recommendation systems
        - Led a team of 5 data scientists on various ML projects
        - Implemented NLP models with 90% accuracy
        - Created data visualizations for executive presentations
        
        Machine Learning Engineer | AI Solutions
        2015 - 2018 (3 years)
        - Created predictive models for financial forecasting
        - Worked with big data technologies (Spark, Hadoop)
        - Optimized SQL queries for improved performance
        - Deployed models to production environments
        
        EDUCATION
        PhD in Computer Science, Stanford University
        Specialization in Machine Learning
        
        MS in Statistics, UCLA
        """
    },
    {
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "phone": "(234) 567-8901",
        "skills": ["Python", "scikit-learn", "SQL", "Data Analysis", "Visualization", "R", "Statistics"],
        "education": ["MS in Data Science, UC Berkeley"],
        "experience": """
        - Data Scientist at DataCorp (3 years)
          Analyzed customer data to identify trends
          Built machine learning models for customer segmentation
          Created dashboards using Tableau
        
        - Data Analyst at Info Systems (2 years)
          Performed statistical analysis on marketing data
          Wrote SQL queries to extract insights from databases
          Generated weekly reports for management
        """,
        "location": "Oakland, CA",
        "resume_text": """
        JANE SMITH
        Data Scientist
        jane.smith@example.com | (234) 567-8901
        
        SKILLS
        - Programming: Python, R, SQL
        - Data Science: scikit-learn, statistical analysis
        - Visualization: Tableau, matplotlib, seaborn
        - Databases: PostgreSQL, MySQL
        
        EXPERIENCE
        Data Scientist | DataCorp
        2019 - Present (3 years)
        - Analyzed customer data to identify trends
        - Built machine learning models for customer segmentation
        - Created dashboards using Tableau
        - Collaborated with marketing team on A/B testing
        
        Data Analyst | Info Systems
        2017 - 2019 (2 years)
        - Performed statistical analysis on marketing data
        - Wrote SQL queries to extract insights from databases
        - Generated weekly reports for management
        
        EDUCATION
        MS in Data Science, UC Berkeley
        """
    },
    {
        "name": "Michael Johnson",
        "email": "michael.johnson@example.com",
        "phone": "(345) 678-9012",
        "skills": ["Java", "C++", "Software Engineering", "Agile", "Git", "Data Structures"],
        "education": ["BS in Computer Science, MIT"],
        "experience": """
        - Senior Software Engineer at TechSoft (5 years)
          Developed backend services using Java
          Implemented CI/CD pipelines
          Mentored junior developers
        
        - Software Developer at CodeCorp (3 years)
          Built applications using C++ and Python
          Worked in an Agile environment
          Participated in code reviews
        """,
        "location": "San Jose, CA",
        "resume_text": """
        MICHAEL JOHNSON
        Senior Software Engineer
        michael.johnson@example.com | (345) 678-9012
        
        SKILLS
        - Programming: Java, C++, Python
        - Software Engineering: Design Patterns, Algorithms
        - Tools: Git, Jenkins, JIRA
        - Methodologies: Agile, Scrum
        
        EXPERIENCE
        Senior Software Engineer | TechSoft
        2016 - Present (5 years)
        - Developed backend services using Java
        - Implemented CI/CD pipelines
        - Mentored junior developers
        - Participated in architecture design sessions
        
        Software Developer | CodeCorp
        2013 - 2016 (3 years)
        - Built applications using C++ and Python
        - Worked in an Agile environment
        - Participated in code reviews
        
        EDUCATION
        BS in Computer Science, MIT
        """
    }
]


def test_matching_agent():
    """Test the MatchingAgent functionality."""
    logger.info("Testing MatchingAgent...")
    
    # Initialize registry
    registry = get_agent_registry()
    
    try:
        # Create and register matching agent
        matching_agent = MatchingAgent()
        registry.register_agent(matching_agent)
        
        # Start the agent
        registry.start_agent(matching_agent.agent_id)
        logger.info("MatchingAgent started")
        
        # Add job to the vector store
        job_id = matching_agent.vector_store.add_job_description(
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
            # Convert education to a string
            education_str = "\n".join([f"- {edu}" for edu in candidate["education"]])
            
            # Add candidate profile
            candidate_id = matching_agent.vector_store.add_candidate_profile(
                name=candidate["name"],
                email=candidate["email"],
                phone=candidate["phone"],
                resume_text=candidate["resume_text"],
                summary="",  # No summary in our test data
                skills=candidate["skills"],
                experience=candidate["experience"],
                education=education_str
            )
            
            if candidate_id:
                candidate_ids.append(candidate_id)
                logger.info(f"Added candidate {candidate['name']} with ID: {candidate_id}")
        
        # Test direct matching
        logger.info("Testing direct candidate matching...")
        
        # Create matching parameters
        params = MatchingParams(
            job_id=job_id,
            candidate_ids=candidate_ids,
            min_score=30.0,  # Lower threshold for testing
            weights={
                "skills": 0.5,
                "experience": 0.3,
                "education": 0.2
            },
            require_explanation=True,
            max_results=10
        )
        
        # Match candidates
        results = matching_agent.match_candidates(
            job_id=job_id,
            candidate_ids=candidate_ids,
            min_score=params.min_score,
            weights=params.weights,
            require_explanation=params.require_explanation
        )
        
        if results:
            logger.info(f"✅ Matched {len(results)} candidates to job")
            for i, result in enumerate(results):
                logger.info(f"  {i+1}. {SAMPLE_CANDIDATES[i]['name']} (Score: {result.overall_score:.1f})")
                logger.info(f"     Skills: {result.skill_match_score:.1f}%, Experience: {result.experience_match_score:.1f}%, Education: {result.education_match_score:.1f}%")
                logger.info(f"     Matched Skills: {', '.join(result.skills_matched[:3])}...")
                
                # Log a short excerpt of the explanation
                explanation_preview = result.explanation.split("\n")[0]
                logger.info(f"     Explanation: {explanation_preview}...")
        else:
            logger.warning("⚠️ No matching candidates found")
        
        # Clean up
        logger.info("Cleaning up...")
        
        # Delete job
        matching_agent.vector_store.delete_object("JobDescription", job_id)
        
        # Delete candidates
        for candidate_id in candidate_ids:
            matching_agent.vector_store.delete_object("CandidateProfile", candidate_id)
        
        # Stop agent
        registry.stop_agent(matching_agent.agent_id)
        registry.unregister_agent(matching_agent.agent_id)
        
        logger.info("✅ Test completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Test failed: {e}")
        # Try to clean up
        try:
            # Delete job
            if 'job_id' in locals():
                matching_agent.vector_store.delete_object("JobDescription", job_id)
            
            # Delete candidates
            if 'candidate_ids' in locals():
                for candidate_id in candidate_ids:
                    matching_agent.vector_store.delete_object("CandidateProfile", candidate_id)
            
            # Stop agent
            registry.stop_agent(matching_agent.agent_id)
            registry.unregister_agent(matching_agent.agent_id)
        except:
            pass
        return False


if __name__ == "__main__":
    success = test_matching_agent()
    exit(0 if success else 1)
