"""
Test script for LLM services.

This script tests both Gemini API (free tier) and Docker-based LLM services
to ensure they're properly integrated and working.
"""
import logging
import time
from typing import List, Dict, Any

from src.llm.llm_factory import get_llm_service, LLMServiceType
from src.utils.config import GEMINI_API_KEYS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_llm_services():
    """Test the LLM services integration."""
    logger.info("Testing LLM services...")
    
    # Check for Gemini API keys
    if not GEMINI_API_KEYS:
        logger.warning("No Gemini API keys found. Gemini tests will be skipped.")
        logger.info("Add your free Gemini API keys to .env (GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.)")
    else:
        logger.info(f"Found {len(GEMINI_API_KEYS)} Gemini API keys")
    
    # Create LLM service with auto-selection
    llm_service = get_llm_service(LLMServiceType.AUTO)
    
    # Get service status
    status = llm_service.get_service_status()
    logger.info(f"Active LLM service: {status['active_service']}")
    logger.info(f"Gemini available: {status['gemini']['available']}")
    logger.info(f"Docker available: {status['docker']['available']}")
    
    # Test generating text with the active service
    active_service = status['active_service']
    
    if active_service:
        logger.info(f"Testing text generation with {active_service} service...")
        
        try:
            # Simple prompt
            prompt = "What are the key skills needed for a Full Stack Developer position?"
            
            # Generate text
            start_time = time.time()
            response = llm_service.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_output_tokens=1024
            )
            duration = time.time() - start_time
            
            logger.info(f"✅ Generated text in {duration:.2f} seconds")
            logger.info(f"Response excerpt: {response[:100]}...")
            
            # Test chat response
            logger.info(f"Testing chat response with {active_service} service...")
            
            # Chat messages
            messages = [
                {"role": "system", "content": "You are a helpful recruitment assistant."},
                {"role": "user", "content": "What questions should I ask a Data Science candidate?"}
            ]
            
            # Generate chat response
            start_time = time.time()
            chat_response = llm_service.generate_chat_response(
                messages=messages,
                temperature=0.7,
                max_output_tokens=1024
            )
            duration = time.time() - start_time
            
            logger.info(f"✅ Generated chat response in {duration:.2f} seconds")
            logger.info(f"Chat response excerpt: {chat_response[:100]}...")
            
            # Test service switching if both are available
            if status['gemini']['available'] and status['docker']['available']:
                logger.info("Testing service switching...")
                
                # Switch to the opposite service
                opposite_service = LLMServiceType.DOCKER if active_service == "gemini" else LLMServiceType.GEMINI
                
                # Try to switch
                switched = llm_service.switch_service(opposite_service)
                
                if switched:
                    logger.info(f"✅ Successfully switched to {opposite_service.value} service")
                    
                    # Get updated status
                    new_status = llm_service.get_service_status()
                    logger.info(f"New active service: {new_status['active_service']}")
                    
                    # Try a simple generation with the new service
                    prompt = "What questions should I ask during a technical interview?"
                    
                    start_time = time.time()
                    new_response = llm_service.generate_text(
                        prompt=prompt,
                        temperature=0.7,
                        max_output_tokens=1024
                    )
                    duration = time.time() - start_time
                    
                    logger.info(f"✅ Generated text with {new_status['active_service']} service in {duration:.2f} seconds")
                    logger.info(f"Response excerpt: {new_response[:100]}...")
                else:
                    logger.warning(f"❌ Failed to switch to {opposite_service.value} service")
            
            logger.info("✅ LLM services test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error testing LLM services: {e}")
            return False
    else:
        logger.error("❌ No active LLM service available")
        return False

if __name__ == "__main__":
    test_llm_services()
