"""Complex system state tracker for multi-agent testing."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
from scipy.stats import gaussian_kde

logger = logging.getLogger(__name__)

@dataclass
class AgentState:
    """State of an individual agent."""
    agent_id: str
    timestamp: float
    position: Optional[Dict[str, float]] = None  # x, y, z coordinates
    status: str = "active"  # active, idle, error
    metrics: Dict[str, Any] = field(default_factory=dict)
    last_update: float = field(default_factory=time.time)
    confidence: float = 1.0

@dataclass
class SystemState:
    """Overall system state across all agents."""
    timestamp: float
    agents: Dict[str, AgentState]
    global_metrics: Dict[str, Any]
    consensus_values: Dict[str, Any]
    emergent_patterns: List[Dict[str, Any]]

class ComplexStateTracker:
    """Tracks and analyzes complex system states."""
    
    def __init__(
        self,
        consensus_threshold: float = 0.67,  # 67% for consensus
        temporal_window: float = 30.0,  # 30 second window
        kde_bandwidth: float = 0.1  # For temporal density estimation
    ):
        """Initialize the state tracker.
        
        Args:
            consensus_threshold: Threshold for reaching consensus
            temporal_window: Time window for temporal analysis
            kde_bandwidth: Bandwidth for kernel density estimation
        """
        self.consensus_threshold = consensus_threshold
        self.temporal_window = temporal_window
        self.kde_bandwidth = kde_bandwidth
        
        # State storage
        self.current_state: Optional[SystemState] = None
        self.state_history: List[SystemState] = []
        self.agent_states: Dict[str, List[AgentState]] = {}
        
        # Temporal analysis
        self.temporal_events: List[Tuple[float, str, Any]] = []
        self.kde_models: Dict[str, gaussian_kde] = {}
        
    async def update_agent_state(
        self,
        agent_id: str,
        state: AgentState,
        require_consensus: bool = True
    ) -> bool:
        """Update the state of an individual agent.
        
        Args:
            agent_id: ID of the agent
            state: New state of the agent
            require_consensus: Whether to require consensus
            
        Returns:
            True if update was accepted
        """
        # Initialize agent history if needed
        if agent_id not in self.agent_states:
            self.agent_states[agent_id] = []
            
        # Check temporal consistency
        if not self._check_temporal_consistency(agent_id, state):
            logger.warning(f"Temporal inconsistency detected for agent {agent_id}")
            return False
            
        # Get consensus if required
        if require_consensus:
            consensus = await self._get_state_consensus(agent_id, state)
            if not consensus:
                logger.warning(f"Failed to reach consensus for agent {agent_id}")
                return False
                
        # Update state
        self.agent_states[agent_id].append(state)
        self._update_temporal_events(agent_id, state)
        self._update_system_state()
        
        return True
        
    def _check_temporal_consistency(
        self,
        agent_id: str,
        state: AgentState
    ) -> bool:
        """Check temporal consistency of state update.
        
        Args:
            agent_id: ID of the agent
            state: New state to check
            
        Returns:
            True if temporally consistent
        """
        if not self.agent_states.get(agent_id):
            return True
            
        last_state = self.agent_states[agent_id][-1]
        
        # Check for backwards time travel
        if state.timestamp < last_state.timestamp:
            return False
            
        # Check for unreasonable time jumps
        if state.timestamp - last_state.timestamp > self.temporal_window:
            return False
            
        # Use KDE to check if timestamp is within expected distribution
        if agent_id in self.kde_models:
            kde = self.kde_models[agent_id]
            prob = kde.evaluate([state.timestamp])[0]
            if prob < 0.01:  # Very unlikely timestamp
                return False
                
        return True
        
    async def _get_state_consensus(
        self,
        agent_id: str,
        state: AgentState
    ) -> bool:
        """Get consensus on state update from other agents.
        
        Args:
            agent_id: ID of the agent
            state: State to validate
            
        Returns:
            True if consensus reached
        """
        # TODO: Implement actual consensus mechanism
        # For now, always return True
        return True
        
    def _update_temporal_events(
        self,
        agent_id: str,
        state: AgentState
    ):
        """Update temporal events and KDE models.
        
        Args:
            agent_id: ID of the agent
            state: New state
        """
        # Add event
        self.temporal_events.append((
            state.timestamp,
            agent_id,
            state
        ))
        
        # Update KDE model
        if agent_id not in self.kde_models:
            timestamps = [state.timestamp]
            self.kde_models[agent_id] = gaussian_kde(
                timestamps,
                bw_method=self.kde_bandwidth
            )
        else:
            kde = self.kde_models[agent_id]
            timestamps = np.append(kde.dataset, [[state.timestamp]], axis=1)
            self.kde_models[agent_id].set_bandwidth(
                bw_method=self.kde_bandwidth
            )
            self.kde_models[agent_id].dataset = timestamps
            
    def _update_system_state(self):
        """Update overall system state."""
        if not self.agent_states:
            return
            
        # Get latest states
        current_agents = {
            agent_id: states[-1]
            for agent_id, states in self.agent_states.items()
        }
        
        # Calculate global metrics
        global_metrics = self._calculate_global_metrics(current_agents)
        
        # Get consensus values
        consensus_values = self._get_consensus_values(current_agents)
        
        # Detect emergent patterns
        emergent_patterns = self._detect_emergent_patterns(current_agents)
        
        # Create new system state
        self.current_state = SystemState(
            timestamp=time.time(),
            agents=current_agents,
            global_metrics=global_metrics,
            consensus_values=consensus_values,
            emergent_patterns=emergent_patterns
        )
        
        # Add to history
        self.state_history.append(self.current_state)
        
    def _calculate_global_metrics(
        self,
        agents: Dict[str, AgentState]
    ) -> Dict[str, Any]:
        """Calculate global system metrics.
        
        Args:
            agents: Current agent states
            
        Returns:
            Dictionary of global metrics
        """
        metrics = {
            'total_agents': len(agents),
            'active_agents': sum(1 for a in agents.values() if a.status == 'active'),
            'average_confidence': np.mean([a.confidence for a in agents.values()]),
            'state_update_rate': self._calculate_update_rate()
        }
        
        if any(a.position for a in agents.values()):
            metrics['spatial_distribution'] = self._calculate_spatial_distribution(agents)
            
        return metrics
        
    def _calculate_update_rate(self) -> float:
        """Calculate state update rate over temporal window.
        
        Returns:
            Updates per second
        """
        now = time.time()
        window_start = now - self.temporal_window
        
        recent_events = [
            e for e in self.temporal_events
            if e[0] >= window_start
        ]
        
        return len(recent_events) / self.temporal_window
        
    def _calculate_spatial_distribution(
        self,
        agents: Dict[str, AgentState]
    ) -> Dict[str, Any]:
        """Calculate spatial distribution metrics.
        
        Args:
            agents: Current agent states
            
        Returns:
            Dictionary of spatial metrics
        """
        positions = [
            a.position for a in agents.values()
            if a.position is not None
        ]
        
        if not positions:
            return {}
            
        x_coords = [p['x'] for p in positions]
        y_coords = [p['y'] for p in positions]
        z_coords = [p.get('z', 0) for p in positions]
        
        return {
            'centroid': {
                'x': np.mean(x_coords),
                'y': np.mean(y_coords),
                'z': np.mean(z_coords)
            },
            'spread': {
                'x': np.std(x_coords),
                'y': np.std(y_coords),
                'z': np.std(z_coords)
            }
        }
        
    def _get_consensus_values(
        self,
        agents: Dict[str, AgentState]
    ) -> Dict[str, Any]:
        """Get consensus values across agents.
        
        Args:
            agents: Current agent states
            
        Returns:
            Dictionary of consensus values
        """
        consensus = {}
        
        # Get all metric keys
        all_metrics = set()
        for agent in agents.values():
            all_metrics.update(agent.metrics.keys())
            
        # Find consensus for each metric
        for metric in all_metrics:
            values = [
                a.metrics[metric] for a in agents.values()
                if metric in a.metrics
            ]
            
            if not values:
                continue
                
            # Get most common value if enough agents agree
            value_counts = {}
            for v in values:
                value_counts[v] = value_counts.get(v, 0) + 1
                
            max_count = max(value_counts.values())
            if max_count / len(agents) >= self.consensus_threshold:
                consensus[metric] = max(
                    value_counts.items(),
                    key=lambda x: x[1]
                )[0]
                
        return consensus
        
    def _detect_emergent_patterns(
        self,
        agents: Dict[str, AgentState]
    ) -> List[Dict[str, Any]]:
        """Detect emergent patterns in agent behavior.
        
        Args:
            agents: Current agent states
            
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Detect spatial clusters
        if any(a.position for a in agents.values()):
            spatial_patterns = self._detect_spatial_patterns(agents)
            patterns.extend(spatial_patterns)
            
        # Detect temporal patterns
        temporal_patterns = self._detect_temporal_patterns()
        patterns.extend(temporal_patterns)
        
        # Detect metric patterns
        metric_patterns = self._detect_metric_patterns(agents)
        patterns.extend(metric_patterns)
        
        return patterns
        
    def _detect_spatial_patterns(
        self,
        agents: Dict[str, AgentState]
    ) -> List[Dict[str, Any]]:
        """Detect spatial patterns in agent positions.
        
        Args:
            agents: Current agent states
            
        Returns:
            List of spatial patterns
        """
        patterns = []
        
        positions = [
            (a.position['x'], a.position['y'], a.position.get('z', 0))
            for a in agents.values()
            if a.position is not None
        ]
        
        if len(positions) < 3:
            return patterns
            
        # Convert to numpy array
        X = np.array(positions)
        
        # Look for clusters
        from sklearn.cluster import DBSCAN
        clustering = DBSCAN(eps=0.5, min_samples=2).fit(X)
        
        # Analyze clusters
        labels = clustering.labels_
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        if n_clusters > 0:
            patterns.append({
                'type': 'spatial_clustering',
                'n_clusters': n_clusters,
                'description': f"Found {n_clusters} spatial agent clusters",
                'confidence': 0.8
            })
            
        return patterns
        
    def _detect_temporal_patterns(self) -> List[Dict[str, Any]]:
        """Detect temporal patterns in state updates.
        
        Returns:
            List of temporal patterns
        """
        patterns = []
        
        # Get recent events
        now = time.time()
        window_start = now - self.temporal_window
        recent_events = [
            e for e in self.temporal_events
            if e[0] >= window_start
        ]
        
        if len(recent_events) < 3:
            return patterns
            
        # Look for periodic updates
        timestamps = [e[0] for e in recent_events]
        intervals = np.diff(timestamps)
        
        # Check for consistent intervals
        if np.std(intervals) < 0.1 * np.mean(intervals):
            patterns.append({
                'type': 'periodic_updates',
                'period': float(np.mean(intervals)),
                'description': f"Detected periodic state updates every {np.mean(intervals):.2f} seconds",
                'confidence': 0.9
            })
            
        return patterns
        
    def _detect_metric_patterns(
        self,
        agents: Dict[str, AgentState]
    ) -> List[Dict[str, Any]]:
        """Detect patterns in agent metrics.
        
        Args:
            agents: Current agent states
            
        Returns:
            List of metric patterns
        """
        patterns = []
        
        # Get all metric keys
        all_metrics = set()
        for agent in agents.values():
            all_metrics.update(agent.metrics.keys())
            
        # Analyze each metric
        for metric in all_metrics:
            values = [
                a.metrics[metric] for a in agents.values()
                if metric in a.metrics
            ]
            
            if not values or not isinstance(values[0], (int, float)):
                continue
                
            # Look for unusual distributions
            mean = np.mean(values)
            std = np.std(values)
            
            if std > 2 * mean:
                patterns.append({
                    'type': 'metric_variance',
                    'metric': metric,
                    'description': f"High variance detected in {metric}",
                    'confidence': 0.7,
                    'stats': {
                        'mean': float(mean),
                        'std': float(std)
                    }
                })
                
        return patterns 