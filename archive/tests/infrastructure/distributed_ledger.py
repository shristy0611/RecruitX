"""Distributed ledger for test result tracking and validation."""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import aioredis
import msgpack

logger = logging.getLogger(__name__)

@dataclass
class TestEvent:
    """Test event data structure."""
    event_id: str
    agent_id: str
    timestamp: float
    event_type: str
    data: Dict[str, Any]
    previous_hash: Optional[str] = None
    consensus_timestamp: Optional[float] = None
    signatures: Set[str] = None

class DistributedTestLedger:
    """Distributed ledger for test result tracking with consensus validation."""
    
    def __init__(
        self,
        node_id: str,
        redis_url: str = "redis://localhost:6379",
        consensus_threshold: float = 0.67
    ):
        """Initialize the distributed ledger.
        
        Args:
            node_id: Unique identifier for this ledger node
            redis_url: URL for Redis connection
            consensus_threshold: Required ratio of nodes for consensus
        """
        self.node_id = node_id
        self.redis_url = redis_url
        self.consensus_threshold = consensus_threshold
        self.events: List[TestEvent] = []
        self.pending_events: Dict[str, TestEvent] = {}
        self.consensus_cache: Dict[str, Set[str]] = {}
        self.redis = None
        self.event_channel = None
        self.consensus_channel = None
    
    async def start(self):
        """Start the ledger node."""
        self.redis = await aioredis.create_redis_pool(self.redis_url)
        
        # Subscribe to event and consensus channels
        self.event_channel = (await self.redis.subscribe('test_events'))[0]
        self.consensus_channel = (await self.redis.subscribe('consensus'))[0]
        
        # Start background tasks
        asyncio.create_task(self._process_events())
        asyncio.create_task(self._process_consensus())
    
    async def stop(self):
        """Stop the ledger node."""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
    
    async def record_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """Record a new test event.
        
        Args:
            event_type: Type of test event
            data: Event data
            
        Returns:
            Event ID
        """
        # Create event
        event = TestEvent(
            event_id=self._generate_event_id(),
            agent_id=self.node_id,
            timestamp=time.time(),
            event_type=event_type,
            data=data,
            previous_hash=self._get_last_hash(),
            signatures={self.node_id}
        )
        
        # Add to pending events
        self.pending_events[event.event_id] = event
        
        # Broadcast event
        await self._broadcast_event(event)
        
        return event.event_id
    
    async def get_event(self, event_id: str) -> Optional[TestEvent]:
        """Get an event by ID.
        
        Args:
            event_id: Event identifier
            
        Returns:
            TestEvent if found, None otherwise
        """
        # Check confirmed events
        for event in self.events:
            if event.event_id == event_id:
                return event
        
        # Check pending events
        return self.pending_events.get(event_id)
    
    async def get_events(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        event_type: Optional[str] = None
    ) -> List[TestEvent]:
        """Get events matching criteria.
        
        Args:
            start_time: Optional start timestamp
            end_time: Optional end timestamp
            event_type: Optional event type filter
            
        Returns:
            List of matching events
        """
        events = []
        
        for event in self.events:
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            if event_type and event.event_type != event_type:
                continue
            events.append(event)
            
        return events
    
    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        timestamp = str(time.time_ns())
        node_id = self.node_id
        random = hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]
        return f"{timestamp}-{node_id}-{random}"
    
    def _get_last_hash(self) -> Optional[str]:
        """Get hash of last confirmed event."""
        if not self.events:
            return None
        return self._hash_event(self.events[-1])
    
    def _hash_event(self, event: TestEvent) -> str:
        """Generate hash for an event.
        
        Args:
            event: Event to hash
            
        Returns:
            Event hash
        """
        event_data = {
            'event_id': event.event_id,
            'agent_id': event.agent_id,
            'timestamp': event.timestamp,
            'event_type': event.event_type,
            'data': event.data,
            'previous_hash': event.previous_hash
        }
        return hashlib.sha256(
            msgpack.packb(event_data, use_bin_type=True)
        ).hexdigest()
    
    async def _broadcast_event(self, event: TestEvent):
        """Broadcast event to other nodes.
        
        Args:
            event: Event to broadcast
        """
        event_data = {
            'event_id': event.event_id,
            'agent_id': event.agent_id,
            'timestamp': event.timestamp,
            'event_type': event.event_type,
            'data': event.data,
            'previous_hash': event.previous_hash,
            'signatures': list(event.signatures)
        }
        await self.redis.publish('test_events', json.dumps(event_data))
    
    async def _process_events(self):
        """Process incoming events from other nodes."""
        while True:
            try:
                message = await self.event_channel.get()
                if message:
                    event_data = json.loads(message)
                    
                    # Create event object
                    event = TestEvent(
                        event_id=event_data['event_id'],
                        agent_id=event_data['agent_id'],
                        timestamp=event_data['timestamp'],
                        event_type=event_data['event_type'],
                        data=event_data['data'],
                        previous_hash=event_data['previous_hash'],
                        signatures=set(event_data['signatures'])
                    )
                    
                    # Validate event
                    if self._validate_event(event):
                        # Add signature
                        event.signatures.add(self.node_id)
                        
                        # Add to pending events
                        self.pending_events[event.event_id] = event
                        
                        # Broadcast with our signature
                        await self._broadcast_event(event)
                        
                        # Check for consensus
                        await self._check_consensus(event)
                    
            except Exception as e:
                logger.error(f"Error processing event: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_consensus(self):
        """Process consensus messages."""
        while True:
            try:
                message = await self.consensus_channel.get()
                if message:
                    consensus_data = json.loads(message)
                    event_id = consensus_data['event_id']
                    consensus_time = consensus_data['timestamp']
                    
                    if event_id in self.pending_events:
                        event = self.pending_events[event_id]
                        event.consensus_timestamp = consensus_time
                        
                        # Move to confirmed events
                        self.events.append(event)
                        del self.pending_events[event_id]
                        
                        # Clean up consensus cache
                        if event_id in self.consensus_cache:
                            del self.consensus_cache[event_id]
                    
            except Exception as e:
                logger.error(f"Error processing consensus: {str(e)}")
                await asyncio.sleep(1)
    
    def _validate_event(self, event: TestEvent) -> bool:
        """Validate an event.
        
        Args:
            event: Event to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check previous hash
            if event.previous_hash != self._get_last_hash():
                return False
            
            # Validate data schema
            if not self._validate_data_schema(event.event_type, event.data):
                return False
            
            # Additional validation logic here
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating event: {str(e)}")
            return False
    
    def _validate_data_schema(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Validate event data schema.
        
        Args:
            event_type: Event type
            data: Event data
            
        Returns:
            True if valid, False otherwise
        """
        # TODO: Implement schema validation
        return True
    
    async def _check_consensus(self, event: TestEvent):
        """Check for consensus on an event.
        
        Args:
            event: Event to check
        """
        # Get total nodes
        total_nodes = await self.redis.scard('nodes')
        if total_nodes == 0:
            return
        
        # Check signatures
        signature_ratio = len(event.signatures) / total_nodes
        if signature_ratio >= self.consensus_threshold:
            # Broadcast consensus achievement
            consensus_data = {
                'event_id': event.event_id,
                'timestamp': time.time()
            }
            await self.redis.publish('consensus', json.dumps(consensus_data))
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get ledger statistics.
        
        Returns:
            Dictionary containing statistics
        """
        return {
            'total_events': len(self.events),
            'pending_events': len(self.pending_events),
            'last_consensus_time': self.events[-1].consensus_timestamp if self.events else None,
            'node_count': await self.redis.scard('nodes')
        } 