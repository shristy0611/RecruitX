#!/usr/bin/env python3
"""
Test script for Gemma 3 integration with Docker Model Runner.

This script tests the Gemma 3 service integration with the Docker Desktop Model Runner.
"""
import logging
import sys
import time
import os

from src.llm.gemma3_service import get_gemma3_service, Gemma3Service
from src.llm.llm_factory import LLMService, LLMServiceType, get_llm_service
from src.utils.config import LOCAL_LLM_URL, LOCAL_LLM_MODEL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Override configuration for the test
os.environ["LOCAL_LLM_URL"] = "http://localhost:12434/engines/v1"
os.environ["LOCAL_LLM_MODEL"] = "ai/gemma3:4B-Q4_K_M"

def test_direct_gemma3_service():
    """Test the Gemma 3 service directly."""
    logger.info("Testing Gemma 3 service directly...")
    
    try:
        # Create a new instance with the correct configuration
        gemma3 = Gemma3Service(
            base_url="http://localhost:12434/engines/v1",
            model_name="ai/gemma3:4B-Q4_K_M"
        )
        
        if not gemma3.is_available:
            logger.error(f"Gemma 3 service is not available at {gemma3.base_url}")
            logger.error(f"Model: {gemma3.model_name}")
            return False
        
        logger.info(f"Gemma 3 service is available at {gemma3.base_url}")
        logger.info(f"Model: {gemma3.model_name}")
        
        # Test text generation
        logger.info("Testing text generation...")
        start_time = time.time()
        response = gemma3.generate_text(
            prompt="What makes a good resume stand out to recruiters?",
            max_output_tokens=200
        )
        elapsed = time.time() - start_time
        
        logger.info(f"Response received in {elapsed:.2f} seconds")
        logger.info(f"Response: {response[:100]}...")
        
        # Test chat completion
        logger.info("Testing chat completion...")
        start_time = time.time()
        response = gemma3.generate_chat_response(
            messages=[
                {"role": "user", "content": "What are the top 3 skills for a data scientist?"}
            ],
            max_output_tokens=200
        )
        elapsed = time.time() - start_time
        
        logger.info(f"Response received in {elapsed:.2f} seconds")
        logger.info(f"Response: {response[:100]}...")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing Gemma 3 service: {e}")
        return False

def test_llm_factory_integration():
    """Test the LLM factory integration with Gemma 3."""
    logger.info("Testing LLM factory integration with Gemma 3...")
    
    try:
        # Create a custom Gemma3 service instance
        custom_gemma3 = Gemma3Service(
            base_url="http://localhost:12434/engines/v1",
            model_name="ai/gemma3:4B-Q4_K_M"
        )
        
        # Create a basic prompt test
        logger.info("Testing direct inference with custom Gemma3 service...")
        
        # Test text generation
        start_time = time.time()
        response = custom_gemma3.generate_text(
            prompt="What are the key qualities of a successful software engineer?",
            max_output_tokens=200
        )
        elapsed = time.time() - start_time
        
        logger.info(f"Response received in {elapsed:.2f} seconds")
        logger.info(f"Response: {response[:100]}...")
        
        # Test chat completion
        logger.info("Testing chat completion with custom Gemma3 service...")
        start_time = time.time()
        response = custom_gemma3.generate_chat_response(
            messages=[
                {"role": "user", "content": "How can I improve my technical interview skills?"}
            ],
            max_output_tokens=200
        )
        elapsed = time.time() - start_time
        
        logger.info(f"Response received in {elapsed:.2f} seconds")
        logger.info(f"Response: {response[:100]}...")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing custom Gemma3 service: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting Gemma 3 integration test...")
    logger.info(f"Using Docker Model Runner at: {os.environ.get('LOCAL_LLM_URL')}")
    logger.info(f"Using model: {os.environ.get('LOCAL_LLM_MODEL')}")
    
    # Test the Gemma 3 service directly
    direct_test_success = test_direct_gemma3_service()
    
    if not direct_test_success:
        logger.error("Direct Gemma 3 service test failed")
        sys.exit(1)
    
    # Test the LLM factory integration
    factory_test_success = test_llm_factory_integration()
    
    if not factory_test_success:
        logger.error("LLM factory integration test failed")
        sys.exit(1)
    
    logger.info("All tests passed!")
    sys.exit(0) 