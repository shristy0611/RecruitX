"""
Self-Improving Agent Architecture for RecruitPro AI.

This module implements advanced self-improvement capabilities for the RecruitPro AI
agents, allowing them to learn from past interactions, optimize their parameters,
and continuously improve their performance.
"""

from src.agents.self_improving.performance_monitor import PerformanceMonitor, get_performance_monitor
from src.agents.self_improving.feedback_processor import FeedbackProcessor, get_feedback_processor
from src.agents.self_improving.reinforcement_learner import ReinforcementLearner, get_reinforcement_learner
from src.agents.self_improving.parameter_optimizer import ParameterOptimizer, get_parameter_optimizer
from src.agents.self_improving.experience_replay import ExperienceReplay, get_experience_replay
from src.agents.self_improving.learning_orchestrator import LearningOrchestrator, get_learning_orchestrator

__all__ = [
    'PerformanceMonitor',
    'get_performance_monitor',
    'FeedbackProcessor',
    'get_feedback_processor',
    'ReinforcementLearner',
    'get_reinforcement_learner',
    'ParameterOptimizer',
    'get_parameter_optimizer',
    'ExperienceReplay',
    'get_experience_replay',
    'LearningOrchestrator',
    'get_learning_orchestrator'
]
