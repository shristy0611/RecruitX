"""
Redis-based message broker for RecruitPro AI agent orchestration.

This module implements a privacy-first approach to agent communication
using Redis as the message broker. All data remains local to ensure privacy.
"""
import json
import logging
import os
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable

import redis

from src.utils.config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD

# Configure logging
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages that can be exchanged between agents."""
    COMMAND = "command"
    RESPONSE = "response"
    EVENT = "event"
    STATUS = "status"
    ERROR = "error"


class MessagePriority(Enum):
    """Priority levels for agent messages."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Message:
    """Message structure for agent communication."""
    
    def __init__(
        self,
        sender: str,
        receiver: str,
        message_type: MessageType,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        message_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        timestamp: Optional[str] = None,
    ):
        """
        Initialize a new message.
        
        Args:
            sender: ID of the sending agent
            receiver: ID of the receiving agent (or 'broadcast')
            message_type: Type of message
            content: Message payload
            priority: Message priority
            message_id: Unique message ID (generated if not provided)
            parent_id: ID of the parent message (for threaded conversations)
            timestamp: Message creation time (generated if not provided)
        """
        self.sender = sender
        self.receiver = receiver
        self.message_type = message_type if isinstance(message_type, MessageType) else MessageType(message_type)
        self.content = content
        self.priority = priority if isinstance(priority, MessagePriority) else MessagePriority(priority)
        self.message_id = message_id or str(uuid.uuid4())
        self.parent_id = parent_id
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type.value,
            "content": self.content,
            "priority": self.priority.value,
            "message_id": self.message_id,
            "parent_id": self.parent_id,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return cls(
            sender=data["sender"],
            receiver=data["receiver"],
            message_type=MessageType(data["message_type"]),
            content=data["content"],
            priority=MessagePriority(data["priority"]),
            message_id=data["message_id"],
            parent_id=data.get("parent_id"),
            timestamp=data["timestamp"],
        )
    
    def to_json(self) -> str:
        """Serialize message to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """Create message from JSON string."""
        return cls.from_dict(json.loads(json_str))


class MessageBroker:
    """
    Redis-based message broker for agent communication.
    
    This provides a privacy-first implementation where all data stays
    on the local system, ensuring sensitive information is not exposed.
    """
    
    def __init__(
        self,
        host: str = REDIS_HOST,
        port: int = REDIS_PORT,
        db: int = REDIS_DB,
        password: Optional[str] = REDIS_PASSWORD,
        queue_prefix: str = "recruitpro:queue:",
    ):
        """
        Initialize the message broker.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (if required)
            queue_prefix: Prefix for Redis queue keys
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.queue_prefix = queue_prefix
        
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,  # Always decode as strings
        )
        
        # Try to ping Redis to ensure connection works
        try:
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {host}:{port} (DB: {db})")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def get_queue_name(self, agent_id: str) -> str:
        """Get the Redis queue name for an agent."""
        return f"{self.queue_prefix}{agent_id}"
    
    def send_message(self, message: Message) -> bool:
        """
        Send a message to an agent's queue.
        
        Args:
            message: Message to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            queue_name = self.get_queue_name(message.receiver)
            # Use RPUSH to add message to the end of the list
            self.redis_client.rpush(queue_name, message.to_json())
            
            # Set expiry time (24 hours) if not already set
            if not self.redis_client.ttl(queue_name):
                self.redis_client.expire(queue_name, 86400)  # 24 hours
                
            logger.debug(f"Sent message to {message.receiver}: {message.message_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def receive_message(
        self, 
        agent_id: str, 
        timeout: int = 0,
        delete: bool = True
    ) -> Optional[Message]:
        """
        Receive a message from an agent's queue.
        
        Args:
            agent_id: ID of the receiving agent
            timeout: Time to wait for a message (0 = no wait)
            delete: Whether to remove the message from the queue
            
        Returns:
            Message object or None if no message available
        """
        try:
            queue_name = self.get_queue_name(agent_id)
            if delete:
                # Use BLPOP (blocking left pop) with timeout
                result = self.redis_client.blpop([queue_name], timeout=timeout)
                if result:
                    _, json_str = result
                    return Message.from_json(json_str)
            else:
                # Use LINDEX to peek at the first message without removing it
                json_str = self.redis_client.lindex(queue_name, 0)
                if json_str:
                    return Message.from_json(json_str)
            
            return None
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            return None
    
    def register_handler(
        self, 
        agent_id: str, 
        handler: Callable[[Message], None],
        polling_interval: float = 0.1,
        run_once: bool = False,
    ) -> None:
        """
        Register a message handler for an agent.
        
        Args:
            agent_id: ID of the receiving agent
            handler: Function to handle received messages
            polling_interval: Time between polling for messages
            run_once: Whether to handle just one message and return
        """
        queue_name = self.get_queue_name(agent_id)
        
        try:
            while True:
                # Use BLPOP (blocking left pop) with timeout
                result = self.redis_client.blpop([queue_name], timeout=polling_interval)
                if result:
                    _, json_str = result
                    message = Message.from_json(json_str)
                    handler(message)
                    
                    if run_once:
                        return
                
                # Small sleep to prevent CPU spinning
                if polling_interval > 0:
                    time.sleep(0.01)
        except KeyboardInterrupt:
            logger.info(f"Message handler for {agent_id} stopped")
        except Exception as e:
            logger.error(f"Error in message handler for {agent_id}: {e}")
    
    def broadcast_message(
        self, 
        sender: str, 
        receivers: List[str],
        message_type: MessageType,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> List[str]:
        """
        Broadcast a message to multiple agents.
        
        Args:
            sender: ID of the sending agent
            receivers: List of receiving agent IDs
            message_type: Type of message
            content: Message payload
            priority: Message priority
            
        Returns:
            List of successfully sent message IDs
        """
        message_ids = []
        parent_id = str(uuid.uuid4())  # Common parent ID for the broadcast
        
        for receiver in receivers:
            message = Message(
                sender=sender,
                receiver=receiver,
                message_type=message_type,
                content=content,
                priority=priority,
                parent_id=parent_id,
            )
            
            if self.send_message(message):
                message_ids.append(message.message_id)
        
        return message_ids
    
    def get_queue_length(self, agent_id: str) -> int:
        """
        Get the number of messages in an agent's queue.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Number of messages in queue
        """
        queue_name = self.get_queue_name(agent_id)
        return self.redis_client.llen(queue_name)
    
    def clear_queue(self, agent_id: str) -> int:
        """
        Clear all messages from an agent's queue.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Number of messages cleared
        """
        queue_name = self.get_queue_name(agent_id)
        queue_length = self.redis_client.llen(queue_name)
        self.redis_client.delete(queue_name)
        return queue_length
    
    def close(self) -> None:
        """Close the Redis connection."""
        self.redis_client.close()


# Singleton instance
_message_broker: Optional[MessageBroker] = None


def get_message_broker() -> MessageBroker:
    """
    Get or create the MessageBroker singleton instance.
    
    Returns:
        MessageBroker instance
    """
    global _message_broker
    if _message_broker is None:
        _message_broker = MessageBroker()
    return _message_broker
