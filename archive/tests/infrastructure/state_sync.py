"""Test state synchronizer for handling distributed consensus."""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
import msgpack
import numpy as np

from .distributed_ledger import TestEvent, DistributedTestLedger
from .event_processor import TestEventProcessor

logger = logging.getLogger(__name__)

@dataclass
class StateSnapshot:
    """Snapshot of test state."""
    timestamp: float
    state: Dict[str, Any]
    node_id: str
    signature: str
    previous_hash: Optional[str] = None

class TestStateSynchronizer:
    """Synchronizes test state across distributed nodes."""
    
    def __init__(
        self,
        ledger: DistributedTestLedger,
        processor: TestEventProcessor,
        sync_interval: float = 1.0,
        max_snapshots: int = 100
    ):
        """Initialize the state synchronizer.
        
        Args:
            ledger: Distributed ledger instance
            processor: Event processor instance
            sync_interval: State sync interval (seconds)
            max_snapshots: Maximum snapshots to retain
        """
        self.ledger = ledger
        self.processor = processor
        self.sync_interval = sync_interval
        self.max_snapshots = max_snapshots
        self.snapshots: List[StateSnapshot] = []
        self.pending_snapshots: Dict[str, Set[StateSnapshot]] = {}
        self.sync_task = None
    
    async def start(self):
        """Start the state synchronizer."""
        self.sync_task = asyncio.create_task(self._sync_loop())
    
    async def stop(self):
        """Stop the state synchronizer."""
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass
    
    async def _sync_loop(self):
        """Main state sync loop."""
        while True:
            try:
                # Create state snapshot
                snapshot = await self._create_snapshot()
                
                # Broadcast snapshot
                await self._broadcast_snapshot(snapshot)
                
                # Process pending snapshots
                await self._process_pending_snapshots()
                
                # Prune old snapshots
                self._prune_snapshots()
                
                await asyncio.sleep(self.sync_interval)
                
            except Exception as e:
                logger.error(f"Error in sync loop: {str(e)}")
                await asyncio.sleep(1)
    
    async def _create_snapshot(self) -> StateSnapshot:
        """Create a state snapshot.
        
        Returns:
            New state snapshot
        """
        # Get current state
        state = await self._get_current_state()
        
        # Create snapshot
        snapshot = StateSnapshot(
            timestamp=time.time(),
            state=state,
            node_id=self.ledger.node_id,
            signature=self._sign_state(state),
            previous_hash=self._get_last_snapshot_hash()
        )
        
        return snapshot
    
    async def _get_current_state(self) -> Dict[str, Any]:
        """Get current test state.
        
        Returns:
            Dictionary containing current state
        """
        # Get recent events
        events = await self.ledger.get_events(
            start_time=time.time() - 60  # Last minute
        )
        
        # Calculate state metrics
        state = {
            'timestamp': time.time(),
            'event_count': len(events),
            'event_types': {},
            'agent_stats': {},
            'correlations': len(self.processor.correlations),
            'clusters': len(self.processor.event_clusters)
        }
        
        # Aggregate event types
        for event in events:
            if event.event_type not in state['event_types']:
                state['event_types'][event.event_type] = 0
            state['event_types'][event.event_type] += 1
        
        # Aggregate agent stats
        for event in events:
            if event.agent_id not in state['agent_stats']:
                state['agent_stats'][event.agent_id] = {
                    'events': 0,
                    'correlations': 0
                }
            state['agent_stats'][event.agent_id]['events'] += 1
        
        # Add correlation stats
        for correlation in self.processor.correlations:
            source_agent = None
            target_agent = None
            
            for event in events:
                if event.event_id == correlation.source_id:
                    source_agent = event.agent_id
                if event.event_id == correlation.target_id:
                    target_agent = event.agent_id
                if source_agent and target_agent:
                    break
            
            if source_agent in state['agent_stats']:
                state['agent_stats'][source_agent]['correlations'] += 1
            if target_agent in state['agent_stats']:
                state['agent_stats'][target_agent]['correlations'] += 1
        
        return state
    
    def _sign_state(self, state: Dict[str, Any]) -> str:
        """Sign state data.
        
        Args:
            state: State data to sign
            
        Returns:
            State signature
        """
        # Pack state data
        packed = msgpack.packb(state, use_bin_type=True)
        
        # Calculate signature
        import hashlib
        return hashlib.sha256(packed).hexdigest()
    
    def _get_last_snapshot_hash(self) -> Optional[str]:
        """Get hash of last snapshot.
        
        Returns:
            Hash of last snapshot or None
        """
        if not self.snapshots:
            return None
            
        # Pack snapshot data
        snapshot = self.snapshots[-1]
        snapshot_data = {
            'timestamp': snapshot.timestamp,
            'state': snapshot.state,
            'node_id': snapshot.node_id,
            'signature': snapshot.signature,
            'previous_hash': snapshot.previous_hash
        }
        packed = msgpack.packb(snapshot_data, use_bin_type=True)
        
        # Calculate hash
        import hashlib
        return hashlib.sha256(packed).hexdigest()
    
    async def _broadcast_snapshot(self, snapshot: StateSnapshot):
        """Broadcast snapshot to other nodes.
        
        Args:
            snapshot: Snapshot to broadcast
        """
        # Pack snapshot data
        snapshot_data = {
            'timestamp': snapshot.timestamp,
            'state': snapshot.state,
            'node_id': snapshot.node_id,
            'signature': snapshot.signature,
            'previous_hash': snapshot.previous_hash
        }
        
        # Broadcast via ledger
        await self.ledger.record_event(
            'state_snapshot',
            snapshot_data
        )
    
    async def _process_pending_snapshots(self):
        """Process pending snapshots."""
        # Group snapshots by timestamp
        timestamp_groups: Dict[float, List[StateSnapshot]] = {}
        
        for snapshots in self.pending_snapshots.values():
            for snapshot in snapshots:
                if snapshot.timestamp not in timestamp_groups:
                    timestamp_groups[snapshot.timestamp] = []
                timestamp_groups[snapshot.timestamp].append(snapshot)
        
        # Process each timestamp group
        for timestamp, snapshots in timestamp_groups.items():
            # Check if we have enough snapshots for consensus
            total_nodes = await self.ledger.redis.scard('nodes')
            if total_nodes == 0:
                continue
                
            consensus_threshold = total_nodes * 0.67
            if len(snapshots) >= consensus_threshold:
                # Merge states
                merged_state = self._merge_states(snapshots)
                
                # Create consensus snapshot
                consensus_snapshot = StateSnapshot(
                    timestamp=timestamp,
                    state=merged_state,
                    node_id='consensus',
                    signature=self._sign_state(merged_state),
                    previous_hash=self._get_last_snapshot_hash()
                )
                
                # Add to confirmed snapshots
                self.snapshots.append(consensus_snapshot)
                
                # Remove from pending
                for node_id in list(self.pending_snapshots.keys()):
                    self.pending_snapshots[node_id] = {
                        s for s in self.pending_snapshots[node_id]
                        if s.timestamp != timestamp
                    }
    
    def _merge_states(self, snapshots: List[StateSnapshot]) -> Dict[str, Any]:
        """Merge multiple state snapshots.
        
        Args:
            snapshots: List of snapshots to merge
            
        Returns:
            Merged state
        """
        # Extract states
        states = [s.state for s in snapshots]
        
        # Initialize merged state
        merged = {
            'timestamp': max(s['timestamp'] for s in states),
            'event_count': 0,
            'event_types': {},
            'agent_stats': {},
            'correlations': 0,
            'clusters': 0
        }
        
        # Merge event counts
        merged['event_count'] = int(np.mean([s['event_count'] for s in states]))
        
        # Merge event types
        event_types = set()
        for state in states:
            event_types.update(state['event_types'].keys())
            
        for event_type in event_types:
            counts = []
            for state in states:
                if event_type in state['event_types']:
                    counts.append(state['event_types'][event_type])
            merged['event_types'][event_type] = int(np.mean(counts))
        
        # Merge agent stats
        agents = set()
        for state in states:
            agents.update(state['agent_stats'].keys())
            
        for agent in agents:
            merged['agent_stats'][agent] = {
                'events': 0,
                'correlations': 0
            }
            
            event_counts = []
            correlation_counts = []
            
            for state in states:
                if agent in state['agent_stats']:
                    event_counts.append(
                        state['agent_stats'][agent]['events']
                    )
                    correlation_counts.append(
                        state['agent_stats'][agent]['correlations']
                    )
            
            if event_counts:
                merged['agent_stats'][agent]['events'] = int(np.mean(event_counts))
            if correlation_counts:
                merged['agent_stats'][agent]['correlations'] = int(np.mean(correlation_counts))
        
        # Merge correlation count
        merged['correlations'] = int(np.mean([s['correlations'] for s in states]))
        
        # Merge cluster count
        merged['clusters'] = int(np.mean([s['clusters'] for s in states]))
        
        return merged
    
    def _prune_snapshots(self):
        """Prune old snapshots."""
        if len(self.snapshots) > self.max_snapshots:
            # Keep most recent snapshots
            self.snapshots = self.snapshots[-self.max_snapshots:]
    
    async def get_state_history(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[StateSnapshot]:
        """Get state history.
        
        Args:
            start_time: Optional start timestamp
            end_time: Optional end timestamp
            
        Returns:
            List of state snapshots
        """
        snapshots = []
        
        for snapshot in self.snapshots:
            if start_time and snapshot.timestamp < start_time:
                continue
            if end_time and snapshot.timestamp > end_time:
                continue
            snapshots.append(snapshot)
            
        return snapshots
    
    async def get_latest_state(self) -> Optional[Dict[str, Any]]:
        """Get latest confirmed state.
        
        Returns:
            Latest state or None
        """
        if not self.snapshots:
            return None
        return self.snapshots[-1].state 