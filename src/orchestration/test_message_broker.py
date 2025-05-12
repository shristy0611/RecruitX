"""
Test script for the Redis-based message broker.

This script demonstrates how to use the MessageBroker for agent communication
and verifies that it's working correctly with Redis.
"""
import logging
import time
from typing import Dict, Any

from src.orchestration.message_broker import (
    Message,
    MessageType,
    MessagePriority,
    get_message_broker
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_message_broker():
    """Test basic message broker functionality."""
    logger.info("Testing message broker...")
    
    # Get message broker instance
    broker = get_message_broker()
    
    # Create test agents
    sender_id = "test_sender"
    receiver_id = "test_receiver"
    
    # Test message creation
    message = Message(
        sender=sender_id,
        receiver=receiver_id,
        message_type=MessageType.COMMAND,
        content={"command": "test", "params": {"key": "value"}},
        priority=MessagePriority.NORMAL
    )
    
    logger.info(f"Created message: {message.message_id}")
    
    # Test sending message
    success = broker.send_message(message)
    logger.info(f"Message sent: {success}")
    
    # Test receiving message
    received_message = broker.receive_message(receiver_id, timeout=5)
    
    if received_message:
        logger.info(f"Received message: {received_message.message_id}")
        logger.info(f"Message content: {received_message.content}")
        assert received_message.message_id == message.message_id
        logger.info("✅ Message broker test passed!")
    else:
        logger.error("❌ Failed to receive message!")
        return False
    
    # Test message handler
    def message_handler(msg: Message) -> None:
        logger.info(f"Handler received message: {msg.message_id}")
        logger.info(f"Message content: {msg.content}")
    
    # Send another message
    another_message = Message(
        sender=sender_id,
        receiver=receiver_id,
        message_type=MessageType.EVENT,
        content={"event": "test_event", "data": {"test": True}},
    )
    
    broker.send_message(another_message)
    
    # Test broadcast
    receivers = [f"broadcast_test_{i}" for i in range(3)]
    message_ids = broker.broadcast_message(
        sender=sender_id,
        receivers=receivers,
        message_type=MessageType.STATUS,
        content={"status": "ready"}
    )
    
    logger.info(f"Broadcast sent: {len(message_ids)} messages")
    
    # Check broadcast messages were received
    for i, receiver in enumerate(receivers):
        msg = broker.receive_message(receiver, timeout=1)
        if msg:
            logger.info(f"Receiver {i} got broadcast: {msg.content}")
        else:
            logger.error(f"Receiver {i} did not receive broadcast!")
    
    # Clean up test queues
    broker.clear_queue(receiver_id)
    for receiver in receivers:
        broker.clear_queue(receiver)
    
    return True


if __name__ == "__main__":
    test_message_broker()
