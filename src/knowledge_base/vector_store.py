"""
Vector database client for RecruitPro AI Knowledge Base.
Implements a simplified wrapper around Weaviate with HTTP API calls,
preserving our privacy-first architecture.

This implementation avoids dependency issues with the Weaviate client library
by using direct HTTP requests to the Weaviate API.
"""
import json
import logging
import time
import uuid
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from sentence_transformers import SentenceTransformer

from src.utils.config import (
    WEAVIATE_URL,
    EMBEDDING_MODEL, 
    EMBEDDING_DIMENSION,
    get_schema
)

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Vector database client for the RecruitPro AI Knowledge Base.
    Uses direct HTTP requests to Weaviate for privacy-first architecture.
    """

    def __init__(self, url: str = WEAVIATE_URL):
        """
        Initialize the vector store client.
        
        Args:
            url: Weaviate HTTP URL
        """
        self.url = url.rstrip('/')
        self.headers = {
            'Content-Type': 'application/json',
            'X-RecruitPro-Client': 'VectorStore/1.0.0'
        }
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info(f"Initialized VectorStore with {url}")
        self._ensure_schemas()

    def _ensure_schemas(self) -> None:
        """
        Ensure all required schemas exist in the vector database.
        Creates schemas if they don't exist.
        """
        from src.utils.config import SCHEMAS
        
        # Check if Weaviate is ready
        try:
            response = requests.get(f"{self.url}/v1/.well-known/ready")
            if response.status_code != 200:
                logger.error(f"Weaviate not ready: {response.status_code} {response.text}")
                raise Exception(f"Weaviate not ready: {response.status_code}")
        except Exception as e:
            logger.error(f"Error connecting to Weaviate: {e}")
            raise
        
        # Get existing schemas
        try:
            response = requests.get(f"{self.url}/v1/schema")
            if response.status_code != 200:
                logger.error(f"Failed to get schemas: {response.status_code} {response.text}")
                raise Exception(f"Failed to get schemas: {response.status_code}")
            
            existing_classes = [c['class'] for c in response.json().get('classes', [])]
            
            # Create missing schemas
            for class_name, schema_config in SCHEMAS.items():
                if class_name not in existing_classes:
                    logger.info(f"Creating schema for {class_name}")
                    
                    # Convert the properties to Weaviate format
                    properties_list = []
                    for prop_name, prop_config in schema_config.get("properties", {}).items():
                        prop_obj = {
                            "name": prop_name,
                            "dataType": prop_config["dataType"]
                        }
                        if "description" in prop_config:
                            prop_obj["description"] = prop_config["description"]
                        if "tokenization" in prop_config:
                            prop_obj["tokenization"] = prop_config["tokenization"]
                        if "vectorize" in prop_config:
                            prop_obj["vectorize"] = prop_config["vectorize"]
                        properties_list.append(prop_obj)
                    
                    class_obj = {
                        "class": class_name,
                        "vectorizer": schema_config.get("vectorizer", "text2vec-transformers"),
                        "properties": properties_list
                    }
                    
                    create_response = requests.post(
                        f"{self.url}/v1/schema", 
                        headers=self.headers,
                        json=class_obj
                    )
                    if create_response.status_code != 200:
                        logger.error(f"Failed to create schema for {class_name}: {create_response.status_code} {create_response.text}")
                        raise Exception(f"Failed to create schema for {class_name}: {create_response.status_code}")
                    logger.info(f"Created schema for {class_name}")
                else:
                    logger.info(f"Schema {class_name} already exists")
        except Exception as e:
            logger.error(f"Error managing schemas: {e}")
            raise

    def embed_text(self, text: str) -> List[float]:
        """
        Generate vector embeddings for text using local embedding model.
        This ensures privacy by keeping all text processing on-premise.
        
        Args:
            text: Text to embed
            
        Returns:
            Vector embedding as list of floats
        """
        return self.embedding_model.encode(text).tolist()

    def add_job_description(
        self, 
        title: str, 
        description: str, 
        requirements: str,
        company: str,
        location: str = "",
        salary_range: str = "",
        job_type: str = "Full-time",
    ) -> str:
        """
        Add a job description to the knowledge base.
        
        Args:
            title: Job title
            description: Job description text
            requirements: Job requirements
            company: Company name
            location: Job location
            salary_range: Salary range as text
            job_type: Job type (Full-time, Part-time, etc.)
            
        Returns:
            UUID of the created object
        """
        # Format dates according to RFC3339 format for Weaviate
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        job_data = {
            "title": title,
            "description": description,
            "requirements": requirements,
            "company": company,
            "location": location,
            "salary_range": salary_range,
            "job_type": job_type,
            "created_at": now,
            "updated_at": now,
        }
        
        # Combine relevant fields for vector representation
        vector_text = f"{title}. {description}. {requirements}"
        vector = self.embed_text(vector_text)
        
        try:
            # Generate a UUID for the object
            object_uuid = str(uuid.uuid4())
            
            # Prepare the request data
            request_data = {
                "id": object_uuid,
                "class": "JobDescription",
                "properties": job_data,
                "vector": vector
            }
            
            # Create the object in Weaviate
            response = requests.post(
                f"{self.url}/v1/objects",
                headers=self.headers,
                json=request_data
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"Error adding job description: {response.status_code} {response.text}")
                raise Exception(f"Failed to add job description: {response.status_code}")
                
            logger.info(f"Added job description: {title} with UUID: {object_uuid}")
            return object_uuid
        except Exception as e:
            logger.error(f"Error adding job description: {e}")
            raise

    def add_candidate_profile(
        self,
        name: str,
        email: str,
        resume_text: str,
        phone: str = "",
        summary: str = "",
        skills: List[str] = None,
        experience: str = "",
        education: str = "",
    ) -> str:
        """
        Add a candidate profile to the knowledge base.
        
        Args:
            name: Candidate name
            email: Candidate email
            resume_text: Full resume text
            phone: Candidate phone number
            summary: Professional summary
            skills: List of skills
            experience: Work experience text
            education: Education background text
            
        Returns:
            UUID of the created object
        """
        if skills is None:
            skills = []
            
        profile_data = {
            "name": name,
            "email": email,
            "phone": phone,
            "summary": summary,
            "skills": skills,
            "experience": experience,
            "education": education,
            "resume_text": resume_text,
            "created_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "updated_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        
        # Generate vector embedding from resume text
        vector = self.embed_text(resume_text)
        profile_data["resume_vector"] = vector
        
        try:
            # Generate a UUID for the object
            object_uuid = str(uuid.uuid4())
            
            # Prepare the request data
            request_data = {
                "id": object_uuid,
                "class": "CandidateProfile",
                "properties": profile_data,
                "vector": vector
            }
            
            # Create the object in Weaviate
            response = requests.post(
                f"{self.url}/v1/objects",
                headers=self.headers,
                json=request_data
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"Error adding candidate profile: {response.status_code} {response.text}")
                raise Exception(f"Failed to add candidate profile: {response.status_code}")
            
            logger.info(f"Added candidate profile: {name} with UUID: {object_uuid}")
            return object_uuid
        except Exception as e:
            logger.error(f"Error adding candidate profile: {e}")
            raise

    def add_company_data(
        self,
        name: str,
        description: str,
        culture: str = "",
        benefits: str = "",
        industry: str = "",
    ) -> str:
        """
        Add company data to the knowledge base.
        
        Args:
            name: Company name
            description: Company description
            culture: Company culture description
            benefits: Company benefits
            industry: Company industry
            
        Returns:
            UUID of the created object
        """
        company_data = {
            "name": name,
            "description": description,
            "culture": culture,
            "benefits": benefits,
            "industry": industry,
            "created_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "updated_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        
        # Combine fields for vector representation
        vector_text = f"{name}. {description}. {culture}. {industry}"
        vector = self.embed_text(vector_text)
        
        try:
            uuid = self.client.data_object.create(
                data_object=company_data,
                class_name="CompanyData",
                vector=vector
            )
            logger.info(f"Added company data: {name} with UUID: {uuid}")
            return uuid
        except Exception as e:
            logger.error(f"Error adding company data: {e}")
            raise

    def get_by_id(self, class_name: str, uuid: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an object by its UUID.
        
        Args:
            class_name: Class name in the vector database
            uuid: UUID of the object
            
        Returns:
            Object data or None if not found
        """
        try:
            # Request the object directly via REST API
            response = requests.get(
                f"{self.url}/v1/objects/{class_name}/{uuid}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.warning(f"Object {class_name}/{uuid} not found: {response.status_code}")
                return None
                
            # Parse and format the response
            result = response.json()
            
            # Format the response to return properties at the top level
            # along with metadata in the _additional field as per typical Weaviate format
            properties = result.get("properties", {})
            
            # Add id and class as metadata
            properties["_additional"] = {
                "id": result.get("id"),
                "class": result.get("class"),
                "vector": result.get("vector", [])
            }
            
            return properties
            
        except Exception as e:
            logger.error(f"Error retrieving object {class_name}/{uuid}: {e}")
            return None

    def update_object(
        self, 
        class_name: str, 
        uuid: str, 
        properties: Dict[str, Any]
    ) -> bool:
        """
        Update an existing object.
        
        Args:
            class_name: Class name in the vector database
            uuid: UUID of the object
            properties: Dictionary of properties to update
            
        Returns:
            True if successful, False otherwise
        """
        # Format date according to RFC3339 format for Weaviate
        properties["updated_at"] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        try:
            # Update the object directly via REST API
            response = requests.patch(
                f"{self.url}/v1/objects/{class_name}/{uuid}",
                headers=self.headers,
                json={"properties": properties}
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to update object {class_name}/{uuid}: {response.status_code} {response.text}")
                return False
                
            logger.info(f"Updated {class_name} object with UUID: {uuid}")
            return True
        except Exception as e:
            logger.error(f"Error updating {class_name} object {uuid}: {e}")
            return False

    def delete_object(self, class_name: str, uuid: str) -> bool:
        """
        Delete an object by its UUID.
        
        Args:
            class_name: Class name in the vector database
            uuid: UUID of the object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete the object directly via REST API
            response = requests.delete(
                f"{self.url}/v1/objects/{class_name}/{uuid}",
                headers=self.headers
            )
            
            if response.status_code not in [200, 204]:
                logger.error(f"Failed to delete object {class_name}/{uuid}: {response.status_code} {response.text}")
                return False
                
            logger.info(f"Deleted {class_name} object with UUID: {uuid}")
            return True
        except Exception as e:
            logger.error(f"Error deleting {class_name} object {uuid}: {e}")
            return False

    def search(
        self, 
        class_name: str, 
        query: str, 
        limit: int = 10, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search in the vector database.
        
        Args:
            class_name: Class name to search in
            query: Search query text
            limit: Maximum number of results
            filters: Optional dictionary of filters to apply
            
        Returns:
            List of matching objects
        """
        try:
            # Generate query vector using local embedding model (privacy-preserving)
            query_vector = self.embed_text(query)
            
            # Get schema properties
            properties = list(get_schema(class_name)["properties"].keys())
            
            # Format vector as a proper JSON array string for the GraphQL query
            vector_str = json.dumps(query_vector)
            
            # Build GraphQL query
            gql_query = {
                "query": f"""
                {{  
                    Get {{ 
                        {class_name}(
                            limit: {limit}
                            nearVector: {{ 
                                vector: {vector_str}
                                certainty: 0.6
                            }}
                        ) {{ 
                            _additional {{ 
                                id
                                certainty 
                            }}
                            {' '.join(properties)}
                        }} 
                    }} 
                }}
                """
            }
            
            # Log the query for debugging
            logger.info(f"Executing search query with vector of length {len(query_vector)}")
            logger.debug(f"Query: {gql_query['query']}")
            
            # Execute the query via REST API
            response = requests.post(
                f"{self.url}/v1/graphql",
                headers=self.headers,
                json=gql_query
            )
            
            if response.status_code != 200:
                logger.error(f"Error in GraphQL query: {response.status_code} {response.text}")
                return []
            
            # Parse results
            result = response.json()
            
            # Format the results to expected structure
            if result and "data" in result and "Get" in result["data"] and class_name in result["data"]["Get"]:
                results = result["data"]["Get"][class_name]
                
                # Format each result
                formatted_results = []
                for item in results:
                    # Extract properties to top level
                    formatted_item = {}
                    
                    # Add properties directly at the top level
                    for prop in properties:
                        if prop in item:
                            formatted_item[prop] = item[prop]
                    
                    # Add metadata in _additional field
                    formatted_item["_additional"] = {
                        "id": item.get("_additional", {}).get("id"),
                        "certainty": item.get("_additional", {}).get("certainty")
                    }
                    
                    formatted_results.append(formatted_item)
                
                return formatted_results
            
            return []
            
        except Exception as e:
            logger.error(f"Error performing search in {class_name}: {e}")
            return []

    def _build_where_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a Weaviate where filter from a dictionary of filters.
        
        Args:
            filters: Dictionary of filters to apply
            
        Returns:
            Weaviate where filter object
        """
        where_filter = {}
        
        for field, value in filters.items():
            if isinstance(value, str):
                # Text field equals
                where_filter["path"] = [field]
                where_filter["operator"] = "Equal"
                where_filter["valueText"] = value
            elif isinstance(value, (int, float)):
                # Numeric field equals
                where_filter["path"] = [field]
                where_filter["operator"] = "Equal"
                where_filter["valueNumber"] = value
            elif isinstance(value, list):
                # Contains any of these values
                where_filter["path"] = [field]
                where_filter["operator"] = "ContainsAny" 
                where_filter["valueTextArray"] = value
            elif isinstance(value, dict) and "operator" in value:
                # Custom operator
                where_filter["path"] = [field]
                where_filter["operator"] = value["operator"]
                
                if "value" in value:
                    if isinstance(value["value"], str):
                        where_filter["valueText"] = value["value"]
                    elif isinstance(value["value"], (int, float)):
                        where_filter["valueNumber"] = value["value"]
                    elif isinstance(value["value"], list):
                        where_filter["valueTextArray"] = value["value"]
        
        return where_filter

    def get_job_candidates_match(
        self, 
        job_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find candidates that match a specific job description.
        This is a privacy-first implementation that uses local embedding models
        to perform semantic matching between jobs and candidates.
        
        Args:
            job_id: UUID of the job description
            limit: Maximum number of results
            
        Returns:
            List of matching candidate profiles with match scores
        """
        try:
            # Get job description
            job = self.get_by_id("JobDescription", job_id)
            if not job:
                logger.error(f"Job description {job_id} not found")
                return []
            
            # Extract key information for matching
            job_props = job.get('properties', {})
            job_text = f"{job_props.get('title', '')}. {job_props.get('description', '')}. {job_props.get('requirements', '')}"
            
            # Get matching candidates using semantic search
            return self.search(
                class_name="CandidateProfile",
                query=job_text,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Error matching candidates to job {job_id}: {e}")
            return []

    def get_candidate_jobs_match(
        self, 
        candidate_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find jobs that match a specific candidate profile.
        Uses on-premise semantic matching for privacy protection.
        
        Args:
            candidate_id: UUID of the candidate profile
            limit: Maximum number of results
            
        Returns:
            List of matching job descriptions with match scores
        """
        try:
            # Get candidate profile
            candidate = self.get_by_id("CandidateProfile", candidate_id)
            if not candidate:
                logger.error(f"Candidate profile {candidate_id} not found")
                return []
            
            # Extract key information for matching
            candidate_props = candidate.get('properties', {})
            skills = candidate_props.get('skills', [])
            skills_text = ", ".join(skills) if isinstance(skills, list) else skills
            
            candidate_text = f"{candidate_props.get('summary', '')}. {skills_text}. {candidate_props.get('experience', '')}. {candidate_props.get('education', '')}"
            
            # Get matching jobs
            return self.search(
                class_name="JobDescription",
                query=candidate_text,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Error matching jobs to candidate {candidate_id}: {e}")
            return []


# Singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """
    Get or create the VectorStore singleton instance.
    
    Returns:
        VectorStore instance
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
