"""
Feedback Processor for Self-Improving Agents.

Collects and processes explicit and implicit feedback from users,
categorizes it, and provides summaries for learning.
"""

import threading
import logging
from typing import List, Dict, Any, Optional
import time
import uuid

logger = logging.getLogger(__name__)


class FeedbackProcessor:
    """
    Processes user feedback to extract actionable insights.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.feedback_entries: List[Dict[str, Any]] = []

    def add_feedback(
        self,
        user_id: str,
        agent_id: str,
        feedback_text: str,
        rating: Optional[int] = None,
        implicit: bool = False
    ) -> Dict[str, Any]:
        """
        Add a feedback entry.

        Args:
            user_id: Identifier of the user providing feedback
            agent_id: Identifier of the agent
            feedback_text: Textual feedback
            rating: Optional numeric rating (e.g., 1-5)
            implicit: Whether feedback is implicit (e.g., low engagement)

        Returns:
            Stored feedback entry
        """
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "user_id": user_id,
            "agent_id": agent_id,
            "text": feedback_text,
            "rating": rating,
            "implicit": implicit
        }
        with self.lock:
            self.feedback_entries.append(entry)
            logger.debug(f"Feedback added: {entry['id']}")
        return entry

    def get_all_feedback(self) -> List[Dict[str, Any]]:
        """
        Retrieve all feedback entries.
        """
        with self.lock:
            return list(self.feedback_entries)

    def summarize_feedback(self) -> Dict[str, Any]:
        """
        Summarize feedback by counts, average rating, and categorization.
        """
        with self.lock:
            total = len(self.feedback_entries)
            if total == 0:
                return {"total": 0, "average_rating": None, "explicit": 0, "implicit": 0}

            ratings = [e['rating'] for e in self.feedback_entries if e.get('rating') is not None]
            avg_rating = sum(ratings) / len(ratings) if ratings else None
            explicit = sum(not e['implicit'] for e in self.feedback_entries)
            implicit = total - explicit

        summary = {
            "total": total,
            "average_rating": avg_rating,
            "explicit": explicit,
            "implicit": implicit
        }
        logger.info(f"Feedback summary: {summary}")
        return summary


# Singleton
_feedback_processor: Optional[FeedbackProcessor] = None


def get_feedback_processor() -> FeedbackProcessor:
    """
    Get or create the FeedbackProcessor singleton.
    """
    global _feedback_processor
    if _feedback_processor is None:
        _feedback_processor = FeedbackProcessor()
        logger.info("Initialized FeedbackProcessor singleton")
    return _feedback_processor
