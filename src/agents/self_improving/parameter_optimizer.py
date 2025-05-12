"""
Parameter Optimizer for Self-Improving Agents.

Tunes agent parameters based on performance metrics to find optimal configurations.
"""

import threading
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ParameterOptimizer:
    """
    Optimizes agent parameters by tracking performance of different configurations.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.parameters: Dict[str, Any] = {}
        self.best_config: Dict[str, Any] = {}
        self.best_metric: Optional[float] = None

    def register_parameter(self, name: str, initial_value: Any):
        """Register a new parameter with an initial value."""
        with self.lock:
            self.parameters[name] = initial_value
            logger.debug(f"Registered parameter: {name} = {initial_value}")

    def update_parameter(self, name: str, value: Any):
        """Update an existing parameter."""
        with self.lock:
            if name in self.parameters:
                self.parameters[name] = value
                logger.debug(f"Updated parameter: {name} = {value}")

    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameter configuration."""
        with self.lock:
            return dict(self.parameters)

    def record_performance(self, metric_value: float, config: Dict[str, Any]):
        """Record performance for a configuration and update best if improved."""
        with self.lock:
            if self.best_metric is None or metric_value > self.best_metric:
                self.best_metric = metric_value
                self.best_config = dict(config)
                logger.info(f"New best config: {self.best_config} with metric {metric_value}")

    def get_best_configuration(self) -> Optional[Dict[str, Any]]:
        """Get the best parameter configuration found so far."""
        with self.lock:
            return dict(self.best_config) if self.best_config else None


# Singleton instance
_optimizer: Optional[ParameterOptimizer] = None

def get_parameter_optimizer() -> ParameterOptimizer:
    """Get or create the ParameterOptimizer singleton."""
    global _optimizer
    if _optimizer is None:
        _optimizer = ParameterOptimizer()
        logger.info("Initialized ParameterOptimizer singleton")
    return _optimizer
