"""Enhanced analytics for multi-agent testing performance."""

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
from sklearn.metrics import silhouette_score
import pandas as pd
from scipy.stats import entropy

from tests.complex_system.state_tracker import SystemState, AgentState
from tests.complex_system.emergent_detector import EmergentBehavior
from tests.ai_pipeline.test_generator import GeneratedTest
from tests.ai_pipeline.test_executor import TestResult

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for analysis."""
    timestamp: float
    agent_metrics: Dict[str, Dict[str, float]]
    system_metrics: Dict[str, float]
    test_metrics: Dict[str, float]
    behavior_metrics: Dict[str, float]

@dataclass
class PerformanceInsight:
    """Performance insight from analysis."""
    category: str
    description: str
    severity: str  # 'low', 'medium', 'high'
    confidence: float
    metrics: Dict[str, Any]
    recommendations: List[str]
    timestamp: float

class PerformanceAnalyzer:
    """Analyzes multi-agent testing performance."""
    
    def __init__(
        self,
        metrics_window: float = 3600.0,  # 1 hour window
        min_confidence: float = 0.7,
        anomaly_threshold: float = 2.0  # Standard deviations
    ):
        """Initialize the analyzer.
        
        Args:
            metrics_window: Time window for metrics
            min_confidence: Minimum confidence for insights
            anomaly_threshold: Threshold for anomaly detection
        """
        self.metrics_window = metrics_window
        self.min_confidence = min_confidence
        self.anomaly_threshold = anomaly_threshold
        
        # Metrics storage
        self.metrics_history: List[PerformanceMetrics] = []
        self.insights: List[PerformanceInsight] = []
        
        # Analysis state
        self.baseline_metrics: Optional[Dict[str, float]] = None
        self.trend_models: Dict[str, Any] = {}
        
    async def analyze_performance(
        self,
        system_state: SystemState,
        test_results: List[TestResult],
        behaviors: List[EmergentBehavior]
    ) -> List[PerformanceInsight]:
        """Analyze system performance.
        
        Args:
            system_state: Current system state
            test_results: Recent test results
            behaviors: Detected behaviors
            
        Returns:
            List of performance insights
        """
        # Calculate current metrics
        metrics = self._calculate_metrics(
            system_state,
            test_results,
            behaviors
        )
        
        # Update history
        self._update_history(metrics)
        
        # Generate insights
        insights = []
        
        # Performance analysis
        perf_insights = self._analyze_performance_patterns(metrics)
        insights.extend(perf_insights)
        
        # Resource analysis
        resource_insights = self._analyze_resource_usage(metrics)
        insights.extend(resource_insights)
        
        # Test analysis
        test_insights = self._analyze_test_patterns(metrics)
        insights.extend(test_insights)
        
        # Behavior analysis
        behavior_insights = self._analyze_behavior_patterns(metrics)
        insights.extend(behavior_insights)
        
        # Filter and store insights
        new_insights = self._filter_insights(insights)
        self.insights.extend(new_insights)
        
        return new_insights
        
    def _calculate_metrics(
        self,
        system_state: SystemState,
        test_results: List[TestResult],
        behaviors: List[EmergentBehavior]
    ) -> PerformanceMetrics:
        """Calculate current performance metrics.
        
        Args:
            system_state: Current system state
            test_results: Recent test results
            behaviors: Detected behaviors
            
        Returns:
            Performance metrics
        """
        # Calculate agent metrics
        agent_metrics = {}
        for agent_id, agent in system_state.agents.items():
            agent_metrics[agent_id] = {
                'update_rate': self._calculate_update_rate(agent),
                'confidence': agent.confidence,
                'test_success_rate': self._calculate_agent_success_rate(
                    agent_id,
                    test_results
                )
            }
            
        # Calculate system metrics
        system_metrics = {
            'total_agents': len(system_state.agents),
            'active_agents': sum(1 for a in system_state.agents.values() if a.status == 'active'),
            'message_rate': self._calculate_message_rate(system_state),
            'consensus_rate': self._calculate_consensus_rate(system_state)
        }
        
        # Calculate test metrics
        test_metrics = {
            'total_tests': len(test_results),
            'success_rate': self._calculate_success_rate(test_results),
            'average_duration': np.mean([r.duration for r in test_results]) if test_results else 0,
            'error_rate': self._calculate_error_rate(test_results)
        }
        
        # Calculate behavior metrics
        behavior_metrics = {
            'total_behaviors': len(behaviors),
            'average_confidence': np.mean([b.confidence for b in behaviors]) if behaviors else 0,
            'behavior_diversity': self._calculate_behavior_diversity(behaviors)
        }
        
        return PerformanceMetrics(
            timestamp=time.time(),
            agent_metrics=agent_metrics,
            system_metrics=system_metrics,
            test_metrics=test_metrics,
            behavior_metrics=behavior_metrics
        )
        
    def _calculate_update_rate(self, agent: AgentState) -> float:
        """Calculate agent update rate.
        
        Args:
            agent: Agent state
            
        Returns:
            Updates per second
        """
        if not hasattr(agent, 'last_update'):
            return 0.0
            
        window = 60.0  # 1 minute window
        now = time.time()
        
        # Get recent metrics
        recent_metrics = [
            m for m in self.metrics_history
            if now - m.timestamp <= window and agent.agent_id in m.agent_metrics
        ]
        
        if not recent_metrics:
            return 0.0
            
        return len(recent_metrics) / window
        
    def _calculate_agent_success_rate(
        self,
        agent_id: str,
        test_results: List[TestResult]
    ) -> float:
        """Calculate agent test success rate.
        
        Args:
            agent_id: Agent identifier
            test_results: Test results
            
        Returns:
            Success rate [0, 1]
        """
        agent_results = [
            r for r in test_results
            if r.test_id.startswith(f"test_{agent_id}")
        ]
        
        if not agent_results:
            return 1.0
            
        return sum(1 for r in agent_results if r.success) / len(agent_results)
        
    def _calculate_message_rate(self, system_state: SystemState) -> float:
        """Calculate system message rate.
        
        Args:
            system_state: System state
            
        Returns:
            Messages per second
        """
        window = 60.0  # 1 minute window
        now = time.time()
        
        # Get recent metrics
        recent_metrics = [
            m for m in self.metrics_history
            if now - m.timestamp <= window
        ]
        
        if not recent_metrics:
            return 0.0
            
        message_counts = [
            m.system_metrics.get('message_count', 0)
            for m in recent_metrics
        ]
        
        return np.mean(message_counts) / window
        
    def _calculate_consensus_rate(self, system_state: SystemState) -> float:
        """Calculate system consensus rate.
        
        Args:
            system_state: System state
            
        Returns:
            Consensus rate [0, 1]
        """
        if not system_state.consensus_values:
            return 0.0
            
        total_metrics = set()
        for agent in system_state.agents.values():
            total_metrics.update(agent.metrics.keys())
            
        if not total_metrics:
            return 1.0
            
        return len(system_state.consensus_values) / len(total_metrics)
        
    def _calculate_success_rate(self, test_results: List[TestResult]) -> float:
        """Calculate overall test success rate.
        
        Args:
            test_results: Test results
            
        Returns:
            Success rate [0, 1]
        """
        if not test_results:
            return 1.0
            
        return sum(1 for r in test_results if r.success) / len(test_results)
        
    def _calculate_error_rate(self, test_results: List[TestResult]) -> float:
        """Calculate test error rate.
        
        Args:
            test_results: Test results
            
        Returns:
            Error rate [0, 1]
        """
        if not test_results:
            return 0.0
            
        return sum(1 for r in test_results if r.error) / len(test_results)
        
    def _calculate_behavior_diversity(
        self,
        behaviors: List[EmergentBehavior]
    ) -> float:
        """Calculate behavior diversity.
        
        Args:
            behaviors: Detected behaviors
            
        Returns:
            Diversity score [0, 1]
        """
        if not behaviors:
            return 0.0
            
        # Count behavior types
        type_counts = {}
        for behavior in behaviors:
            type_counts[behavior.type] = type_counts.get(behavior.type, 0) + 1
            
        # Calculate entropy
        total = len(behaviors)
        probabilities = [count / total for count in type_counts.values()]
        
        return entropy(probabilities)
        
    def _update_history(self, metrics: PerformanceMetrics):
        """Update metrics history.
        
        Args:
            metrics: New metrics
        """
        self.metrics_history.append(metrics)
        
        # Remove old metrics
        cutoff = time.time() - self.metrics_window
        self.metrics_history = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff
        ]
        
        # Update baseline if needed
        if not self.baseline_metrics:
            self.baseline_metrics = self._calculate_baseline()
            
    def _calculate_baseline(self) -> Dict[str, float]:
        """Calculate baseline metrics.
        
        Returns:
            Dictionary of baseline values
        """
        if not self.metrics_history:
            return {}
            
        # Get all metric keys
        metric_keys = set()
        for metrics in self.metrics_history:
            metric_keys.update(metrics.system_metrics.keys())
            metric_keys.update(metrics.test_metrics.keys())
            metric_keys.update(metrics.behavior_metrics.keys())
            
        # Calculate baselines
        baselines = {}
        for key in metric_keys:
            values = []
            for metrics in self.metrics_history:
                if key in metrics.system_metrics:
                    values.append(metrics.system_metrics[key])
                elif key in metrics.test_metrics:
                    values.append(metrics.test_metrics[key])
                elif key in metrics.behavior_metrics:
                    values.append(metrics.behavior_metrics[key])
                    
            if values:
                baselines[key] = np.mean(values)
                
        return baselines
        
    def _analyze_performance_patterns(
        self,
        metrics: PerformanceMetrics
    ) -> List[PerformanceInsight]:
        """Analyze performance patterns.
        
        Args:
            metrics: Current metrics
            
        Returns:
            List of insights
        """
        insights = []
        
        # Check for performance anomalies
        if self.baseline_metrics:
            for key, value in metrics.system_metrics.items():
                if key not in self.baseline_metrics:
                    continue
                    
                baseline = self.baseline_metrics[key]
                if baseline == 0:
                    continue
                    
                deviation = abs(value - baseline) / baseline
                if deviation > self.anomaly_threshold:
                    insights.append(PerformanceInsight(
                        category='performance',
                        description=f"Anomaly detected in {key}",
                        severity='high',
                        confidence=min(1.0, deviation / self.anomaly_threshold),
                        metrics={
                            'metric': key,
                            'value': value,
                            'baseline': baseline,
                            'deviation': deviation
                        },
                        recommendations=[
                            f"Investigate cause of {key} anomaly",
                            "Check system logs for errors",
                            "Review recent configuration changes"
                        ],
                        timestamp=time.time()
                    ))
                    
        # Check for performance trends
        for key in metrics.system_metrics:
            trend = self._analyze_metric_trend(key)
            if trend:
                insights.append(trend)
                
        return insights
        
    def _analyze_resource_usage(
        self,
        metrics: PerformanceMetrics
    ) -> List[PerformanceInsight]:
        """Analyze resource usage patterns.
        
        Args:
            metrics: Current metrics
            
        Returns:
            List of insights
        """
        insights = []
        
        # Check agent utilization
        active_ratio = metrics.system_metrics['active_agents'] / metrics.system_metrics['total_agents']
        if active_ratio < 0.5:
            insights.append(PerformanceInsight(
                category='resource',
                description="Low agent utilization detected",
                severity='medium',
                confidence=0.8,
                metrics={
                    'active_ratio': active_ratio,
                    'active_agents': metrics.system_metrics['active_agents'],
                    'total_agents': metrics.system_metrics['total_agents']
                },
                recommendations=[
                    "Consider reducing number of agents",
                    "Check for agent initialization issues",
                    "Review agent activation thresholds"
                ],
                timestamp=time.time()
            ))
            
        # Check message rate
        if metrics.system_metrics['message_rate'] > 100:  # High message rate threshold
            insights.append(PerformanceInsight(
                category='resource',
                description="High message rate detected",
                severity='medium',
                confidence=0.9,
                metrics={
                    'message_rate': metrics.system_metrics['message_rate']
                },
                recommendations=[
                    "Consider message batching",
                    "Review message filtering rules",
                    "Check for message loops"
                ],
                timestamp=time.time()
            ))
            
        return insights
        
    def _analyze_test_patterns(
        self,
        metrics: PerformanceMetrics
    ) -> List[PerformanceInsight]:
        """Analyze test execution patterns.
        
        Args:
            metrics: Current metrics
            
        Returns:
            List of insights
        """
        insights = []
        
        # Check success rate
        if metrics.test_metrics['success_rate'] < 0.8:  # Below 80% success
            insights.append(PerformanceInsight(
                category='testing',
                description="Low test success rate",
                severity='high',
                confidence=0.9,
                metrics={
                    'success_rate': metrics.test_metrics['success_rate'],
                    'total_tests': metrics.test_metrics['total_tests']
                },
                recommendations=[
                    "Review failed test cases",
                    "Check for environmental issues",
                    "Validate test prerequisites"
                ],
                timestamp=time.time()
            ))
            
        # Check error patterns
        if metrics.test_metrics['error_rate'] > 0.2:  # Above 20% errors
            insights.append(PerformanceInsight(
                category='testing',
                description="High test error rate",
                severity='high',
                confidence=0.9,
                metrics={
                    'error_rate': metrics.test_metrics['error_rate'],
                    'total_tests': metrics.test_metrics['total_tests']
                },
                recommendations=[
                    "Analyze error patterns",
                    "Check for common failure modes",
                    "Review error handling logic"
                ],
                timestamp=time.time()
            ))
            
        return insights
        
    def _analyze_behavior_patterns(
        self,
        metrics: PerformanceMetrics
    ) -> List[PerformanceInsight]:
        """Analyze behavior patterns.
        
        Args:
            metrics: Current metrics
            
        Returns:
            List of insights
        """
        insights = []
        
        # Check behavior diversity
        if metrics.behavior_metrics['behavior_diversity'] < 0.5:  # Low diversity
            insights.append(PerformanceInsight(
                category='behavior',
                description="Low behavior diversity",
                severity='medium',
                confidence=0.8,
                metrics={
                    'diversity': metrics.behavior_metrics['behavior_diversity'],
                    'total_behaviors': metrics.behavior_metrics['total_behaviors']
                },
                recommendations=[
                    "Review behavior detection thresholds",
                    "Check for behavior type limitations",
                    "Consider adding new behavior types"
                ],
                timestamp=time.time()
            ))
            
        # Check behavior confidence
        if metrics.behavior_metrics['average_confidence'] < 0.7:  # Low confidence
            insights.append(PerformanceInsight(
                category='behavior',
                description="Low behavior detection confidence",
                severity='medium',
                confidence=0.85,
                metrics={
                    'average_confidence': metrics.behavior_metrics['average_confidence'],
                    'total_behaviors': metrics.behavior_metrics['total_behaviors']
                },
                recommendations=[
                    "Tune behavior detection parameters",
                    "Review confidence calculation logic",
                    "Validate behavior patterns"
                ],
                timestamp=time.time()
            ))
            
        return insights
        
    def _analyze_metric_trend(
        self,
        metric_key: str
    ) -> Optional[PerformanceInsight]:
        """Analyze trend for specific metric.
        
        Args:
            metric_key: Metric to analyze
            
        Returns:
            Trend insight if significant
        """
        if not self.metrics_history:
            return None
            
        # Get metric values
        values = []
        timestamps = []
        
        for metrics in self.metrics_history:
            if metric_key in metrics.system_metrics:
                values.append(metrics.system_metrics[metric_key])
                timestamps.append(metrics.timestamp)
                
        if len(values) < 3:
            return None
            
        # Fit linear trend
        X = np.array(timestamps).reshape(-1, 1)
        y = np.array(values)
        
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        model.fit(X, y)
        
        # Check if trend is significant
        slope = model.coef_[0]
        baseline = np.mean(values)
        if baseline == 0:
            return None
            
        relative_slope = abs(slope / baseline)
        if relative_slope > 0.1:  # 10% change per unit time
            direction = "increasing" if slope > 0 else "decreasing"
            return PerformanceInsight(
                category='trend',
                description=f"Significant {direction} trend in {metric_key}",
                severity='medium',
                confidence=min(1.0, relative_slope * 5),
                metrics={
                    'metric': metric_key,
                    'slope': slope,
                    'baseline': baseline,
                    'relative_slope': relative_slope
                },
                recommendations=[
                    f"Monitor {metric_key} trend",
                    "Investigate cause of change",
                    "Review system configuration"
                ],
                timestamp=time.time()
            )
            
        return None
        
    def _filter_insights(
        self,
        insights: List[PerformanceInsight]
    ) -> List[PerformanceInsight]:
        """Filter and deduplicate insights.
        
        Args:
            insights: List of insights
            
        Returns:
            Filtered insight list
        """
        # Filter by confidence
        insights = [
            i for i in insights
            if i.confidence >= self.min_confidence
        ]
        
        # Sort by severity and confidence
        insights.sort(
            key=lambda x: (
                {'high': 2, 'medium': 1, 'low': 0}[x.severity],
                x.confidence
            ),
            reverse=True
        )
        
        # Remove duplicates
        seen = set()
        filtered = []
        
        for insight in insights:
            key = (insight.category, insight.description)
            if key not in seen:
                filtered.append(insight)
                seen.add(key)
                
        return filtered 