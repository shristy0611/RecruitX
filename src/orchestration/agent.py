"""
Base agent class for RecruitPro AI's multi-agent system.

This module provides the foundational Agent class that all specialized
agents will inherit from, with message handling capabilities.
"""
import json
import logging
import threading
import time
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Union

from src.orchestration.message_broker import (
    Message, 
    MessageType,
    MessagePriority, 
    MessageBroker, 
    get_message_broker
)

# Configure logging
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Status values for agents."""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class Agent(ABC):
    """
    Base agent class for the RecruitPro AI multi-agent system.
    
    This abstract class provides core functionality for all agents:
    - Message handling
    - Status management
    - Integration with the message broker
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str = "",
        capabilities: Optional[List[str]] = None
    ):
        """
        Initialize the agent.
        
        Args:
            agent_id: Unique ID for the agent
            name: Human-readable name for the agent
            description: Description of the agent's purpose
            capabilities: List of capabilities this agent provides
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities or []
        
        # Connect to the message broker
        self.message_broker = get_message_broker()
        
        # Set initial status
        self._status = AgentStatus.INITIALIZING
        self._status_message = "Agent initializing"
        
        # Message handling
        self.message_handlers: Dict[MessageType, Callable[[Message], None]] = {}
        self._known_agents: Set[str] = set()
        self._listening_thread: Optional[threading.Thread] = None
        self._stop_listening = threading.Event()
        
        # Register default message handlers
        self._register_default_handlers()
    
    @property
    def status(self) -> AgentStatus:
        """Get the current agent status."""
        return self._status
    
    @status.setter
    def status(self, value: Union[AgentStatus, str]) -> None:
        """Set the agent status."""
        if isinstance(value, str):
            value = AgentStatus(value)
        self._status = value
        self._broadcast_status()
    
    def _broadcast_status(self) -> None:
        """Broadcast status change to other agents."""
        if not self._known_agents:
            return
        
        content = {
            "status": self._status.value,
            "message": self._status_message,
            "timestamp": time.time()
        }
        
        self.message_broker.broadcast_message(
            sender=self.agent_id,
            receivers=list(self._known_agents),
            message_type=MessageType.STATUS,
            content=content
        )
    
    def _register_default_handlers(self) -> None:
        """Register default message handlers."""
        # Register handlers for different message types
        self.register_handler(MessageType.COMMAND, self._handle_command)
        self.register_handler(MessageType.STATUS, self._handle_status)
    
    def register_handler(
        self, 
        message_type: MessageType, 
        handler: Callable[[Message], None]
    ) -> None:
        """
        Register a handler for a specific message type.
        
        Args:
            message_type: Type of message to handle
            handler: Function to handle the message
        """
        self.message_handlers[message_type] = handler
    
    def send_message(
        self,
        receiver: str,
        message_type: MessageType,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        parent_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Send a message to another agent.
        
        Args:
            receiver: ID of the receiving agent
            message_type: Type of message
            content: Message payload
            priority: Message priority
            parent_id: ID of the parent message (for threaded conversations)
            
        Returns:
            Message ID if successful, None otherwise
        """
        message = Message(
            sender=self.agent_id,
            receiver=receiver,
            message_type=message_type,
            content=content,
            priority=priority,
            parent_id=parent_id
        )
        
        if self.message_broker.send_message(message):
            # Add receiver to known agents
            self._known_agents.add(receiver)
            return message.message_id
        return None
    
    def broadcast_message(
        self,
        receivers: List[str],
        message_type: MessageType,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> List[str]:
        """
        Broadcast a message to multiple agents.
        
        Args:
            receivers: List of receiving agent IDs
            message_type: Type of message
            content: Message payload
            priority: Message priority
            
        Returns:
            List of successfully sent message IDs
        """
        message_ids = self.message_broker.broadcast_message(
            sender=self.agent_id,
            receivers=receivers,
            message_type=message_type,
            content=content,
            priority=priority
        )
        
        # Add receivers to known agents
        self._known_agents.update(receivers)
        return message_ids
    
    def receive_message(self, timeout: int = 0) -> Optional[Message]:
        """
        Receive a message from the agent's queue.
        
        Args:
            timeout: Time to wait for a message (0 = no wait)
            
        Returns:
            Message object or None if no message available
        """
        return self.message_broker.receive_message(self.agent_id, timeout)
    
    def _handle_message(self, message: Message) -> None:
        """
        Primary message handler that routes to type-specific handlers.
        
        Args:
            message: Received message
        """
        logger.debug(f"Agent {self.agent_id} received message: {message.message_id}")
        
        # Route to specific handler based on message type
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error handling message {message.message_id}: {e}")
                self._send_error_response(message, str(e))
        else:
            logger.warning(f"No handler for message type: {message.message_type.value}")
    
    def _handle_command(self, message: Message) -> None:
        """
        Handle command messages.
        
        Args:
            message: Command message
        """
        command = message.content.get("command")
        if not command:
            self._send_error_response(message, "No command specified")
            return
        
        if command == "status":
            # Respond with current status
            self._send_status_response(message)
        elif command == "capabilities":
            # Respond with agent capabilities
            self._send_capabilities_response(message)
        elif command == "stop":
            # Stop the agent
            self.stop()
            self._send_simple_response(message, "Agent stopped")
        else:
            # Let the subclass handle the command
            self.handle_command(message)
    
    def _handle_status(self, message: Message) -> None:
        """
        Handle status update messages.
        
        Args:
            message: Status message
        """
        # Add sender to known agents
        self._known_agents.add(message.sender)
        
        # Subclass can override to handle status updates
        self.handle_status(message)
    
    def _send_error_response(self, original_message: Message, error_message: str) -> None:
        """
        Send an error response to a message.
        
        Args:
            original_message: Original message that caused the error
            error_message: Error message
        """
        content = {
            "error": error_message,
            "in_response_to": original_message.message_id
        }
        
        self.send_message(
            receiver=original_message.sender,
            message_type=MessageType.ERROR,
            content=content,
            priority=MessagePriority.HIGH,
            parent_id=original_message.message_id
        )
    
    def _send_status_response(self, original_message: Message) -> None:
        """
        Send a status response to a message.
        
        Args:
            original_message: Original message requesting status
        """
        content = {
            "status": self._status.value,
            "message": self._status_message,
            "in_response_to": original_message.message_id
        }
        
        self.send_message(
            receiver=original_message.sender,
            message_type=MessageType.RESPONSE,
            content=content,
            parent_id=original_message.message_id
        )
    
    def _send_capabilities_response(self, original_message: Message) -> None:
        """
        Send a capabilities response to a message.
        
        Args:
            original_message: Original message requesting capabilities
        """
        content = {
            "capabilities": self.capabilities,
            "in_response_to": original_message.message_id
        }
        
        self.send_message(
            receiver=original_message.sender,
            message_type=MessageType.RESPONSE,
            content=content,
            parent_id=original_message.message_id
        )
    
    def _send_simple_response(
        self, 
        original_message: Message, 
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send a simple response to a message.
        
        Args:
            original_message: Original message to respond to
            message: Response message
            data: Additional data to include in the response
        """
        content = {
            "message": message,
            "in_response_to": original_message.message_id
        }
        
        if data:
            content.update(data)
        
        self.send_message(
            receiver=original_message.sender,
            message_type=MessageType.RESPONSE,
            content=content,
            parent_id=original_message.message_id
        )
    
    def start_listening(self) -> None:
        """Start listening for messages in a background thread."""
        if self._listening_thread and self._listening_thread.is_alive():
            logger.warning(f"Agent {self.agent_id} already listening")
            return
        
        self._stop_listening.clear()
        self._listening_thread = threading.Thread(
            target=self._listen_for_messages,
            daemon=True
        )
        self._listening_thread.start()
        logger.info(f"Agent {self.agent_id} started listening for messages")
    
    def stop_listening(self) -> None:
        """Stop listening for messages."""
        if not self._listening_thread:
            return
        
        self._stop_listening.set()
        if self._listening_thread.is_alive():
            self._listening_thread.join(timeout=1.0)
        
        self._listening_thread = None
        logger.info(f"Agent {self.agent_id} stopped listening for messages")
    
    def _listen_for_messages(self) -> None:
        """Background thread that listens for and processes messages."""
        self.status = AgentStatus.READY
        
        try:
            while not self._stop_listening.is_set():
                # Check for messages with a short timeout
                message = self.receive_message(timeout=1)
                if message:
                    # Set status to busy while processing
                    prev_status = self.status
                    self.status = AgentStatus.BUSY
                    
                    # Handle the message
                    self._handle_message(message)
                    
                    # Restore previous status
                    self.status = prev_status
                
                # Sleep to prevent CPU spinning
                time.sleep(0.01)
        except Exception as e:
            logger.error(f"Error in message listening thread: {e}")
            self.status = AgentStatus.ERROR
            self._status_message = str(e)
    
    def start(self) -> None:
        """Start the agent."""
        logger.info(f"Starting agent: {self.name} ({self.agent_id})")
        self.initialize()
        self.start_listening()
    
    def stop(self) -> None:
        """Stop the agent."""
        logger.info(f"Stopping agent: {self.name} ({self.agent_id})")
        self.status = AgentStatus.STOPPED
        self.stop_listening()
        self.cleanup()
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the agent (abstract method).
        
        This method should be overridden by subclasses to perform
        any necessary initialization before the agent starts listening.
        """
        pass
    
    @abstractmethod
    def handle_command(self, message: Message) -> None:
        """
        Handle command messages (abstract method).
        
        This method should be overridden by subclasses to handle
        command messages specific to the agent type.
        
        Args:
            message: Command message
        """
        pass
    
    def handle_status(self, message: Message) -> None:
        """
        Handle status messages.
        
        This method can be overridden by subclasses to handle
        status messages from other agents.
        
        Args:
            message: Status message
        """
        pass
    
    def cleanup(self) -> None:
        """
        Clean up resources before agent stops.
        
        This method can be overridden by subclasses to perform
        any necessary cleanup when the agent stops.
        """
        pass
