"""
Test script for the agent registry.

This script demonstrates how to use the AgentRegistry to manage agents
and route messages between them.
"""
import logging
import time
from typing import Dict, Any

from src.orchestration.agent import Agent, AgentStatus, Message, MessageType
from src.orchestration.agent_registry import get_agent_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class TestAgent(Agent):
    """Test agent implementation for registry testing."""
    
    def __init__(self, agent_id: str, name: str, capabilities: list = None):
        """Initialize test agent."""
        capabilities = capabilities or ["test", "echo"]
        super().__init__(agent_id, name, f"Test agent for {name}", capabilities)
        self.received_commands = []
        self.last_command_time = 0  # Track when commands are received
    
    def initialize(self) -> None:
        """Initialize the agent."""
        logger.info(f"Initializing {self.name}")
        # Simple initialization for test
    
    def handle_command(self, message: Message) -> None:
        """Handle command messages."""
        command = message.content.get("command")
        logger.info(f"Agent {self.name} received command: {command}")
        
        self.received_commands.append(command)
        self.last_command_time = time.time()
        
        if command == "echo":
            # Echo back the message content
            text = message.content.get("text", "")
            self._send_simple_response(
                message,
                f"Echo: {text}",
                {"original_text": text}
            )
        elif command == "ping":
            # Respond to ping
            self._send_simple_response(message, "pong")
        else:
            # Unknown command
            self._send_simple_response(
                message,
                f"Unknown command: {command}"
            )


def test_agent_registry():
    """Test the agent registry functionality."""
    logger.info("Testing agent registry...")
    
    # Get agent registry
    registry = get_agent_registry()
    
    try:
        # Create test agents
        agent1 = TestAgent("test_agent_1", "Agent 1")
        agent2 = TestAgent("test_agent_2", "Agent 2")
        agent3 = TestAgent("test_agent_3", "Agent 3", ["test", "echo", "special"])
        
        # Register agents
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        registry.register_agent(agent3)
        
        # Verify registration
        assert len(registry.get_all_agents()) == 3
        logger.info("✅ Agents registered successfully")
        
        # Debug capabilities
        logger.info(f"Registry capabilities: {registry.capabilities}")
        for agent in registry.get_all_agents():
            logger.info(f"Agent {agent.name} has capabilities: {agent.capabilities}")
        
        # Test lookup
        test_agents = registry.get_agents_by_capability("test")
        logger.info(f"Found {len(test_agents)} agents with 'test' capability")
        assert len(test_agents) == 3
        
        special_agents = registry.get_agents_by_capability("special")
        assert len(special_agents) == 1
        assert special_agents[0].agent_id == "test_agent_3"
        logger.info("✅ Agent lookup works")
        
        # Start agents
        logger.info("Starting all agents...")
        registry.start_all_agents()
        
        # Wait for agents to be ready (with timeout)
        max_wait = 5  # seconds
        start_time = time.time()
        all_ready = False
        
        while time.time() - start_time < max_wait and not all_ready:
            all_ready = all(agent.status == AgentStatus.READY for agent in registry.get_all_agents())
            if not all_ready:
                time.sleep(0.1)
        
        assert all_ready, "Timed out waiting for agents to be ready"
        logger.info("✅ All agents started and ready")
        
        # Test direct message
        logger.info("Testing direct message (ping)...")
        agent1.send_message(
            receiver=agent2.agent_id,
            message_type=MessageType.COMMAND,
            content={"command": "ping"}
        )
        
        # Wait for ping to be received (with timeout)
        max_wait = 5  # seconds
        start_time = time.time()
        ping_received = False
        
        while time.time() - start_time < max_wait and not ping_received:
            ping_received = "ping" in agent2.received_commands
            if not ping_received:
                time.sleep(0.1)
        
        # Debug received commands
        logger.info(f"Agent {agent2.name} received commands: {agent2.received_commands}")
        assert ping_received, "Timed out waiting for ping command"
        logger.info("✅ Direct message sent and received")
        
        # Reset received commands for clean testing
        for agent in registry.get_all_agents():
            agent.received_commands = []
        
        # Test broadcasting
        logger.info("Broadcasting echo command to all agents with 'test' capability")
        registry.broadcast_to_capability(
            capability="test",
            message_type=MessageType.COMMAND,
            content={"command": "echo", "text": "Hello from registry"}
        )
        
        # Wait for all agents to receive the broadcast (with timeout)
        max_wait = 5  # seconds
        start_time = time.time()
        all_received = False
        
        while time.time() - start_time < max_wait and not all_received:
            all_received = all("echo" in agent.received_commands for agent in registry.get_all_agents())
            if not all_received:
                time.sleep(0.1)
        
        # Debug received commands
        for agent in registry.get_all_agents():
            logger.info(f"Agent {agent.name} received commands: {agent.received_commands}")
        
        assert all_received, "Timed out waiting for broadcast to be received"
        logger.info("✅ Broadcast to capability successful")
        
        # Stop all agents
        logger.info("Stopping all agents...")
        registry.stop_all_agents()
        
        # Wait for agents to stop (with timeout)
        max_wait = 5  # seconds
        start_time = time.time()
        all_stopped = False
        
        while time.time() - start_time < max_wait and not all_stopped:
            all_stopped = all(agent.status == AgentStatus.STOPPED for agent in registry.get_all_agents())
            if not all_stopped:
                time.sleep(0.1)
        
        assert all_stopped, "Timed out waiting for agents to stop"
        logger.info("✅ All agents stopped successfully")
        
        # Clean up
        for agent_id in list(registry.agents.keys()):
            registry.unregister_agent(agent_id)
        
        assert len(registry.get_all_agents()) == 0
        logger.info("✅ All agents unregistered successfully")
        
        logger.info("✅ Agent registry test completed successfully!")
        return True
    
    except Exception as e:
        logger.error(f"Test failed: {e}")
        # Try to clean up
        for agent in registry.get_all_agents():
            try:
                agent.stop()
                registry.unregister_agent(agent.agent_id)
            except:
                pass
        return False


if __name__ == "__main__":
    success = test_agent_registry()
    exit(0 if success else 1)
