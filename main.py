"""
Main entry point for the RecruitPro AI application.

This script launches the FastAPI application with Uvicorn server.
"""
import logging
import uvicorn

from src.api.app import app
from src.utils.config import API_HOST, API_PORT, DEBUG
from src.knowledge_base.vector_store import get_vector_store

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    # Log startup message
    logger.info(f"Starting RecruitPro AI on {API_HOST}:{API_PORT}")
    logger.info(f"Debug mode: {DEBUG}")
    
    # Initialize vector store (ensure schemas exist)
    try:
        vector_store = get_vector_store()
        logger.info("Vector store initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")
        logger.error("Make sure Weaviate is running and accessible")
        logger.info("You can set up Weaviate using: python setup_weaviate.py")
        exit(1)
    
    # Start Uvicorn server
    uvicorn.run(
        "src.api.app:app",
        host=API_HOST,
        port=API_PORT,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info",
    )
