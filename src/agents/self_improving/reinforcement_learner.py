"""
Reinforcement Learner for Self-Improving Agents.

Learns from feedback and performance metrics to adjust agent behavior using
Q-learning-style updates.
"""

import logging
from typing import Dict, Optional

from src.agents.self_improving.feedback_processor import FeedbackProcessor, get_feedback_processor
from src.agents.self_improving.performance_monitor import PerformanceMonitor, get_performance_monitor

logger = logging.getLogger(__name__)


class ReinforcementLearner:
    """
    Learns from feedback and performance metrics to optimize agent policies.
    """
    def __init__(self, learning_rate: float = 0.1):
        self.feedback_processor = get_feedback_processor()
        self.performance_monitor = get_performance_monitor()
        self.learning_rate = learning_rate
        self.q_table: Dict[str, float] = {}

    def learn(self, episodes: int = 10):
        """
        Run learning cycles based on stored feedback.
        """
        feedbacks = self.feedback_processor.get_all_feedback()
        for _ in range(episodes):
            for f in feedbacks:
                key = f"{f['agent_id']}:{f['text']}"
                reward = f.get('rating', 0) if not f.get('implicit', False) else -1
                old_q = self.q_table.get(key, 0.0)
                self.q_table[key] = old_q + self.learning_rate * (reward - old_q)
        logger.info("Reinforcement learning completed")

    def get_policy(self) -> Dict[str, float]:
        """
        Return the learned Q-values mapping.
        """
        return dict(self.q_table)


# Singleton instance
_learner: Optional[ReinforcementLearner] = None

def get_reinforcement_learner() -> ReinforcementLearner:
    """
    Get or create the ReinforcementLearner singleton.
    """
    global _learner
    if _learner is None:
        _learner = ReinforcementLearner()
        logger.info("Initialized ReinforcementLearner singleton")
    return _learner
