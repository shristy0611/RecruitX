"""Complex system emergent behavior detector."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from scipy.stats import entropy

from tests.complex_system.state_tracker import SystemState, AgentState

logger = logging.getLogger(__name__)

@dataclass
class EmergentBehavior:
    """Detected emergent behavior."""
    behavior_id: str
    type: str  # spatial, temporal, interaction, etc.
    description: str
    confidence: float
    agents_involved: List[str]
    timestamp: float
    metrics: Dict[str, Any]
    context: Dict[str, Any]

class EmergentDetector:
    """Detects emergent behaviors in complex systems."""
    
    def __init__(
        self,
        temporal_window: float = 300.0,  # 5 minute window
        min_confidence: float = 0.7,
        min_agents: int = 2,
        interaction_threshold: float = 0.5
    ):
        """Initialize the detector.
        
        Args:
            temporal_window: Time window for analysis
            min_confidence: Minimum confidence for detection
            min_agents: Minimum agents for pattern
            interaction_threshold: Threshold for interaction strength
        """
        self.temporal_window = temporal_window
        self.min_confidence = min_confidence
        self.min_agents = min_agents
        self.interaction_threshold = interaction_threshold
        
        # Detection history
        self.detected_behaviors: List[EmergentBehavior] = []
        self.behavior_counter = 0
        
        # Analysis state
        self.state_buffer: List[SystemState] = []
        self.interaction_graph: Dict[str, Dict[str, float]] = {}
        
    async def analyze_state(
        self,
        state: SystemState
    ) -> List[EmergentBehavior]:
        """Analyze system state for emergent behaviors.
        
        Args:
            state: Current system state
            
        Returns:
            List of detected behaviors
        """
        # Update state buffer
        self._update_buffer(state)
        
        # Detect behaviors
        behaviors = []
        
        # Spatial emergence
        spatial_behaviors = await self._detect_spatial_emergence()
        behaviors.extend(spatial_behaviors)
        
        # Temporal emergence
        temporal_behaviors = await self._detect_temporal_emergence()
        behaviors.extend(temporal_behaviors)
        
        # Interaction emergence
        interaction_behaviors = await self._detect_interaction_emergence()
        behaviors.extend(interaction_behaviors)
        
        # Metric emergence
        metric_behaviors = await self._detect_metric_emergence()
        behaviors.extend(metric_behaviors)
        
        # Filter and store behaviors
        new_behaviors = self._filter_behaviors(behaviors)
        self.detected_behaviors.extend(new_behaviors)
        
        return new_behaviors
        
    def _update_buffer(self, state: SystemState):
        """Update state buffer with new state.
        
        Args:
            state: New system state
        """
        # Add new state
        self.state_buffer.append(state)
        
        # Remove old states
        cutoff = time.time() - self.temporal_window
        self.state_buffer = [
            s for s in self.state_buffer
            if s.timestamp >= cutoff
        ]
        
        # Update interaction graph
        self._update_interaction_graph(state)
        
    def _update_interaction_graph(self, state: SystemState):
        """Update agent interaction graph.
        
        Args:
            state: Current system state
        """
        # Initialize new agents
        for agent_id in state.agents:
            if agent_id not in self.interaction_graph:
                self.interaction_graph[agent_id] = {}
                
        # Update interaction strengths
        for agent_id, agent in state.agents.items():
            for other_id, other in state.agents.items():
                if agent_id == other_id:
                    continue
                    
                # Calculate interaction strength
                strength = self._calculate_interaction_strength(
                    agent,
                    other,
                    state.global_metrics
                )
                
                # Update graph
                self.interaction_graph[agent_id][other_id] = strength
                
    def _calculate_interaction_strength(
        self,
        agent1: AgentState,
        agent2: AgentState,
        global_metrics: Dict[str, Any]
    ) -> float:
        """Calculate interaction strength between agents.
        
        Args:
            agent1: First agent
            agent2: Second agent
            global_metrics: Global system metrics
            
        Returns:
            Interaction strength [0, 1]
        """
        strength = 0.0
        factors = 0
        
        # Spatial proximity
        if agent1.position and agent2.position:
            distance = np.sqrt(
                (agent1.position['x'] - agent2.position['x']) ** 2 +
                (agent1.position['y'] - agent2.position['y']) ** 2 +
                (agent1.position.get('z', 0) - agent2.position.get('z', 0)) ** 2
            )
            
            # Normalize by global spread
            if 'spatial_distribution' in global_metrics:
                spread = global_metrics['spatial_distribution']['spread']
                max_spread = max(spread.values())
                if max_spread > 0:
                    strength += 1 - min(distance / max_spread, 1)
                    factors += 1
                    
        # Metric similarity
        common_metrics = set(agent1.metrics) & set(agent2.metrics)
        if common_metrics:
            similarities = []
            for metric in common_metrics:
                if isinstance(agent1.metrics[metric], (int, float)):
                    diff = abs(agent1.metrics[metric] - agent2.metrics[metric])
                    max_val = max(abs(agent1.metrics[metric]), abs(agent2.metrics[metric]))
                    if max_val > 0:
                        similarities.append(1 - min(diff / max_val, 1))
                        
            if similarities:
                strength += np.mean(similarities)
                factors += 1
                
        # Status alignment
        if agent1.status == agent2.status:
            strength += 1
            factors += 1
            
        return strength / max(factors, 1)
        
    async def _detect_spatial_emergence(self) -> List[EmergentBehavior]:
        """Detect spatially emergent behaviors.
        
        Returns:
            List of spatial behaviors
        """
        behaviors = []
        
        # Get latest state
        if not self.state_buffer:
            return behaviors
            
        state = self.state_buffer[-1]
        
        # Get agent positions
        positions = [
            (agent_id, agent.position)
            for agent_id, agent in state.agents.items()
            if agent.position is not None
        ]
        
        if len(positions) < self.min_agents:
            return behaviors
            
        # Convert to numpy array
        agent_ids = [p[0] for p in positions]
        X = np.array([
            [p[1]['x'], p[1]['y'], p[1].get('z', 0)]
            for p in positions
        ])
        
        # Normalize positions
        X = StandardScaler().fit_transform(X)
        
        # Detect clusters
        clustering = DBSCAN(eps=0.5, min_samples=self.min_agents).fit(X)
        labels = clustering.labels_
        
        # Analyze clusters
        unique_labels = set(labels)
        if -1 in unique_labels:
            unique_labels.remove(-1)
            
        for label in unique_labels:
            cluster_mask = labels == label
            cluster_agents = [
                agent_ids[i] for i in range(len(agent_ids))
                if cluster_mask[i]
            ]
            
            if len(cluster_agents) >= self.min_agents:
                # Calculate cluster metrics
                cluster_positions = X[cluster_mask]
                centroid = np.mean(cluster_positions, axis=0)
                spread = np.std(cluster_positions, axis=0)
                
                behaviors.append(EmergentBehavior(
                    behavior_id=f"spatial_{self.behavior_counter}",
                    type="spatial_clustering",
                    description=f"Detected spatial cluster of {len(cluster_agents)} agents",
                    confidence=0.8,
                    agents_involved=cluster_agents,
                    timestamp=time.time(),
                    metrics={
                        'centroid': centroid.tolist(),
                        'spread': spread.tolist(),
                        'size': len(cluster_agents)
                    },
                    context={
                        'global_metrics': state.global_metrics
                    }
                ))
                self.behavior_counter += 1
                
        return behaviors
        
    async def _detect_temporal_emergence(self) -> List[EmergentBehavior]:
        """Detect temporally emergent behaviors.
        
        Returns:
            List of temporal behaviors
        """
        behaviors = []
        
        if len(self.state_buffer) < 3:
            return behaviors
            
        # Analyze update patterns
        update_times = {}
        for state in self.state_buffer:
            for agent_id, agent in state.agents.items():
                if agent_id not in update_times:
                    update_times[agent_id] = []
                update_times[agent_id].append(agent.last_update)
                
        # Look for periodic updates
        for agent_id, times in update_times.items():
            if len(times) < 3:
                continue
                
            intervals = np.diff(times)
            mean_interval = np.mean(intervals)
            std_interval = np.std(intervals)
            
            if std_interval < 0.1 * mean_interval:
                behaviors.append(EmergentBehavior(
                    behavior_id=f"temporal_{self.behavior_counter}",
                    type="periodic_updates",
                    description=f"Agent {agent_id} shows periodic updates every {mean_interval:.2f}s",
                    confidence=0.9,
                    agents_involved=[agent_id],
                    timestamp=time.time(),
                    metrics={
                        'period': float(mean_interval),
                        'std_dev': float(std_interval)
                    },
                    context={
                        'update_times': times
                    }
                ))
                self.behavior_counter += 1
                
        # Look for synchronized updates
        if len(update_times) >= self.min_agents:
            # Calculate phase differences
            phase_diffs = {}
            for agent1 in update_times:
                for agent2 in update_times:
                    if agent1 >= agent2:
                        continue
                        
                    times1 = np.array(update_times[agent1])
                    times2 = np.array(update_times[agent2])
                    
                    # Calculate minimum time differences
                    diffs = []
                    for t1 in times1:
                        diff = np.min(np.abs(times2 - t1))
                        diffs.append(diff)
                        
                    mean_diff = np.mean(diffs)
                    if mean_diff < 0.1:  # 100ms threshold
                        phase_diffs[(agent1, agent2)] = mean_diff
                        
            # Find synchronized groups
            if phase_diffs:
                synced_agents = set()
                for (a1, a2), diff in phase_diffs.items():
                    synced_agents.add(a1)
                    synced_agents.add(a2)
                    
                if len(synced_agents) >= self.min_agents:
                    behaviors.append(EmergentBehavior(
                        behavior_id=f"temporal_{self.behavior_counter}",
                        type="synchronized_updates",
                        description=f"Detected synchronized updates among {len(synced_agents)} agents",
                        confidence=0.85,
                        agents_involved=list(synced_agents),
                        timestamp=time.time(),
                        metrics={
                            'mean_phase_diff': float(np.mean(list(phase_diffs.values()))),
                            'num_synced': len(synced_agents)
                        },
                        context={
                            'phase_differences': phase_diffs
                        }
                    ))
                    self.behavior_counter += 1
                    
        return behaviors
        
    async def _detect_interaction_emergence(self) -> List[EmergentBehavior]:
        """Detect interaction-based emergent behaviors.
        
        Returns:
            List of interaction behaviors
        """
        behaviors = []
        
        if len(self.interaction_graph) < self.min_agents:
            return behaviors
            
        # Convert graph to matrix
        agent_ids = sorted(self.interaction_graph.keys())
        n_agents = len(agent_ids)
        interaction_matrix = np.zeros((n_agents, n_agents))
        
        for i, agent1 in enumerate(agent_ids):
            for j, agent2 in enumerate(agent_ids):
                if agent1 in self.interaction_graph and agent2 in self.interaction_graph[agent1]:
                    interaction_matrix[i, j] = self.interaction_graph[agent1][agent2]
                    
        # Find strongly connected components
        strong_interactions = interaction_matrix >= self.interaction_threshold
        n_components, labels = connected_components(strong_interactions)
        
        # Analyze components
        for component in range(n_components):
            component_mask = labels == component
            component_agents = [
                agent_ids[i] for i in range(n_agents)
                if component_mask[i]
            ]
            
            if len(component_agents) >= self.min_agents:
                # Calculate component metrics
                component_strength = np.mean(
                    interaction_matrix[component_mask][:, component_mask]
                )
                
                behaviors.append(EmergentBehavior(
                    behavior_id=f"interaction_{self.behavior_counter}",
                    type="strong_interaction_group",
                    description=f"Detected strongly interacting group of {len(component_agents)} agents",
                    confidence=float(component_strength),
                    agents_involved=component_agents,
                    timestamp=time.time(),
                    metrics={
                        'group_size': len(component_agents),
                        'mean_strength': float(component_strength)
                    },
                    context={
                        'interaction_matrix': interaction_matrix[component_mask][:, component_mask].tolist()
                    }
                ))
                self.behavior_counter += 1
                
        return behaviors
        
    async def _detect_metric_emergence(self) -> List[EmergentBehavior]:
        """Detect metric-based emergent behaviors.
        
        Returns:
            List of metric behaviors
        """
        behaviors = []
        
        if not self.state_buffer:
            return behaviors
            
        state = self.state_buffer[-1]
        
        # Get all metrics
        all_metrics = set()
        for agent in state.agents.values():
            all_metrics.update(agent.metrics.keys())
            
        # Analyze each metric
        for metric in all_metrics:
            values = [
                (agent_id, agent.metrics[metric])
                for agent_id, agent in state.agents.items()
                if metric in agent.metrics and isinstance(agent.metrics[metric], (int, float))
            ]
            
            if len(values) < self.min_agents:
                continue
                
            agent_ids = [v[0] for v in values]
            metric_values = np.array([v[1] for v in values])
            
            # Check for clusters
            if len(metric_values) >= 5:
                X = metric_values.reshape(-1, 1)
                X = StandardScaler().fit_transform(X)
                
                clustering = DBSCAN(eps=0.5, min_samples=2).fit(X)
                labels = clustering.labels_
                
                # Analyze clusters
                unique_labels = set(labels)
                if -1 in unique_labels:
                    unique_labels.remove(-1)
                    
                if len(unique_labels) > 1:
                    behaviors.append(EmergentBehavior(
                        behavior_id=f"metric_{self.behavior_counter}",
                        type="metric_clustering",
                        description=f"Detected {len(unique_labels)} distinct clusters in metric {metric}",
                        confidence=0.75,
                        agents_involved=agent_ids,
                        timestamp=time.time(),
                        metrics={
                            'num_clusters': len(unique_labels),
                            'metric_name': metric,
                            'cluster_sizes': [
                                sum(1 for l in labels if l == label)
                                for label in unique_labels
                            ]
                        },
                        context={
                            'metric_values': metric_values.tolist(),
                            'cluster_labels': labels.tolist()
                        }
                    ))
                    self.behavior_counter += 1
                    
            # Check for convergence
            mean_value = np.mean(metric_values)
            std_value = np.std(metric_values)
            
            if std_value < 0.1 * abs(mean_value):
                behaviors.append(EmergentBehavior(
                    behavior_id=f"metric_{self.behavior_counter}",
                    type="metric_convergence",
                    description=f"Detected convergence in metric {metric}",
                    confidence=0.9,
                    agents_involved=agent_ids,
                    timestamp=time.time(),
                    metrics={
                        'metric_name': metric,
                        'mean_value': float(mean_value),
                        'std_value': float(std_value)
                    },
                    context={
                        'metric_values': metric_values.tolist()
                    }
                ))
                self.behavior_counter += 1
                
        return behaviors
        
    def _filter_behaviors(
        self,
        behaviors: List[EmergentBehavior]
    ) -> List[EmergentBehavior]:
        """Filter and deduplicate behaviors.
        
        Args:
            behaviors: List of detected behaviors
            
        Returns:
            Filtered behavior list
        """
        # Filter by confidence
        behaviors = [
            b for b in behaviors
            if b.confidence >= self.min_confidence
        ]
        
        # Sort by confidence
        behaviors.sort(key=lambda x: x.confidence, reverse=True)
        
        # Remove duplicates
        seen_patterns = set()
        filtered = []
        
        for behavior in behaviors:
            pattern_key = (
                behavior.type,
                tuple(sorted(behavior.agents_involved))
            )
            
            if pattern_key not in seen_patterns:
                filtered.append(behavior)
                seen_patterns.add(pattern_key)
                
        return filtered

def connected_components(matrix: np.ndarray) -> Tuple[int, np.ndarray]:
    """Find connected components in binary matrix.
    
    Args:
        matrix: Binary adjacency matrix
        
    Returns:
        Tuple of (number of components, component labels)
    """
    n = matrix.shape[0]
    labels = np.zeros(n, dtype=int)
    current_label = 0
    
    def dfs(node: int, label: int):
        labels[node] = label
        for neighbor in range(n):
            if matrix[node, neighbor] and labels[neighbor] == 0:
                dfs(neighbor, label)
                
    for node in range(n):
        if labels[node] == 0:
            current_label += 1
            dfs(node, current_label)
            
    return current_label, labels 