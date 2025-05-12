"""
Agent registry for the RecruitPro AI multi-agent system.

This module provides a central registry for managing all agents in the system,
including discovery, coordination, and lifecycle management.
"""
import logging
import threading
import time
import uuid
from typing import Dict, List, Optional, Set, Type, Any, Union, Callable

from src.orchestration.agent import Agent, AgentStatus
from src.orchestration.message_broker import (
    Message, 
    MessageType,
    MessagePriority, 
    get_message_broker
)

# Configure logging
logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Central registry for the RecruitPro AI multi-agent system.
    
    Provides:
    - Agent discovery and lookup
    - Agent lifecycle management (start/stop)
    - System-wide status monitoring
    - Inter-agent communication coordination
    """
    
    def __init__(self, registry_id: str = "agent_registry"):
        """
        Initialize the agent registry.
        
        Args:
            registry_id: Unique ID for the registry
        """
        self.registry_id = registry_id
        
        # Agent tracking
        self.agents: Dict[str, Agent] = {}
        self.agent_types: Dict[str, Set[str]] = {}  # type -> set of agent_ids
        self.capabilities: Dict[str, Set[str]] = {}  # capability -> set of agent_ids
        
        # Status tracking
        self.agent_status: Dict[str, AgentStatus] = {}
        
        # Message broker
        self.message_broker = get_message_broker()
        
        # Monitoring
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        
        logger.info(f"AgentRegistry initialized with ID: {registry_id}")
    
    def register_agent(self, agent: Agent) -> bool:
        """
        Register an agent with the registry.
        
        Args:
            agent: Agent to register
            
        Returns:
            True if registration successful, False otherwise
        """
        if agent.agent_id in self.agents:
            logger.warning(f"Agent {agent.agent_id} already registered")
            return False
        
        # Add to registry
        self.agents[agent.agent_id] = agent
        
        # Update type mapping
        agent_type = agent.__class__.__name__
        if agent_type not in self.agent_types:
            self.agent_types[agent_type] = set()
        self.agent_types[agent_type].add(agent.agent_id)
        
        # Update capabilities mapping
        for capability in agent.capabilities:
            if capability not in self.capabilities:
                self.capabilities[capability] = set()
            self.capabilities[capability].add(agent.agent_id)
        
        # Initialize status
        self.agent_status[agent.agent_id] = agent.status
        
        logger.info(f"Registered agent {agent.name} ({agent.agent_id})")
        return True
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the registry.
        
        Args:
            agent_id: ID of the agent to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not registered")
            return False
        
        agent = self.agents[agent_id]
        
        # Remove from type mapping
        agent_type = agent.__class__.__name__
        if agent_type in self.agent_types and agent_id in self.agent_types[agent_type]:
            self.agent_types[agent_type].remove(agent_id)
            if not self.agent_types[agent_type]:
                del self.agent_types[agent_type]
        
        # Remove from capabilities mapping
        for capability in agent.capabilities:
            if capability in self.capabilities and agent_id in self.capabilities[capability]:
                self.capabilities[capability].remove(agent_id)
                if not self.capabilities[capability]:
                    del self.capabilities[capability]
        
        # Remove status
        if agent_id in self.agent_status:
            del self.agent_status[agent_id]
        
        # Remove from registry
        del self.agents[agent_id]
        
        logger.info(f"Unregistered agent {agent.name} ({agent_id})")
        return True
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: ID of the agent to get
            
        Returns:
            Agent object or None if not found
        """
        return self.agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: Union[str, Type[Agent]]) -> List[Agent]:
        """
        Get all agents of a specific type.
        
        Args:
            agent_type: Type name or class of the agent
            
        Returns:
            List of matching agent objects
        """
        if isinstance(agent_type, type):
            agent_type = agent_type.__name__
        
        agent_ids = self.agent_types.get(agent_type, set())
        return [self.agents[agent_id] for agent_id in agent_ids]
    
    def get_agents_by_capability(self, capability: str) -> List[Agent]:
        """
        Get all agents with a specific capability.
        
        Args:
            capability: Capability to look for
            
        Returns:
            List of matching agent objects
        """
        agent_ids = self.capabilities.get(capability, set())
        return [self.agents[agent_id] for agent_id in agent_ids]
    
    def get_all_agents(self) -> List[Agent]:
        """
        Get all registered agents.
        
        Returns:
            List of all agent objects
        """
        return list(self.agents.values())
    
    def start_agent(self, agent_id: str) -> bool:
        """
        Start an agent.
        
        Args:
            agent_id: ID of the agent to start
            
        Returns:
            True if agent started successfully, False otherwise
        """
        agent = self.get_agent(agent_id)
        if not agent:
            logger.warning(f"Cannot start agent {agent_id} - not registered")
            return False
        
        agent.start()
        return True
    
    def stop_agent(self, agent_id: str) -> bool:
        """
        Stop an agent.
        
        Args:
            agent_id: ID of the agent to stop
            
        Returns:
            True if agent stopped successfully, False otherwise
        """
        agent = self.get_agent(agent_id)
        if not agent:
            logger.warning(f"Cannot stop agent {agent_id} - not registered")
            return False
        
        agent.stop()
        return True
    
    def start_all_agents(self) -> List[str]:
        """
        Start all registered agents.
        
        Returns:
            List of agent IDs that were started
        """
        started_agents = []
        for agent_id in self.agents.keys():
            if self.start_agent(agent_id):
                started_agents.append(agent_id)
        
        logger.info(f"Started {len(started_agents)} agents")
        return started_agents
    
    def stop_all_agents(self) -> List[str]:
        """
        Stop all registered agents.
        
        Returns:
            List of agent IDs that were stopped
        """
        stopped_agents = []
        for agent_id in self.agents.keys():
            if self.stop_agent(agent_id):
                stopped_agents.append(agent_id)
        
        logger.info(f"Stopped {len(stopped_agents)} agents")
        return stopped_agents
    
    def broadcast_to_all(
        self,
        message_type: MessageType,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        exclude: Optional[List[str]] = None
    ) -> List[str]:
        """
        Broadcast a message to all registered agents.
        
        Args:
            message_type: Type of message to broadcast
            content: Message payload
            priority: Message priority
            exclude: List of agent IDs to exclude from broadcast
            
        Returns:
            List of message IDs that were sent
        """
        exclude_set = set(exclude or [])
        receivers = [
            agent_id for agent_id in self.agents.keys()
            if agent_id not in exclude_set
        ]
        
        if not receivers:
            return []
        
        return self.message_broker.broadcast_message(
            sender=self.registry_id,
            receivers=receivers,
            message_type=message_type,
            content=content,
            priority=priority
        )
    
    def broadcast_to_type(
        self,
        agent_type: Union[str, Type[Agent]],
        message_type: MessageType,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> List[str]:
        """
        Broadcast a message to all agents of a specific type.
        
        Args:
            agent_type: Type name or class of agents to target
            message_type: Type of message to broadcast
            content: Message payload
            priority: Message priority
            
        Returns:
            List of message IDs that were sent
        """
        if isinstance(agent_type, type):
            agent_type = agent_type.__name__
        
        receivers = list(self.agent_types.get(agent_type, set()))
        if not receivers:
            return []
        
        return self.message_broker.broadcast_message(
            sender=self.registry_id,
            receivers=receivers,
            message_type=message_type,
            content=content,
            priority=priority
        )
    
    def broadcast_to_capability(
        self,
        capability: str,
        message_type: MessageType,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> List[str]:
        """
        Broadcast a message to all agents with a specific capability.
        
        Args:
            capability: Capability that agents must have
            message_type: Type of message to broadcast
            content: Message payload
            priority: Message priority
            
        Returns:
            List of message IDs that were sent
        """
        receivers = list(self.capabilities.get(capability, set()))
        if not receivers:
            return []
        
        return self.message_broker.broadcast_message(
            sender=self.registry_id,
            receivers=receivers,
            message_type=message_type,
            content=content,
            priority=priority
        )
    
    def find_agent_for_task(self, task_type: str, **criteria) -> Optional[Agent]:
        """
        Find the most suitable agent for a task.
        
        Args:
            task_type: Type of task to find an agent for
            **criteria: Additional criteria for agent selection
            
        Returns:
            Best matching agent or None if no suitable agent found
        """
        # Start with agents that have the capability
        candidates = self.get_agents_by_capability(task_type)
        if not candidates:
            return None
        
        # Filter by any additional criteria
        # This could be extended with more sophisticated selection logic
        for key, value in criteria.items():
            if key == "status":
                candidates = [
                    agent for agent in candidates
                    if agent.status == value
                ]
            elif key == "agent_type":
                candidates = [
                    agent for agent in candidates
                    if agent.__class__.__name__ == value
                ]
        
        # Return the first available agent
        return candidates[0] if candidates else None
    
    def start_monitoring(self, interval: float = 5.0) -> None:
        """
        Start monitoring agent statuses in a background thread.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            logger.warning("Monitoring already active")
            return
        
        self._stop_monitoring.clear()
        self._monitoring_thread = threading.Thread(
            target=self._monitor_agents,
            args=(interval,),
            daemon=True
        )
        self._monitoring_thread.start()
        logger.info(f"Started agent monitoring (interval: {interval}s)")
    
    def stop_monitoring(self) -> None:
        """Stop the agent monitoring thread."""
        if not self._monitoring_thread:
            return
        
        self._stop_monitoring.set()
        if self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=1.0)
        
        self._monitoring_thread = None
        logger.info("Stopped agent monitoring")
    
    def _monitor_agents(self, interval: float) -> None:
        """
        Background thread that monitors agent statuses.
        
        Args:
            interval: Monitoring interval in seconds
        """
        try:
            while not self._stop_monitoring.is_set():
                # Check status of each agent
                for agent_id, agent in self.agents.items():
                    # Update status in registry
                    current_status = agent.status
                    self.agent_status[agent_id] = current_status
                
                # Wait for next check
                time.sleep(interval)
        except Exception as e:
            logger.error(f"Error in agent monitoring thread: {e}")
    
    def shutdown(self) -> None:
        """Shutdown the registry and all agents."""
        logger.info("Shutting down agent registry")
        
        # Stop monitoring
        self.stop_monitoring()
        
        # Stop all agents
        self.stop_all_agents()
        
        # Close message broker connection
        self.message_broker.close()
        
        logger.info("Agent registry shutdown complete")


# Singleton instance
_agent_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """
    Get or create the AgentRegistry singleton instance.
    
    Returns:
        AgentRegistry instance
    """
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry
