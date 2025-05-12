"""
Experience Replay for Self-Improving Agents.

Stores past interactions for training and sampling to improve learning stability.
"""

import threading
import logging
from typing import List, Any, Optional
from collections import deque

logger = logging.getLogger(__name__)


class ExperienceReplay:
    """
    Implements an experience replay buffer for agent training.
    """
    def __init__(self, capacity: int = 1000):
        self.buffer = deque(maxlen=capacity)
        self.lock = threading.Lock()

    def add_experience(self, experience: Any):
        """
        Add an experience to the buffer.
        """
        with self.lock:
            self.buffer.append(experience)
            logger.debug(f"Experience added. Buffer size: {len(self.buffer)}")

    def sample(self, batch_size: int) -> List[Any]:
        """
        Sample a batch of experiences.
        """
        with self.lock:
            if batch_size > len(self.buffer):
                batch_size = len(self.buffer)
            return list(self.buffer)[:batch_size]

    def clear(self):
        """
        Clear all experiences.
        """
        with self.lock:
            self.buffer.clear()
            logger.info("Experience replay buffer cleared")


# Singleton instance
_replay: Optional[ExperienceReplay] = None

def get_experience_replay() -> ExperienceReplay:
    """Get or create the ExperienceReplay singleton."""
    global _replay
    if _replay is None:
        _replay = ExperienceReplay()
        logger.info("Initialized ExperienceReplay singleton")
    return _replay
