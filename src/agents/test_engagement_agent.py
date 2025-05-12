"""
Test script for the EngagementAgent.

This script demonstrates how the EngagementAgent provides conversational interactions
with candidates and maintains conversation state.
"""
import json
import logging
import time
from typing import Dict, Any, List

from src.agents.engagement_agent import EngagementAgent, MessageRequest, Conversation
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
    "title": "Senior Full Stack Developer",
    "company": "TechInnovate Solutions",
    "location": "Remote (US)",
    "description": "We are looking for a Senior Full Stack Developer to join our product team. You will work on developing and maintaining our SaaS platform that helps businesses manage their operations efficiently.",
    "requirements": """
    Requirements:
    - 5+ years of experience in full stack development
    - Strong proficiency in JavaScript/TypeScript, React, and Node.js
    - Experience with SQL and NoSQL databases
    - Familiarity with cloud platforms (AWS, GCP, or Azure)
    - Strong problem-solving skills and attention to detail
    
    Preferred Qualifications:
    - Experience with microservices architecture
    - Knowledge of Docker and Kubernetes
    - Experience with CI/CD pipelines
    - Previous work with SaaS products
    
    Responsibilities:
    - Develop and maintain front-end and back-end components
    - Collaborate with product managers to implement new features
    - Ensure code quality through testing and code reviews
    - Optimize application performance and scalability
    - Participate in agile development processes
    """
}

# Sample candidate data for testing
SAMPLE_CANDIDATE = {
    "name": "Jordan Taylor",
    "email": "jordan.taylor@example.com",
    "phone": "(123) 456-7890",
    "skills": ["JavaScript", "TypeScript", "React", "Node.js", "MongoDB", "AWS", "Docker"],
    "education": ["BS in Computer Science, University of Washington"],
    "experience": """
    - Senior Software Engineer at WebTech Inc. (3 years)
      Led development of a React-based dashboard application
      Implemented Node.js microservices for backend functionality
      Managed AWS infrastructure using Terraform
    
    - Full Stack Developer at AppSolutions (4 years)
      Developed and maintained multiple web applications
      Implemented RESTful APIs using Express.js
      Worked with MongoDB and PostgreSQL databases
    """,
    "location": "Seattle, WA",
    "resume_text": """
    JORDAN TAYLOR
    Full Stack Developer
    jordan.taylor@example.com | (123) 456-7890 | Seattle, WA
    
    SKILLS
    Languages: JavaScript, TypeScript, HTML, CSS, SQL
    Frameworks: React, Angular, Express.js, Node.js
    Databases: MongoDB, PostgreSQL, Redis
    Tools: Git, Docker, AWS, Jest, Webpack
    
    EXPERIENCE
    Senior Software Engineer | WebTech Inc.
    2020 - Present (3 years)
    - Led development of a React-based dashboard application
    - Implemented Node.js microservices for backend functionality
    - Managed AWS infrastructure using Terraform
    - Mentored junior developers and conducted code reviews
    
    Full Stack Developer | AppSolutions
    2016 - 2020 (4 years)
    - Developed and maintained multiple web applications
    - Implemented RESTful APIs using Express.js
    - Worked with MongoDB and PostgreSQL databases
    - Participated in agile development processes
    
    EDUCATION
    BS in Computer Science, University of Washington
    """
}


def test_engagement_agent():
    """Test the EngagementAgent functionality."""
    logger.info("Testing EngagementAgent...")
    
    # Initialize registry
    registry = get_agent_registry()
    
    try:
        # Create and register engagement agent
        engagement_agent = EngagementAgent()
        registry.register_agent(engagement_agent)
        
        # Start the agent
        registry.start_agent(engagement_agent.agent_id)
        logger.info("EngagementAgent started")
        
        # Add job to the vector store
        job_id = engagement_agent.vector_store.add_job_description(
            title=SAMPLE_JOB["title"],
            company=SAMPLE_JOB["company"],
            location=SAMPLE_JOB["location"],
            description=SAMPLE_JOB["description"],
            requirements=SAMPLE_JOB["requirements"]
        )
        logger.info(f"Added job with ID: {job_id}")
        
        # Add sample candidate to the vector store
        candidate_id = engagement_agent.vector_store.add_candidate_profile(
            name=SAMPLE_CANDIDATE["name"],
            email=SAMPLE_CANDIDATE["email"],
            phone=SAMPLE_CANDIDATE["phone"],
            resume_text=SAMPLE_CANDIDATE["resume_text"],
            summary="",  # No summary in our test data
            skills=SAMPLE_CANDIDATE["skills"],
            experience=SAMPLE_CANDIDATE["experience"],
            education="\n".join(SAMPLE_CANDIDATE["education"])
        )
        logger.info(f"Added candidate {SAMPLE_CANDIDATE['name']} with ID: {candidate_id}")
        
        # Test 1: Initial greeting using template
        logger.info("Test 1: Sending initial greeting message...")
        greeting_request = MessageRequest(
            conversation_id=None,  # New conversation
            candidate_id=candidate_id,
            message="",  # Will be ignored since we're using a template
            job_id=job_id,
            template_key="greeting",
            template_vars={}  # Will use defaults from job and candidate data
        )
        
        conversation = engagement_agent.send_message(greeting_request)
        conversation_id = conversation.conversation_id
        
        # Verify the conversation was created
        if conversation and conversation.conversation_id:
            logger.info(f"✅ Created conversation with ID: {conversation.conversation_id}")
            logger.info(f"   Message: {conversation.messages[-1]['content'][:100]}...")
        else:
            logger.error("❌ Failed to create conversation")
            raise Exception("Failed to create conversation")
        
        # Test 2: Job description message
        logger.info("\nTest 2: Sending job description message...")
        job_description_request = MessageRequest(
            conversation_id=conversation_id,
            candidate_id=candidate_id,
            message="",
            job_id=job_id,
            template_key="job_description",
            template_vars={}
        )
        
        conversation = engagement_agent.send_message(job_description_request)
        
        # Verify the message was added
        if conversation and len(conversation.messages) == 2:
            logger.info(f"✅ Added job description message")
            logger.info(f"   Message: {conversation.messages[-1]['content'][:100]}...")
        else:
            logger.error("❌ Failed to add job description message")
            raise Exception("Failed to add job description message")
        
        # Test 3: Skill inquiry message
        logger.info("\nTest 3: Sending skill inquiry message...")
        skill_inquiry_request = MessageRequest(
            conversation_id=conversation_id,
            candidate_id=candidate_id,
            message="",
            job_id=job_id,
            template_key="skill_inquiry",
            template_vars={"specific_skill": "React"}
        )
        
        conversation = engagement_agent.send_message(skill_inquiry_request)
        
        # Verify the message was added
        if conversation and len(conversation.messages) == 3:
            logger.info(f"✅ Added skill inquiry message")
            logger.info(f"   Message: {conversation.messages[-1]['content'][:100]}...")
        else:
            logger.error("❌ Failed to add skill inquiry message")
            raise Exception("Failed to add skill inquiry message")
        
        # Test 4: Simulate candidate response
        logger.info("\nTest 4: Simulating candidate response...")
        candidate_response = """
        I've been working with React for over 5 years. Most recently, I led the development of a dashboard 
        application at WebTech that used React with TypeScript and Redux. The dashboard processed real-time
        data and displayed it through various interactive charts and tables. I also implemented several
        reusable component libraries that were used across multiple projects.
        """
        
        # Add the response directly to the conversation
        if conversation:
            conversation.messages.append({
                "role": "user",
                "content": candidate_response,
                "timestamp": time.time()
            })
            engagement_agent._save_conversation(conversation)
            logger.info(f"✅ Added simulated candidate response")
            logger.info(f"   Response: {candidate_response[:100]}...")
        
        # Test 5: Generate agent response to candidate
        logger.info("\nTest 5: Testing agent's ability to generate responses...")
        
        # Skip the actual LLM call if Ollama is not available
        if not engagement_agent.llm_available:
            logger.warning("⚠️ Ollama LLM not available, skipping actual response generation")
            logger.info("   Using simulated response instead")
            
            # Manually add a simulated response
            simulated_response = """
            Thank you for sharing your React experience. Your background with the dashboard application
            and component libraries is impressive and aligns well with what we're looking for.
            
            Could you tell me about your experience with Node.js and microservices architecture?
            """
            
            conversation.messages.append({
                "role": "assistant",
                "content": simulated_response,
                "timestamp": time.time()
            })
            engagement_agent._save_conversation(conversation)
            logger.info(f"✅ Added simulated agent response")
            logger.info(f"   Response: {simulated_response[:100]}...")
        else:
            # Use the actual LLM to generate a response
            response = engagement_agent.process_candidate_response(conversation_id, candidate_response)
            
            if response:
                logger.info(f"✅ Generated response to candidate input")
                logger.info(f"   Response: {response[:100]}...")
            else:
                logger.warning("⚠️ Failed to generate response, using fallback")
        
        # Test 6: Get conversation by ID
        logger.info("\nTest 6: Getting conversation by ID...")
        retrieved_conversation = engagement_agent.get_conversation_by_id(conversation_id)
        
        if retrieved_conversation and retrieved_conversation.conversation_id == conversation_id:
            logger.info(f"✅ Retrieved conversation by ID")
            logger.info(f"   Conversation has {len(retrieved_conversation.messages)} messages")
        else:
            logger.error("❌ Failed to retrieve conversation by ID")
            raise Exception("Failed to retrieve conversation by ID")
        
        # Test 7: Get conversation by candidate ID
        logger.info("\nTest 7: Getting conversation by candidate ID...")
        retrieved_conversation = engagement_agent.get_conversation_by_candidate(candidate_id)
        
        if retrieved_conversation and retrieved_conversation.candidate_id == candidate_id:
            logger.info(f"✅ Retrieved conversation by candidate ID")
            logger.info(f"   Conversation has {len(retrieved_conversation.messages)} messages")
        else:
            logger.error("❌ Failed to retrieve conversation by candidate ID")
            raise Exception("Failed to retrieve conversation by candidate ID")
        
        # Test 8: End conversation
        logger.info("\nTest 8: Ending conversation...")
        success = engagement_agent.end_conversation(conversation_id)
        
        if success:
            logger.info(f"✅ Ended conversation")
            # Verify conversation is no longer active
            ended_conversation = engagement_agent.get_conversation_by_id(conversation_id)
            if ended_conversation and ended_conversation.is_active == False:
                logger.info(f"   Conversation status: {ended_conversation.state}")
            else:
                logger.error("❌ Conversation not properly ended")
                if ended_conversation:
                    logger.error(f"   Conversation status: {ended_conversation.state}, is_active: {ended_conversation.is_active}")
        else:
            logger.error("❌ Failed to end conversation")
            raise Exception("Failed to end conversation")
        
        # Clean up
        logger.info("\nCleaning up...")
        
        # Delete job
        engagement_agent.vector_store.delete_object("JobDescription", job_id)
        logger.info(f"Deleted job with ID: {job_id}")
        
        # Delete candidate
        engagement_agent.vector_store.delete_object("CandidateProfile", candidate_id)
        logger.info(f"Deleted candidate with ID: {candidate_id}")
        
        # Stop agent
        registry.stop_agent(engagement_agent.agent_id)
        registry.unregister_agent(engagement_agent.agent_id)
        
        logger.info("\n✅ Test completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Test failed: {e}")
        # Try to clean up
        try:
            # Delete job and candidate if they exist
            if 'job_id' in locals():
                engagement_agent.vector_store.delete_object("JobDescription", job_id)
            
            if 'candidate_id' in locals():
                engagement_agent.vector_store.delete_object("CandidateProfile", candidate_id)
            
            # Stop agent
            registry.stop_agent(engagement_agent.agent_id)
            registry.unregister_agent(engagement_agent.agent_id)
        except Exception as cleanup_error:
            logger.error(f"Cleanup error: {cleanup_error}")
        
        return False


if __name__ == "__main__":
    success = test_engagement_agent()
    exit(0 if success else 1)
