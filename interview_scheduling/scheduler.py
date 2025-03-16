"""Interview Scheduler Module

This module implements a basic interview scheduling system.
It is designed to find common time slots between candidates and interviewers, based on their provided availabilities.
Currently, it supports simple matching; future enhancements may integrate calendar APIs (e.g., Google Calendar) for automated scheduling.
SOTA practices include time zone awareness, real-time scheduling, and integration with candidate ranking outputs.
Inspired by patterns in the OpenManus-main repository.
"""

import datetime
from datetime import datetime
from typing import List, Dict, Optional


class InterviewScheduler:
    def __init__(self):
        """
        Initialize the scheduler with empty availability listings for candidates and interviewers.
        """
        self.candidate_availabilities = {}  # candidate_id -> list of (start_datetime, end_datetime) tuples
        self.interviewer_availabilities = {}  # interviewer_id -> list of (start_datetime, end_datetime) tuples

    def add_candidate_availability(self, candidate_id: str, slots: List[Dict[str, str]]):
        """
        Add candidate availability.

        Args:
            candidate_id: Candidate identifier.
            slots: List of availability slots with 'start' and 'end' as ISO formatted strings.
        """
        self.candidate_availabilities[candidate_id] = [
            (datetime.fromisoformat(slot['start']), datetime.fromisoformat(slot['end'])) for slot in slots
        ]

    def add_interviewer_availability(self, interviewer_id: str, slots: List[Dict[str, str]]):
        """
        Add interviewer availability.

        Args:
            interviewer_id: Interviewer identifier.
            slots: List of availability slots with 'start' and 'end' as ISO formatted strings.
        """
        self.interviewer_availabilities[interviewer_id] = [
            (datetime.fromisoformat(slot['start']), datetime.fromisoformat(slot['end'])) for slot in slots
        ]

    def find_common_slots(self, candidate_id: str, interviewer_id: str, min_duration_minutes: int = 30) -> List[Dict[str, str]]:
        """
        Find common available time slots between a candidate and an interviewer
        that are at least min_duration_minutes long.

        Args:
            candidate_id: Candidate identifier.
            interviewer_id: Interviewer identifier.
            min_duration_minutes: Minimum duration in minutes for a valid slot.

        Returns:
            List of common time slots, each represented as a dictionary with 'start' and 'end' ISO strings.
        """
        candidate_slots = self.candidate_availabilities.get(candidate_id, [])
        interviewer_slots = self.interviewer_availabilities.get(interviewer_id, [])
        common_slots = []

        for c_start, c_end in candidate_slots:
            for i_start, i_end in interviewer_slots:
                common_start = max(c_start, i_start)
                common_end = min(c_end, i_end)
                if common_end > common_start and (common_end - common_start).total_seconds() >= min_duration_minutes * 60:
                    common_slots.append({
                        "start": common_start.isoformat(),
                        "end": common_end.isoformat()
                    })
        return common_slots

    def schedule_interview(self, candidate_id: str, interviewer_id: str, desired_slot: Optional[Dict[str, str]] = None) -> Optional[Dict[str, str]]:
        """
        Schedule an interview between a candidate and an interviewer.
        If a desired_slot is provided, it checks availability; otherwise, it returns the earliest common slot.

        Args:
            candidate_id: Candidate identifier.
            interviewer_id: Interviewer identifier.
            desired_slot: Optional desired time slot with 'start' and 'end' as ISO strings.

        Returns:
            Scheduled interview slot as a dictionary with 'start' and 'end', or None if no valid slot found.
        """
        common_slots = self.find_common_slots(candidate_id, interviewer_id)
        if not common_slots:
            return None
        if desired_slot:
            for slot in common_slots:
                if slot["start"] == desired_slot["start"] and slot["end"] == desired_slot["end"]:
                    return slot
            return None
        else:
            # Return the earliest available slot
            common_slots.sort(key=lambda slot: slot["start"])
            return common_slots[0] 