"""
Configuration utilities for RecruitPro AI.
Handles environment variables, connections, and global settings.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).parent.parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

# Database configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "recruitx")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "your_postgres_password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "recruitx_dev")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Weaviate vector database configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_GRPC_URL = os.getenv("WEAVIATE_GRPC_URL", "localhost:50051")

# MinIO / S3 configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "your_minio_user")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "your_minio_password")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
DOCUMENT_BUCKET = os.getenv("DOCUMENT_BUCKET", "recruitx-documents")

# LLM configuration
# Parse the 10 rotating Gemini API keys
GEMINI_API_KEYS = [
    os.getenv(f"GEMINI_API_KEY_{i}", "")
    for i in range(1, 11)
    if os.getenv(f"GEMINI_API_KEY_{i}", "")
]
# Parse the 10 rotating Gemma API keys
GEMMA_API_KEYS = [
    os.getenv(f"GEMMA_API_KEY_{i}", "")
    for i in range(1, 11)
    if os.getenv(f"GEMMA_API_KEY_{i}", "")
]
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-2.0-flash-lite")
GEMINI_THINKING_MODEL = os.getenv("GEMINI_THINKING_MODEL", "gemini-2.0-flash")
GEMMA_MODEL = os.getenv("GEMMA_MODEL", "gemma-3")
# For local deployment
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"

# Ollama configuration for local LLM
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b-instruct")

# Docker Desktop Models configuration
DOCKER_DESKTOP_MODEL_URL = os.getenv("DOCKER_DESKTOP_MODEL_URL", "http://localhost:12434/engines/v1")
LOCAL_LLM_URL = os.getenv("LOCAL_LLM_URL", "http://localhost:12434/engines/v1")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "ai/gemma3:4B-Q4_K_M")

# Debug/logging settings
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Vector embedding models
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))

# Knowledge base schema settings
SCHEMAS = {
    "JobDescription": {
        "vectorizer": "text2vec-transformers",
        "properties": {
            "title": {"dataType": ["text"]},
            "description": {"dataType": ["text"]},
            "requirements": {"dataType": ["text"]},
            "company": {"dataType": ["text"]},
            "location": {"dataType": ["text"]},
            "salary_range": {"dataType": ["text"]},
            "job_type": {"dataType": ["text"]},
            "created_at": {"dataType": ["date"]},
            "updated_at": {"dataType": ["date"]},
        },
    },
    "CandidateProfile": {
        "vectorizer": "text2vec-transformers",
        "properties": {
            "name": {"dataType": ["text"]},
            "email": {"dataType": ["text"]},
            "phone": {"dataType": ["text"]},
            "summary": {"dataType": ["text"]},
            "skills": {"dataType": ["text[]"]},
            "experience": {"dataType": ["text"]},
            "education": {"dataType": ["text"]},
            "resume_text": {"dataType": ["text"]},
            "resume_vector": {"dataType": ["number[]"], "vectorize": False},
            "created_at": {"dataType": ["date"]},
            "updated_at": {"dataType": ["date"]},
        },
    },
    "CompanyData": {
        "vectorizer": "text2vec-transformers",
        "properties": {
            "name": {"dataType": ["text"]},
            "description": {"dataType": ["text"]},
            "culture": {"dataType": ["text"]},
            "benefits": {"dataType": ["text"]},
            "industry": {"dataType": ["text"]},
            "created_at": {"dataType": ["date"]},
            "updated_at": {"dataType": ["date"]},
        },
    },
}


def get_schema(schema_name: str) -> Dict[str, Any]:
    """
    Retrieve schema configuration by name.
    
    Args:
        schema_name: Name of the schema to retrieve
        
    Returns:
        Schema configuration dictionary
    """
    if schema_name not in SCHEMAS:
        raise ValueError(f"Schema {schema_name} not found")
    return SCHEMAS[schema_name]


# API and web server settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
API_CORS_ORIGINS = os.getenv(
    "API_CORS_ORIGINS", "http://localhost:3000,http://localhost:8000"
).split(",")
