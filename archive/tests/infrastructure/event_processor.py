"""Test event processor for handling temporal uncertainty and event correlation."""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
from scipy import stats
from sklearn.cluster import DBSCAN

from .distributed_ledger import TestEvent, DistributedTestLedger

logger = logging.getLogger(__name__)

@dataclass
class EventCorrelation:
    """Correlation between test events."""
    source_id: str
    target_id: str
    correlation_type: str
    confidence: float
    temporal_distance: float
    metadata: Dict[str, Any]

class TestEventProcessor:
    """Processes test events with temporal uncertainty handling."""
    
    def __init__(
        self,
        ledger: DistributedTestLedger,
        temporal_window: float = 5.0,
        confidence_threshold: float = 0.8,
        max_correlations: int = 1000
    ):
        """Initialize the event processor.
        
        Args:
            ledger: Distributed ledger instance
            temporal_window: Time window for event correlation (seconds)
            confidence_threshold: Minimum confidence for correlations
            max_correlations: Maximum correlations to track
        """
        self.ledger = ledger
        self.temporal_window = temporal_window
        self.confidence_threshold = confidence_threshold
        self.max_correlations = max_correlations
        self.correlations: List[EventCorrelation] = []
        self.event_clusters: Dict[str, List[TestEvent]] = {}
        
    async def process_event(self, event: TestEvent):
        """Process a new test event.
        
        Args:
            event: Test event to process
        """
        # Get recent events for correlation
        recent_events = await self._get_recent_events(event.timestamp)
        
        # Handle temporal uncertainty
        adjusted_event = await self._handle_temporal_uncertainty(event, recent_events)
        
        # Find correlations
        correlations = await self._find_correlations(adjusted_event, recent_events)
        
        # Update clusters
        await self._update_clusters(adjusted_event, correlations)
        
        # Prune old correlations
        self._prune_correlations()
        
        return adjusted_event
    
    async def _get_recent_events(
        self,
        timestamp: float
    ) -> List[TestEvent]:
        """Get recent events within temporal window.
        
        Args:
            timestamp: Current timestamp
            
        Returns:
            List of recent events
        """
        start_time = timestamp - self.temporal_window
        return await self.ledger.get_events(start_time=start_time)
    
    async def _handle_temporal_uncertainty(
        self,
        event: TestEvent,
        recent_events: List[TestEvent]
    ) -> TestEvent:
        """Handle temporal uncertainty in event timing.
        
        Args:
            event: Event to process
            recent_events: Recent events for context
            
        Returns:
            Event with adjusted timestamp
        """
        if not recent_events:
            return event
            
        # Extract timestamps
        timestamps = [e.timestamp for e in recent_events]
        
        # Calculate temporal uncertainty
        uncertainty = self._calculate_temporal_uncertainty(
            event.timestamp,
            timestamps
        )
        
        # Adjust timestamp if needed
        if uncertainty > 0:
            adjusted_time = self._adjust_timestamp(
                event.timestamp,
                timestamps,
                uncertainty
            )
            event.data['original_timestamp'] = event.timestamp
            event.data['temporal_uncertainty'] = uncertainty
            event.timestamp = adjusted_time
            
        return event
    
    def _calculate_temporal_uncertainty(
        self,
        timestamp: float,
        reference_timestamps: List[float]
    ) -> float:
        """Calculate temporal uncertainty for a timestamp.
        
        Args:
            timestamp: Timestamp to analyze
            reference_timestamps: Reference timestamps
            
        Returns:
            Temporal uncertainty value
        """
        if not reference_timestamps:
            return 0.0
            
        # Calculate time differences
        diffs = np.array([abs(timestamp - t) for t in reference_timestamps])
        
        # Use kernel density estimation
        kde = stats.gaussian_kde(diffs)
        uncertainty = kde.evaluate(0)[0]
        
        return float(uncertainty)
    
    def _adjust_timestamp(
        self,
        timestamp: float,
        reference_timestamps: List[float],
        uncertainty: float
    ) -> float:
        """Adjust timestamp based on uncertainty.
        
        Args:
            timestamp: Timestamp to adjust
            reference_timestamps: Reference timestamps
            uncertainty: Temporal uncertainty value
            
        Returns:
            Adjusted timestamp
        """
        if not reference_timestamps:
            return timestamp
            
        # Find closest reference timestamp
        closest = min(reference_timestamps, key=lambda t: abs(t - timestamp))
        
        # Calculate adjustment
        adjustment = (closest - timestamp) * uncertainty
        
        return timestamp + adjustment
    
    async def _find_correlations(
        self,
        event: TestEvent,
        recent_events: List[TestEvent]
    ) -> List[EventCorrelation]:
        """Find correlations between events.
        
        Args:
            event: Event to analyze
            recent_events: Recent events to correlate with
            
        Returns:
            List of event correlations
        """
        correlations = []
        
        for target in recent_events:
            # Skip self-correlation
            if target.event_id == event.event_id:
                continue
                
            # Calculate correlation
            correlation = await self._correlate_events(event, target)
            
            # Add if confidence exceeds threshold
            if correlation and correlation.confidence >= self.confidence_threshold:
                correlations.append(correlation)
                self.correlations.append(correlation)
        
        return correlations
    
    async def _correlate_events(
        self,
        source: TestEvent,
        target: TestEvent
    ) -> Optional[EventCorrelation]:
        """Correlate two events.
        
        Args:
            source: Source event
            target: Target event
            
        Returns:
            EventCorrelation if correlated, None otherwise
        """
        try:
            # Calculate temporal distance
            temporal_dist = abs(source.timestamp - target.timestamp)
            
            # Skip if outside window
            if temporal_dist > self.temporal_window:
                return None
            
            # Calculate correlation metrics
            metrics = self._calculate_correlation_metrics(source, target)
            
            # Determine correlation type
            corr_type = self._determine_correlation_type(
                source,
                target,
                metrics
            )
            
            if corr_type:
                return EventCorrelation(
                    source_id=source.event_id,
                    target_id=target.event_id,
                    correlation_type=corr_type,
                    confidence=metrics['confidence'],
                    temporal_distance=temporal_dist,
                    metadata=metrics
                )
            
        except Exception as e:
            logger.error(f"Error correlating events: {str(e)}")
            
        return None
    
    def _calculate_correlation_metrics(
        self,
        source: TestEvent,
        target: TestEvent
    ) -> Dict[str, Any]:
        """Calculate correlation metrics between events.
        
        Args:
            source: Source event
            target: Target event
            
        Returns:
            Dictionary of correlation metrics
        """
        metrics = {}
        
        # Calculate temporal similarity
        temporal_sim = 1.0 / (1.0 + abs(source.timestamp - target.timestamp))
        metrics['temporal_similarity'] = temporal_sim
        
        # Calculate data similarity
        data_sim = self._calculate_data_similarity(source.data, target.data)
        metrics['data_similarity'] = data_sim
        
        # Calculate agent relationship
        agent_sim = 1.0 if source.agent_id == target.agent_id else 0.5
        metrics['agent_similarity'] = agent_sim
        
        # Calculate overall confidence
        metrics['confidence'] = (temporal_sim + data_sim + agent_sim) / 3.0
        
        return metrics
    
    def _calculate_data_similarity(
        self,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any]
    ) -> float:
        """Calculate similarity between event data.
        
        Args:
            source_data: Source event data
            target_data: Target event data
            
        Returns:
            Similarity score
        """
        # TODO: Implement more sophisticated similarity calculation
        common_keys = set(source_data.keys()) & set(target_data.keys())
        if not common_keys:
            return 0.0
            
        matches = sum(
            1 for k in common_keys
            if source_data[k] == target_data[k]
        )
        return matches / len(common_keys)
    
    def _determine_correlation_type(
        self,
        source: TestEvent,
        target: TestEvent,
        metrics: Dict[str, Any]
    ) -> Optional[str]:
        """Determine type of correlation between events.
        
        Args:
            source: Source event
            target: Target event
            metrics: Correlation metrics
            
        Returns:
            Correlation type if found, None otherwise
        """
        confidence = metrics['confidence']
        
        if confidence < self.confidence_threshold:
            return None
            
        if source.agent_id == target.agent_id:
            return 'same_agent'
            
        if source.event_type == target.event_type:
            return 'same_type'
            
        if metrics['temporal_similarity'] > 0.8:
            return 'temporal'
            
        if metrics['data_similarity'] > 0.8:
            return 'data'
            
        return 'weak'
    
    async def _update_clusters(
        self,
        event: TestEvent,
        correlations: List[EventCorrelation]
    ):
        """Update event clusters.
        
        Args:
            event: New event
            correlations: New correlations
        """
        # Extract features for clustering
        features = []
        events = []
        
        # Add new event
        features.append([
            event.timestamp,
            hash(event.event_type) % 1000,
            hash(event.agent_id) % 1000
        ])
        events.append(event)
        
        # Add correlated events
        for correlation in correlations:
            target = await self.ledger.get_event(correlation.target_id)
            if target:
                features.append([
                    target.timestamp,
                    hash(target.event_type) % 1000,
                    hash(target.agent_id) % 1000
                ])
                events.append(target)
        
        if not features:
            return
            
        # Perform clustering
        features = np.array(features)
        clusters = DBSCAN(
            eps=0.5,
            min_samples=2
        ).fit(features)
        
        # Update clusters
        for i, label in enumerate(clusters.labels_):
            if label >= 0:
                cluster_id = f"cluster_{label}"
                if cluster_id not in self.event_clusters:
                    self.event_clusters[cluster_id] = []
                self.event_clusters[cluster_id].append(events[i])
    
    def _prune_correlations(self):
        """Prune old correlations."""
        if len(self.correlations) > self.max_correlations:
            # Sort by confidence and keep top correlations
            self.correlations.sort(key=lambda c: c.confidence, reverse=True)
            self.correlations = self.correlations[:self.max_correlations]
    
    async def get_event_context(
        self,
        event_id: str
    ) -> Dict[str, Any]:
        """Get context for an event.
        
        Args:
            event_id: Event identifier
            
        Returns:
            Dictionary containing event context
        """
        event = await self.ledger.get_event(event_id)
        if not event:
            return {}
            
        # Get correlations
        correlations = [
            c for c in self.correlations
            if c.source_id == event_id or c.target_id == event_id
        ]
        
        # Get cluster
        cluster = None
        for cluster_id, events in self.event_clusters.items():
            if any(e.event_id == event_id for e in events):
                cluster = {
                    'id': cluster_id,
                    'size': len(events),
                    'events': [e.event_id for e in events]
                }
                break
        
        return {
            'event': event,
            'correlations': correlations,
            'cluster': cluster,
            'temporal_uncertainty': event.data.get('temporal_uncertainty')
        } 