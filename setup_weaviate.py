"""
Weaviate setup script for RecruitPro AI.

This script sets up Weaviate with the necessary schemas and configurations,
including installing required modules and creating class definitions.
"""
import logging
import sys
import time
import json
import requests
from typing import Dict, Any

import weaviate
from weaviate import WeaviateClient
import weaviate.classes.config
import weaviate.connect
from dotenv import load_dotenv

from src.utils.config import WEAVIATE_URL, SCHEMAS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def wait_for_weaviate(url: str, max_retries: int = 10, retry_interval: int = 5) -> bool:
    """
    Wait for Weaviate to be ready.
    
    Args:
        url: Weaviate URL
        max_retries: Maximum number of retries
        retry_interval: Seconds between retries
        
    Returns:
        bool: True if Weaviate is ready, False otherwise
    """
    for i in range(max_retries):
        try:
            response = requests.get(f"{url}/v1/.well-known/ready")
            if response.status_code == 200:
                logger.info(f"Weaviate is ready at {url}")
                return True
        except Exception as e:
            logger.warning(f"Weaviate not ready (attempt {i+1}/{max_retries}): {e}")
        
        logger.info(f"Waiting {retry_interval} seconds before retrying...")
        time.sleep(retry_interval)
    
    logger.error(f"Weaviate not ready after {max_retries} attempts")
    return False


def setup_schema(client: weaviate.WeaviateClient, schema_name: str, schema_config: Dict[str, Any]) -> bool:
    """
    Set up a schema in Weaviate.
    
    Args:
        client: Weaviate client
        schema_name: Name of the schema to create
        schema_config: Schema configuration
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if schema exists
        collection_names = [c.name for c in client.collections.list_all()]
        
        if schema_name in collection_names:
            logger.info(f"Schema {schema_name} already exists")
            return True
        
        # Create schema
        logger.info(f"Creating schema for {schema_name}")
        
        # Configure the collection
        collection = client.collections.create(
            name=schema_name,
            vectorizer_config=weaviate.classes.config.Configure.NamedVectorizer(
                vectorizer=schema_config.get("vectorizer", "text2vec-transformers")
            ),
        )
        
        # Add properties
        for prop_name, prop_config in schema_config.get("properties", {}).items():
            data_type = prop_config.get("dataType", ["text"])[0]
            
            # Map Weaviate v3 data types to v4
            if data_type == "text":
                collection.properties.create(
                    name=prop_name,
                    data_type=weaviate.classes.config.DataType.TEXT
                )
            elif data_type == "text[]":
                collection.properties.create(
                    name=prop_name,
                    data_type=weaviate.classes.config.DataType.TEXT_ARRAY
                )
            elif data_type == "int":
                collection.properties.create(
                    name=prop_name,
                    data_type=weaviate.classes.config.DataType.INT
                )
            elif data_type == "number":
                collection.properties.create(
                    name=prop_name,
                    data_type=weaviate.classes.config.DataType.NUMBER
                )
            elif data_type == "boolean":
                collection.properties.create(
                    name=prop_name,
                    data_type=weaviate.classes.config.DataType.BOOLEAN
                )
            elif data_type == "date":
                collection.properties.create(
                    name=prop_name,
                    data_type=weaviate.classes.config.DataType.DATE
                )
            elif data_type == "vector":
                # Skip vector properties as they're handled differently in v4
                pass
                
        logger.info(f"Created schema for {schema_name}")
        return True
    except Exception as e:
        logger.error(f"Error creating schema for {schema_name}: {e}")
        return False


def setup_weaviate():
    """Set up Weaviate with required schemas."""
    logger.info(f"Setting up Weaviate at {WEAVIATE_URL}")
    
    # Wait for Weaviate to be ready
    if not wait_for_weaviate(WEAVIATE_URL):
        logger.error("Weaviate is not available. Please ensure it's running.")
        return False
    
    # Connect to Weaviate
    try:
        # Create connection params
        connection_params = weaviate.connect.ConnectionParams.from_url(
            url=WEAVIATE_URL
        )
        
        # Set additional headers
        connection_params.headers = {
            "X-RecruitPro-Client": "Setup/1.0.0"
        }
        
        # Create client
        client = weaviate.WeaviateClient(connection_params=connection_params)
        logger.info("Connected to Weaviate")
    except Exception as e:
        logger.error(f"Failed to connect to Weaviate: {e}")
        return False
    
    # Set up schemas
    success = True
    for schema_name, schema_config in SCHEMAS.items():
        if not setup_schema(client, schema_name, schema_config):
            success = False
    
    return success


def add_test_data(client: weaviate.WeaviateClient):
    """
    Add test data to Weaviate for demonstration purposes.
    
    Args:
        client: Weaviate client
    """
    try:
        # Get collections
        job_collection = client.collections.get("JobDescription")
        candidate_collection = client.collections.get("CandidateProfile")
        
        # Example job description
        job_data = {
            "title": "Senior Python Developer",
            "description": "We are seeking an experienced Python developer to join our team. You will be responsible for developing and maintaining high-quality applications using Python and related technologies.",
            "requirements": "5+ years of Python experience, familiarity with web frameworks such as Django or Flask, experience with SQL and NoSQL databases, knowledge of REST APIs, and excellent problem-solving skills.",
            "company": "TechInnovate Labs",
            "location": "San Francisco, CA (Remote)",
            "salary_range": "$120,000 - $160,000",
            "job_type": "Full-time",
            "created_at": "2025-05-11T00:00:00Z",
            "updated_at": "2025-05-11T00:00:00Z",
        }
        
        # Add job description
        job_result = job_collection.data.insert(job_data)
        job_id = job_result.uuid
        logger.info(f"Added test job description with ID: {job_id}")
        
        # Example candidate profile
        candidate_data = {
            "name": "Alex Johnson",
            "email": "alex.johnson@example.com",
            "phone": "(555) 123-4567",
            "summary": "Experienced Python developer with 7 years of experience building web applications and APIs using Django and Flask.",
            "skills": ["Python", "Django", "Flask", "PostgreSQL", "MongoDB", "Docker", "AWS"],
            "experience": "Senior Developer at CodeCorp (2020-Present), Python Developer at TechSolutions (2018-2020)",
            "education": "Bachelor of Science in Computer Science, Stanford University",
            "resume_text": """
                Alex Johnson
                (555) 123-4567 | alex.johnson@example.com | github.com/alexj
                
                SUMMARY
                Experienced Python developer with 7 years of experience building web applications and APIs using Django and Flask.
                Passionate about clean code, testing, and DevOps practices.
                
                SKILLS
                Programming: Python, JavaScript, SQL, Bash
                Frameworks: Django, Flask, FastAPI, React
                Databases: PostgreSQL, MongoDB, Redis
                Tools: Docker, Kubernetes, AWS, Git, CI/CD
                
                EXPERIENCE
                
                Senior Developer, CodeCorp (2020-Present)
                - Developed and maintained multiple Python microservices handling 1M+ daily requests
                - Implemented CI/CD pipelines reducing deployment time by 70%
                - Optimized database queries resulting in 40% performance improvement
                - Mentored junior developers and conducted code reviews
                
                Python Developer, TechSolutions (2018-2020)
                - Built RESTful APIs using Django REST Framework for mobile applications
                - Integrated payment processing systems including Stripe and PayPal
                - Implemented automated testing achieving 90% code coverage
                
                EDUCATION
                
                Bachelor of Science in Computer Science
                Stanford University (2014-2018)
            """,
            "created_at": "2025-05-11T00:00:00Z",
            "updated_at": "2025-05-11T00:00:00Z",
        }
        
        # Add candidate profile
        candidate_result = candidate_collection.data.insert(candidate_data)
        candidate_id = candidate_result.uuid
        logger.info(f"Added test candidate profile with ID: {candidate_id}")
        
        return True
    except Exception as e:
        logger.error(f"Error adding test data: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting Weaviate setup")
    
    # Setup Weaviate
    if not setup_weaviate():
        logger.error("Failed to set up Weaviate")
        sys.exit(1)
    
    # Connect to Weaviate for test data
    try:
        client = weaviate.Client(
            url=WEAVIATE_URL,
            additional_headers={
                "X-RecruitPro-Client": "Setup/1.0.0"
            }
        )
        
        # Ask if user wants to add test data
        add_test = input("Do you want to add test data? (y/n): ").lower().strip() == 'y'
        if add_test:
            if add_test_data(client):
                logger.info("Test data added successfully")
            else:
                logger.error("Failed to add test data")
    except Exception as e:
        logger.error(f"Error connecting to Weaviate for test data: {e}")
    
    logger.info("Setup complete")
