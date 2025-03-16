"""OpenManus integration bridge for multi-agent testing."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import json

from tests.complex_system.state_tracker import SystemState, AgentState
from tests.complex_system.emergent_detector import EmergentBehavior
from tests.ai_pipeline.test_generator import GeneratedTest
from tests.ai_pipeline.test_executor import TestResult

logger = logging.getLogger(__name__)

@dataclass
class OpenManusAgent:
    """OpenManus agent wrapper."""
    agent_id: str
    agent_type: str
    capabilities: Set[str]
    state: Dict[str, Any]
    context: Dict[str, Any]
    communication_channels: List[str]
    last_update: float = field(default_factory=time.time)

@dataclass
class OpenManusMessage:
    """OpenManus communication message."""
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: str
    content: Dict[str, Any]
    timestamp: float
    context: Dict[str, Any]

class OpenManusBridge:
    """Bridge between testing framework and OpenManus."""
    
    def __init__(
        self,
        communication_timeout: float = 5.0,
        retry_limit: int = 3,
        buffer_size: int = 1000
    ):
        """Initialize the bridge.
        
        Args:
            communication_timeout: Timeout for agent communication
            retry_limit: Maximum retries for failed operations
            buffer_size: Size of message buffer
        """
        self.communication_timeout = communication_timeout
        self.retry_limit = retry_limit
        self.buffer_size = buffer_size
        
        # Agent management
        self.agents: Dict[str, OpenManusAgent] = {}
        self.agent_states: Dict[str, List[Dict[str, Any]]] = {}
        
        # Communication
        self.message_buffer: List[OpenManusMessage] = []
        self.pending_responses: Dict[str, asyncio.Future] = {}
        
        # Synchronization
        self.sync_lock = asyncio.Lock()
        self.message_counter = 0
        
    async def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: Set[str],
        initial_state: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Register an OpenManus agent.
        
        Args:
            agent_id: Agent identifier
            agent_type: Type of agent
            capabilities: Set of agent capabilities
            initial_state: Initial agent state
            context: Agent context
            
        Returns:
            True if registration successful
        """
        async with self.sync_lock:
            if agent_id in self.agents:
                logger.warning(f"Agent {agent_id} already registered")
                return False
                
            # Create agent
            agent = OpenManusAgent(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=capabilities,
                state=initial_state or {},
                context=context or {},
                communication_channels=[]
            )
            
            # Store agent
            self.agents[agent_id] = agent
            self.agent_states[agent_id] = []
            
            # Initialize state history
            if initial_state:
                self.agent_states[agent_id].append({
                    'state': initial_state,
                    'timestamp': time.time()
                })
                
            return True
            
    async def update_agent_state(
        self,
        agent_id: str,
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update agent state.
        
        Args:
            agent_id: Agent identifier
            state: New agent state
            context: Updated context
            
        Returns:
            True if update successful
        """
        async with self.sync_lock:
            if agent_id not in self.agents:
                logger.warning(f"Agent {agent_id} not found")
                return False
                
            # Update agent state
            self.agents[agent_id].state.update(state)
            self.agents[agent_id].last_update = time.time()
            
            # Update context if provided
            if context:
                self.agents[agent_id].context.update(context)
                
            # Store state history
            self.agent_states[agent_id].append({
                'state': state,
                'timestamp': time.time()
            })
            
            # Trim history if needed
            if len(self.agent_states[agent_id]) > self.buffer_size:
                self.agent_states[agent_id].pop(0)
                
            return True
            
    async def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        message_type: str,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[OpenManusMessage]:
        """Send message between agents.
        
        Args:
            sender_id: Sender agent ID
            receiver_id: Receiver agent ID
            message_type: Type of message
            content: Message content
            context: Message context
            
        Returns:
            Message object if sent successfully
        """
        if sender_id not in self.agents:
            logger.warning(f"Sender agent {sender_id} not found")
            return None
            
        if receiver_id not in self.agents:
            logger.warning(f"Receiver agent {receiver_id} not found")
            return None
            
        # Create message
        message = OpenManusMessage(
            message_id=f"msg_{self.message_counter}",
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content,
            timestamp=time.time(),
            context=context or {}
        )
        self.message_counter += 1
        
        # Add to buffer
        self.message_buffer.append(message)
        
        # Trim buffer if needed
        if len(self.message_buffer) > self.buffer_size:
            self.message_buffer.pop(0)
            
        return message
        
    async def get_agent_state(
        self,
        agent_id: str,
        include_history: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get agent state.
        
        Args:
            agent_id: Agent identifier
            include_history: Whether to include state history
            
        Returns:
            Agent state information
        """
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not found")
            return None
            
        agent = self.agents[agent_id]
        
        state_info = {
            'current_state': agent.state,
            'last_update': agent.last_update,
            'context': agent.context
        }
        
        if include_history:
            state_info['history'] = self.agent_states[agent_id]
            
        return state_info
        
    async def get_messages(
        self,
        agent_id: Optional[str] = None,
        message_type: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[OpenManusMessage]:
        """Get filtered messages.
        
        Args:
            agent_id: Filter by agent ID
            message_type: Filter by message type
            start_time: Filter by start time
            end_time: Filter by end time
            
        Returns:
            List of matching messages
        """
        messages = self.message_buffer
        
        # Apply filters
        if agent_id:
            messages = [
                m for m in messages
                if m.sender_id == agent_id or m.receiver_id == agent_id
            ]
            
        if message_type:
            messages = [
                m for m in messages
                if m.message_type == message_type
            ]
            
        if start_time:
            messages = [
                m for m in messages
                if m.timestamp >= start_time
            ]
            
        if end_time:
            messages = [
                m for m in messages
                if m.timestamp <= end_time
            ]
            
        return messages
        
    async def convert_to_system_state(self) -> SystemState:
        """Convert current state to SystemState.
        
        Returns:
            SystemState object
        """
        # Create agent states
        agent_states = {}
        for agent_id, agent in self.agents.items():
            agent_states[agent_id] = AgentState(
                agent_id=agent_id,
                timestamp=agent.last_update,
                status="active",
                metrics=agent.state,
                last_update=agent.last_update,
                confidence=agent.state.get('confidence', 1.0)
            )
            
        # Calculate global metrics
        global_metrics = {
            'total_agents': len(self.agents),
            'active_agents': len(self.agents),  # All agents considered active
            'message_count': len(self.message_buffer),
            'average_update_rate': self._calculate_update_rate()
        }
        
        # Get consensus values
        consensus_values = self._get_consensus_values()
        
        # Create system state
        return SystemState(
            timestamp=time.time(),
            agents=agent_states,
            global_metrics=global_metrics,
            consensus_values=consensus_values,
            emergent_patterns=[]  # Patterns detected separately
        )
        
    def _calculate_update_rate(self) -> float:
        """Calculate average agent update rate.
        
        Returns:
            Updates per second
        """
        now = time.time()
        window = 60.0  # 1 minute window
        
        updates = 0
        for agent_states in self.agent_states.values():
            updates += sum(
                1 for s in agent_states
                if now - s['timestamp'] <= window
            )
            
        return updates / window
        
    def _get_consensus_values(self) -> Dict[str, Any]:
        """Get consensus values across agents.
        
        Returns:
            Dictionary of consensus values
        """
        consensus = {}
        
        # Get all metric keys
        all_metrics = set()
        for agent in self.agents.values():
            all_metrics.update(agent.state.keys())
            
        # Find consensus for each metric
        for metric in all_metrics:
            values = [
                agent.state[metric]
                for agent in self.agents.values()
                if metric in agent.state
            ]
            
            if not values:
                continue
                
            # Get most common value
            value_counts = {}
            for v in values:
                value_counts[v] = value_counts.get(v, 0) + 1
                
            max_count = max(value_counts.values())
            if max_count >= len(self.agents) * 0.67:  # 67% consensus
                consensus[metric] = max(
                    value_counts.items(),
                    key=lambda x: x[1]
                )[0]
                
        return consensus 