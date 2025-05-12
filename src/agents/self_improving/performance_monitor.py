"""
Performance Monitoring for Self-Improving Agents.

This module implements a sophisticated performance monitoring system that tracks
various metrics for RecruitPro AI agents, providing insights into their performance
and identifying areas for improvement.
"""

import logging
import time
import json
import datetime
from typing import Dict, List, Any, Optional, Union, Callable
from threading import Lock
import uuid
import statistics
import os
import csv
from collections import defaultdict, deque

from src.utils.config import DEBUG

logger = logging.getLogger(__name__)


class MetricTimeWindow:
    """
    Time window aggregator for metrics.
    
    Maintains metrics over configurable time windows, supporting:
    - Real-time metrics (last N seconds)
    - Short-term trends (minutes to hours)
    - Long-term analysis (days to weeks)
    """
    
    def __init__(
        self,
        window_size: int,
        max_samples: Optional[int] = None
    ):
        """
        Initialize a metric time window.
        
        Args:
            window_size: Window size in seconds
            max_samples: Maximum number of samples to store (optional)
        """
        self.window_size = window_size
        self.max_samples = max_samples
        self.samples = deque(maxlen=max_samples)
        self.lock = Lock()
        
    def add_sample(self, value: Union[int, float], timestamp: Optional[float] = None):
        """
        Add a metric sample to the window.
        
        Args:
            value: Metric value
            timestamp: Optional timestamp (default: current time)
        """
        timestamp = timestamp or time.time()
        
        with self.lock:
            self.samples.append((timestamp, value))
            
            # Clean old samples outside the window
            current_time = time.time()
            cutoff_time = current_time - self.window_size
            
            # Remove old samples (more efficient than filtering the whole deque)
            while self.samples and self.samples[0][0] < cutoff_time:
                self.samples.popleft()
    
    def get_samples(self, within_seconds: Optional[int] = None) -> List[Union[int, float]]:
        """
        Get all samples within the specified time window.
        
        Args:
            within_seconds: Optional custom time window in seconds
            
        Returns:
            List of sample values
        """
        with self.lock:
            if not self.samples:
                return []
                
            if within_seconds is None:
                # Return all samples in the default window
                return [s[1] for s in self.samples]
                
            # Filter by custom time window
            cutoff_time = time.time() - within_seconds
            return [s[1] for s in self.samples if s[0] >= cutoff_time]
    
    def get_stats(self, within_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        Get statistics for the samples in the window.
        
        Args:
            within_seconds: Optional custom time window in seconds
            
        Returns:
            Dictionary of statistics
        """
        samples = self.get_samples(within_seconds)
        
        if not samples:
            return {
                "count": 0,
                "min": None,
                "max": None,
                "mean": None,
                "median": None,
                "std_dev": None,
                "p95": None,
                "p99": None
            }
            
        # Calculate statistics
        sorted_samples = sorted(samples)
        count = len(sorted_samples)
        
        # Calculate percentiles
        p95_idx = max(0, int(0.95 * count) - 1)
        p99_idx = max(0, int(0.99 * count) - 1)
        
        # Handle standard deviation with single sample
        std_dev = statistics.stdev(samples) if count > 1 else 0
        
        return {
            "count": count,
            "min": min(samples),
            "max": max(samples),
            "mean": statistics.mean(samples),
            "median": statistics.median(samples),
            "std_dev": std_dev,
            "p95": sorted_samples[p95_idx],
            "p99": sorted_samples[p99_idx]
        }


class PerformanceMetric:
    """
    Performance metric tracker with multiple time windows.
    
    Tracks a specific performance metric across multiple time windows,
    providing both immediate and historical views of the metric.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        unit: str = "",
        windows: Optional[List[int]] = None,
        max_samples: Optional[int] = 10000
    ):
        """
        Initialize a performance metric.
        
        Args:
            name: Metric name
            description: Metric description
            unit: Unit of measurement
            windows: List of window sizes in seconds
            max_samples: Maximum samples per window
        """
        self.name = name
        self.description = description
        self.unit = unit
        self.created_at = time.time()
        
        # Default windows: 1 minute, 1 hour, 1 day, 30 days
        self.windows = windows or [60, 3600, 86400, 2592000]
        
        # Initialize time windows
        self.time_windows = {
            window: MetricTimeWindow(window, max_samples)
            for window in self.windows
        }
        
        # Track overall metrics
        self.total_count = 0
        self.total_sum = 0
        self.last_value = None
        self.last_update = None
        
        # Thread safety
        self.lock = Lock()
    
    def record(self, value: Union[int, float], timestamp: Optional[float] = None):
        """
        Record a metric value.
        
        Args:
            value: Metric value
            timestamp: Optional timestamp (default: current time)
        """
        timestamp = timestamp or time.time()
        
        with self.lock:
            # Update overall metrics
            self.total_count += 1
            self.total_sum += value
            self.last_value = value
            self.last_update = timestamp
            
            # Add to all time windows
            for window in self.time_windows.values():
                window.add_sample(value, timestamp)
    
    def get_stats(self, window_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Get statistics for the metric.
        
        Args:
            window_size: Optional specific window size in seconds
            
        Returns:
            Dictionary of statistics
        """
        with self.lock:
            # Get overall metrics
            overall = {
                "name": self.name,
                "description": self.description,
                "unit": self.unit,
                "total_count": self.total_count,
                "total_sum": self.total_sum,
                "lifetime_avg": self.total_sum / self.total_count if self.total_count > 0 else None,
                "last_value": self.last_value,
                "last_update": self.last_update
            }
            
            # If specific window requested
            if window_size is not None:
                # Use the closest available window
                closest_window = min(self.windows, key=lambda w: abs(w - window_size))
                window_stats = self.time_windows[closest_window].get_stats()
                overall["window_stats"] = window_stats
                overall["window_size"] = closest_window
                return overall
                
            # Get stats for all windows
            window_stats = {
                f"window_{window}s": self.time_windows[window].get_stats()
                for window in self.windows
            }
            
            return {**overall, **window_stats}


class AlertRule:
    """
    Alert rule for performance metrics.
    
    Defines conditions for generating alerts based on performance metrics,
    supporting thresholds, trends, and anomaly detection.
    """
    
    # Alert severities
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    
    def __init__(
        self,
        name: str,
        metric_name: str,
        condition: Callable[[Dict[str, Any]], bool],
        severity: str = WARNING,
        description: str = "",
        window_size: Optional[int] = None,
        cooldown_seconds: int = 300,  # 5 minutes default cooldown
        actions: Optional[List[Callable]] = None
    ):
        """
        Initialize an alert rule.
        
        Args:
            name: Rule name
            metric_name: Target metric name
            condition: Function that evaluates the metric and returns True if alert should trigger
            severity: Alert severity level
            description: Rule description
            window_size: Time window size in seconds for evaluation
            cooldown_seconds: Minimum seconds between consecutive alerts
            actions: List of action functions to execute when alert triggers
        """
        self.name = name
        self.metric_name = metric_name
        self.condition = condition
        self.severity = severity
        self.description = description
        self.window_size = window_size
        self.cooldown_seconds = cooldown_seconds
        self.actions = actions or []
        
        # Last alert tracking
        self.last_triggered = 0
        self.trigger_count = 0
    
    def evaluate(self, metric_stats: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Evaluate the rule against metric statistics.
        
        Args:
            metric_stats: Metric statistics dictionary
            
        Returns:
            Alert dictionary if triggered, None otherwise
        """
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_triggered < self.cooldown_seconds:
            return None
            
        # Evaluate condition
        try:
            if self.condition(metric_stats):
                # Create alert
                alert = {
                    "rule_name": self.name,
                    "metric_name": self.metric_name,
                    "severity": self.severity,
                    "description": self.description,
                    "timestamp": current_time,
                    "stats": metric_stats
                }
                
                # Update tracking
                self.last_triggered = current_time
                self.trigger_count += 1
                
                # Execute actions
                for action in self.actions:
                    try:
                        action(alert)
                    except Exception as e:
                        logger.error(f"Error executing alert action: {e}")
                
                return alert
        except Exception as e:
            logger.error(f"Error evaluating alert rule '{self.name}': {e}")
            
        return None


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system for RecruitPro AI agents.
    
    Tracks various performance metrics, analyzes trends, detects anomalies,
    and generates alerts to help improve agent performance.
    """
    
    def __init__(
        self,
        agent_id: str = "global",
        metrics_dir: Optional[str] = None,
        auto_snapshot: bool = True,
        snapshot_interval: int = 86400  # Daily snapshots by default
    ):
        """
        Initialize the performance monitor.
        
        Args:
            agent_id: Agent identifier (or 'global' for system-wide)
            metrics_dir: Directory for storing metrics data
            auto_snapshot: Whether to automatically take snapshots
            snapshot_interval: Interval in seconds between snapshots
        """
        self.agent_id = agent_id
        self.metrics_dir = metrics_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
            "metrics"
        )
        
        # Create metrics directory if not exists
        os.makedirs(self.metrics_dir, exist_ok=True)
        
        # Metrics and alerts collections
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.recent_alerts: deque = deque(maxlen=100)  # Last 100 alerts
        
        # Enable auto snapshotting
        self.auto_snapshot = auto_snapshot
        self.snapshot_interval = snapshot_interval
        self.last_snapshot = time.time()
        
        # Thread safety
        self.lock = Lock()
        
        # Initialize standard metrics
        self._initialize_standard_metrics()
        
        logger.info(f"Performance monitor initialized for {agent_id}")
    
    def _initialize_standard_metrics(self):
        """Initialize standard performance metrics."""
        # Response time metrics
        self.register_metric(
            name="response_time",
            description="Time to generate response",
            unit="ms"
        )
        
        # Success rate metrics
        self.register_metric(
            name="success_rate",
            description="Percentage of successful operations",
            unit="%"
        )
        
        # Error rate metrics
        self.register_metric(
            name="error_rate",
            description="Percentage of operations that resulted in errors",
            unit="%"
        )
        
        # Throughput metrics
        self.register_metric(
            name="throughput",
            description="Number of operations per second",
            unit="ops/s"
        )
        
        # Token usage metrics
        self.register_metric(
            name="token_usage",
            description="Number of tokens used",
            unit="tokens"
        )
        
        # User feedback metrics
        self.register_metric(
            name="user_satisfaction",
            description="User satisfaction score",
            unit="score"
        )
        
        # Set up standard alert rules
        self._initialize_standard_alerts()
    
    def _initialize_standard_alerts(self):
        """Initialize standard alert rules."""
        # High error rate alert
        self.register_alert_rule(
            name="high_error_rate",
            metric_name="error_rate",
            condition=lambda stats: stats.get("last_value", 0) > 10.0,  # >10% error rate
            severity=AlertRule.WARNING,
            description="Error rate is above 10%",
            window_size=300  # 5 minutes
        )
        
        # High response time alert
        self.register_alert_rule(
            name="high_response_time",
            metric_name="response_time",
            condition=lambda stats: stats.get("window_stats", {}).get("p95", 0) > 5000,  # >5s p95
            severity=AlertRule.WARNING,
            description="95th percentile response time is above 5 seconds",
            window_size=300  # 5 minutes
        )
        
        # Low user satisfaction alert
        self.register_alert_rule(
            name="low_user_satisfaction",
            metric_name="user_satisfaction",
            condition=lambda stats: stats.get("window_stats", {}).get("mean", 5) < 3.0,  # <3 out of 5
            severity=AlertRule.ERROR,
            description="Average user satisfaction score is below 3.0",
            window_size=3600  # 1 hour
        )
    
    def register_metric(
        self,
        name: str,
        description: str,
        unit: str = "",
        windows: Optional[List[int]] = None,
        max_samples: Optional[int] = 10000
    ) -> PerformanceMetric:
        """
        Register a new performance metric.
        
        Args:
            name: Metric name
            description: Metric description
            unit: Unit of measurement
            windows: List of window sizes in seconds
            max_samples: Maximum samples per window
            
        Returns:
            Created PerformanceMetric object
        """
        with self.lock:
            # Check if metric already exists
            if name in self.metrics:
                return self.metrics[name]
                
            # Create new metric
            metric = PerformanceMetric(
                name=name,
                description=description,
                unit=unit,
                windows=windows,
                max_samples=max_samples
            )
            
            self.metrics[name] = metric
            logger.debug(f"Registered metric: {name}")
            
            return metric
    
    def record_metric(
        self,
        name: str,
        value: Union[int, float],
        timestamp: Optional[float] = None
    ):
        """
        Record a value for a metric.
        
        Args:
            name: Metric name
            value: Metric value
            timestamp: Optional timestamp (default: current time)
        """
        # Get or create the metric
        if name not in self.metrics:
            self.register_metric(name=name, description=f"Auto-registered metric: {name}")
            
        # Record the value
        self.metrics[name].record(value, timestamp)
        
        # Evaluate alert rules for this metric
        self._evaluate_alerts(name)
        
        # Check if snapshot needed
        if self.auto_snapshot and time.time() - self.last_snapshot >= self.snapshot_interval:
            self.take_snapshot()
    
    def register_alert_rule(
        self,
        name: str,
        metric_name: str,
        condition: Callable[[Dict[str, Any]], bool],
        severity: str = AlertRule.WARNING,
        description: str = "",
        window_size: Optional[int] = None,
        cooldown_seconds: int = 300,
        actions: Optional[List[Callable]] = None
    ) -> AlertRule:
        """
        Register a new alert rule.
        
        Args:
            name: Rule name
            metric_name: Target metric name
            condition: Function that evaluates metric and returns True if alert should trigger
            severity: Alert severity level
            description: Rule description
            window_size: Time window size in seconds for evaluation
            cooldown_seconds: Minimum seconds between consecutive alerts
            actions: List of action functions to execute when alert triggers
            
        Returns:
            Created AlertRule object
        """
        with self.lock:
            # Check if rule already exists
            if name in self.alert_rules:
                return self.alert_rules[name]
                
            # Create new rule
            rule = AlertRule(
                name=name,
                metric_name=metric_name,
                condition=condition,
                severity=severity,
                description=description,
                window_size=window_size,
                cooldown_seconds=cooldown_seconds,
                actions=actions
            )
            
            self.alert_rules[name] = rule
            logger.debug(f"Registered alert rule: {name}")
            
            return rule
    
    def _evaluate_alerts(self, metric_name: Optional[str] = None):
        """
        Evaluate alert rules for a specific metric or all metrics.
        
        Args:
            metric_name: Optional specific metric to evaluate
        """
        if metric_name:
            # Evaluate rules for specific metric
            rules = [rule for rule in self.alert_rules.values() if rule.metric_name == metric_name]
        else:
            # Evaluate all rules
            rules = list(self.alert_rules.values())
            
        # Skip if no rules to evaluate
        if not rules:
            return
            
        # Evaluate each rule
        for rule in rules:
            try:
                # Get metric stats
                if rule.metric_name not in self.metrics:
                    continue
                    
                metric_stats = self.metrics[rule.metric_name].get_stats(rule.window_size)
                
                # Evaluate rule
                alert = rule.evaluate(metric_stats)
                
                # Handle triggered alert
                if alert:
                    self.recent_alerts.append(alert)
                    logger.warning(f"Alert triggered: {rule.name} - {rule.description}")
                    
                    # Log critical alerts at error level
                    if rule.severity == AlertRule.CRITICAL:
                        logger.error(f"CRITICAL ALERT: {rule.name} - {rule.description}")
            except Exception as e:
                logger.error(f"Error evaluating alert rule '{rule.name}': {e}")
    
    def take_snapshot(self):
        """
        Take a snapshot of current metrics and save to disk.
        
        This allows for historical analysis and long-term trend monitoring.
        """
        with self.lock:
            timestamp = time.time()
            self.last_snapshot = timestamp
            
            # Format timestamp for filename
            date_str = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d_%H-%M-%S")
            snapshot_file = os.path.join(
                self.metrics_dir,
                f"{self.agent_id}_metrics_{date_str}.json"
            )
            
            # Gather all metrics
            snapshot_data = {
                "agent_id": self.agent_id,
                "timestamp": timestamp,
                "metrics": {
                    name: metric.get_stats()
                    for name, metric in self.metrics.items()
                },
                "alerts": [
                    {
                        "rule_name": rule.name,
                        "metric_name": rule.metric_name,
                        "severity": rule.severity,
                        "description": rule.description,
                        "trigger_count": rule.trigger_count,
                        "last_triggered": rule.last_triggered
                    }
                    for rule in self.alert_rules.values()
                    if rule.trigger_count > 0
                ]
            }
            
            # Save to file
            try:
                with open(snapshot_file, 'w') as f:
                    json.dump(snapshot_data, f, indent=2)
                    
                logger.info(f"Metrics snapshot saved to {snapshot_file}")
                return snapshot_file
            except Exception as e:
                logger.error(f"Error saving metrics snapshot: {e}")
                return None
    
    def get_metric_stats(
        self,
        metric_name: str,
        window_size: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific metric.
        
        Args:
            metric_name: Metric name
            window_size: Optional specific window size in seconds
            
        Returns:
            Metric statistics dictionary or None if metric not found
        """
        if metric_name not in self.metrics:
            return None
            
        return self.metrics[metric_name].get_stats(window_size)
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all metrics.
        
        Returns:
            Dictionary of metric names to statistics
        """
        return {
            name: metric.get_stats()
            for name, metric in self.metrics.items()
        }
    
    def get_recent_alerts(self) -> List[Dict[str, Any]]:
        """
        Get list of recent alerts.
        
        Returns:
            List of recent alert dictionaries
        """
        return list(self.recent_alerts)
    
    def export_metrics_csv(self, output_file: Optional[str] = None) -> Optional[str]:
        """
        Export metrics data to CSV file.
        
        Args:
            output_file: Optional output file path
            
        Returns:
            Path to CSV file or None if export failed
        """
        if not output_file:
            # Generate default filename
            date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_file = os.path.join(
                self.metrics_dir,
                f"{self.agent_id}_metrics_export_{date_str}.csv"
            )
            
        try:
            # Get all metrics
            all_metrics = self.get_all_metrics()
            
            # Prepare CSV data
            rows = []
            header = ["metric_name", "description", "unit", "total_count", "last_value", "lifetime_avg"]
            
            # Add window stats columns for the first metric's windows
            window_sizes = []
            if all_metrics:
                first_metric = next(iter(all_metrics.values()))
                for key in first_metric.keys():
                    if key.startswith("window_") and key.endswith("s"):
                        window_size = key.replace("window_", "").replace("s", "")
                        window_sizes.append(window_size)
                        header.extend([
                            f"window_{window_size}s_count",
                            f"window_{window_size}s_min",
                            f"window_{window_size}s_max",
                            f"window_{window_size}s_mean",
                            f"window_{window_size}s_median",
                            f"window_{window_size}s_p95"
                        ])
            
            # Add each metric as a row
            for name, stats in all_metrics.items():
                row = [
                    name,
                    stats.get("description", ""),
                    stats.get("unit", ""),
                    stats.get("total_count", 0),
                    stats.get("last_value", ""),
                    stats.get("lifetime_avg", "")
                ]
                
                # Add window stats
                for window_size in window_sizes:
                    window_key = f"window_{window_size}s"
                    window_stats = stats.get(window_key, {})
                    row.extend([
                        window_stats.get("count", 0),
                        window_stats.get("min", ""),
                        window_stats.get("max", ""),
                        window_stats.get("mean", ""),
                        window_stats.get("median", ""),
                        window_stats.get("p95", "")
                    ])
                
                rows.append(row)
                
            # Write to CSV
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(rows)
                
            logger.info(f"Metrics exported to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting metrics to CSV: {e}")
            return None


# Singleton instance
_performance_monitor = None

def get_performance_monitor(agent_id: str = "global") -> PerformanceMonitor:
    """
    Get or create the PerformanceMonitor singleton.
    
    Args:
        agent_id: Agent identifier
        
    Returns:
        PerformanceMonitor instance
    """
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(agent_id)
    return _performance_monitor
