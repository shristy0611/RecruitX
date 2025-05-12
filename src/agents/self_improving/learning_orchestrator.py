"""
Learning Orchestrator for Self-Improving Agents.

Coordinates the learning cycle by integrating feedback, performance metrics,
reinforcement learning, experience replay, and parameter optimization.
"""
import logging
from typing import Dict, Any

from src.agents.self_improving.feedback_processor import get_feedback_processor
from src.agents.self_improving.performance_monitor import get_performance_monitor
from src.agents.self_improving.reinforcement_learner import get_reinforcement_learner
from src.agents.self_improving.parameter_optimizer import get_parameter_optimizer
from src.agents.self_improving.experience_replay import get_experience_replay

logger = logging.getLogger(__name__)


class LearningOrchestrator:
    """
    Orchestrates the self-improvement learning process.
    """
    def __init__(self):
        self.processor = get_feedback_processor()
        self.monitor = get_performance_monitor()
        self.learner = get_reinforcement_learner()
        self.optimizer = get_parameter_optimizer()
        self.replay = get_experience_replay()
        logger.info("Initialized LearningOrchestrator singleton")

    def run_cycle(self, episodes: int = 10, metric_name: str = "response_time") -> Dict[str, Any]:
        """
        Run a full self-improvement cycle:
        1. Learn from feedback via reinforcement learning
        2. Store feedback in experience replay
        3. Optimize parameters based on performance metrics
        """
        # 1. Reinforcement learning
        self.learner.learn(episodes)

        # 2. Store feedback experiences
        feedbacks = self.processor.get_all_feedback()
        for f in feedbacks:
            self.replay.add_experience(f)

        # 3. Optimize parameters based on latest performance
        stats = self.monitor.get_metric_stats(metric_name)
        if stats and stats.get("last_value") is not None:
            value = stats["last_value"]
            params = self.optimizer.get_parameters()
            self.optimizer.record_performance(value, params)
            logger.info(f"Optimized parameters with metric {metric_name}: {value}")

        return {
            "q_table": self.learner.get_policy(),
            "best_config": self.optimizer.get_best_configuration()
        }


# Singleton instance
_orchestrator: LearningOrchestrator = None

def get_learning_orchestrator() -> LearningOrchestrator:
    """
    Get or create the LearningOrchestrator singleton.
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = LearningOrchestrator()
    return _orchestrator
