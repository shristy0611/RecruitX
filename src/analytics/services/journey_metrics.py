"""
Candidate journey metrics service for RecruitPro AI.

This service tracks and analyzes candidates' journeys through the 
recruitment process, from initial sourcing to final outcome.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from src.analytics.models.metrics import (
    CandidateJourneyMetrics,
    CandidateJourneyEvent,
    CandidateStatus,
    TimeFrame,
    AgentType
)
from src.utils.config import REDIS_HOST, REDIS_PORT, REDIS_DB
from src.utils.redis_client import RedisClient

# Configure logging
logger = logging.getLogger(__name__)


class JourneyMetricsService:
    """Service for tracking and analyzing candidate journey metrics."""
    
    def __init__(self, redis_client: Optional[RedisClient] = None):
        """
        Initialize the JourneyMetricsService.
        
        Args:
            redis_client: Optional Redis client for metrics storage
        """
        self.redis_client = redis_client or RedisClient(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB
        )
    
    async def get_candidate_journey(
        self, 
        candidate_id: str,
        job_id: Optional[str] = None
    ) -> CandidateJourneyMetrics:
        """
        Get the journey metrics for a specific candidate.
        
        Args:
            candidate_id: ID of the candidate to analyze
            job_id: Optional job ID to filter journey by specific job
            
        Returns:
            CandidateJourneyMetrics: Journey metrics for the candidate
        """
        try:
            # Initialize journey metrics
            journey = CandidateJourneyMetrics(
                candidate_id=candidate_id,
                job_id=job_id
            )
            
            # Fetch candidate data
            candidate_data = await self._fetch_candidate_data(candidate_id, job_id)
            if not candidate_data:
                logger.warning(f"No data found for candidate {candidate_id}")
                return journey
            
            # Set job ID if not provided but available in candidate data
            if not job_id and 'job_id' in candidate_data:
                journey.job_id = candidate_data['job_id']
            
            # Fetch journey events
            events = await self._fetch_journey_events(candidate_id, job_id)
            journey.events = events
            
            # Calculate journey metrics
            journey = self._calculate_journey_metrics(journey, candidate_data)
            
            return journey
            
        except Exception as e:
            logger.error(f"Error retrieving candidate journey: {e}")
            return CandidateJourneyMetrics(candidate_id=candidate_id, job_id=job_id)
    
    async def track_journey_event(
        self,
        candidate_id: str,
        status: CandidateStatus,
        job_id: Optional[str] = None,
        agent_type: Optional[AgentType] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track a new event in a candidate's journey.
        
        Args:
            candidate_id: ID of the candidate
            status: New status of the candidate
            job_id: Optional job ID associated with the event
            agent_type: Optional agent type that triggered the event
            description: Optional description of the event
            metadata: Optional additional data for the event
        """
        try:
            # Create event object
            event = CandidateJourneyEvent(
                timestamp=datetime.now(),
                status=status,
                agent_type=agent_type,
                description=description,
                metadata=metadata or {}
            )
            
            # Store event in Redis
            event_id = f"{datetime.now().timestamp()}"
            event_key = f"candidate:{candidate_id}:journey:{event_id}"
            
            if job_id:
                event_key = f"job:{job_id}:{event_key}"
                event.metadata['job_id'] = job_id
            
            await self.redis_client.set(event_key, str(event.dict()), expire_seconds=180*24*60*60)  # 180 days TTL
            
            # Update candidate's current status
            if job_id:
                status_key = f"candidate:{candidate_id}:job:{job_id}:status"
            else:
                status_key = f"candidate:{candidate_id}:status"
                
            await self.redis_client.set(status_key, status.value)
            
            # Update interaction count
            if job_id:
                interaction_key = f"candidate:{candidate_id}:job:{job_id}:interactions"
            else:
                interaction_key = f"candidate:{candidate_id}:interactions"
                
            await self.redis_client.incr(interaction_key)
            
            logger.debug(f"Tracked journey event for candidate {candidate_id}: {status}")
            
        except Exception as e:
            logger.error(f"Error tracking journey event: {e}")
    
    async def get_cohort_journey_metrics(
        self,
        job_id: Optional[str] = None,
        status: Optional[CandidateStatus] = None,
        time_frame: TimeFrame = TimeFrame.MONTH,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated journey metrics for a cohort of candidates.
        
        Args:
            job_id: Optional job ID to filter candidates
            status: Optional status to filter candidates
            time_frame: Time frame for the metrics
            start_date: Start date for custom time frame
            end_date: End date for custom time frame
            
        Returns:
            Dict[str, Any]: Aggregated journey metrics
        """
        try:
            # Determine date range based on time frame
            if time_frame == TimeFrame.CUSTOM and (not start_date or not end_date):
                raise ValueError("Custom time frame requires start_date and end_date")
                
            if not start_date or not end_date:
                start_date, end_date = self._calculate_date_range(time_frame)
            
            # Fetch all candidates in the cohort
            candidate_ids = await self._fetch_cohort_candidates(job_id, status, start_date, end_date)
            
            if not candidate_ids:
                logger.warning(f"No candidates found for cohort with job_id={job_id}, "
                              f"status={status}, from {start_date} to {end_date}")
                return {
                    "count": 0,
                    "avg_time_in_pipeline": None,
                    "avg_time_to_decision": None,
                    "status_distribution": {},
                    "conversion_rates": {}
                }
            
            # Collect journey metrics for each candidate
            journeys = []
            for candidate_id in candidate_ids:
                journey = await self.get_candidate_journey(candidate_id, job_id)
                journeys.append(journey)
            
            # Calculate aggregated metrics
            return self._calculate_cohort_metrics(journeys)
            
        except Exception as e:
            logger.error(f"Error retrieving cohort journey metrics: {e}")
            return {
                "error": str(e),
                "count": 0
            }
    
    async def _fetch_candidate_data(
        self,
        candidate_id: str,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch candidate data from Redis.
        
        Args:
            candidate_id: ID of the candidate
            job_id: Optional job ID to filter candidate data
            
        Returns:
            Dict[str, Any]: Candidate data
        """
        try:
            # Determine the key to use
            if job_id:
                candidate_key = f"job:{job_id}:candidate:{candidate_id}"
            else:
                candidate_key = f"candidate:{candidate_id}"
                
            # Fetch from Redis
            candidate_data_str = await self.redis_client.get(candidate_key)
            
            if candidate_data_str:
                return eval(candidate_data_str)  # In reality, use proper JSON deserialization
            
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching candidate data: {e}")
            return {}
    
    async def _fetch_journey_events(
        self,
        candidate_id: str,
        job_id: Optional[str] = None
    ) -> List[CandidateJourneyEvent]:
        """
        Fetch journey events for a candidate from Redis.
        
        Args:
            candidate_id: ID of the candidate
            job_id: Optional job ID to filter events
            
        Returns:
            List[CandidateJourneyEvent]: Journey events for the candidate
        """
        try:
            # Determine the pattern to use
            if job_id:
                pattern = f"job:{job_id}:candidate:{candidate_id}:journey:*"
            else:
                pattern = f"candidate:{candidate_id}:journey:*"
                
            # Fetch keys from Redis
            event_keys = await self.redis_client.keys(pattern)
            
            events = []
            for key in event_keys:
                event_data_str = await self.redis_client.get(key)
                if event_data_str:
                    event_data = eval(event_data_str)  # In reality, use proper JSON deserialization
                    
                    # Create event object
                    event = CandidateJourneyEvent(
                        timestamp=event_data.get('timestamp', datetime.now()),
                        status=event_data.get('status', CandidateStatus.NEW),
                        agent_type=event_data.get('agent_type'),
                        description=event_data.get('description'),
                        metadata=event_data.get('metadata', {})
                    )
                    
                    events.append(event)
            
            # Sort events by timestamp
            events.sort(key=lambda e: e.timestamp)
            
            return events
            
        except Exception as e:
            logger.error(f"Error fetching journey events: {e}")
            return []
    
    def _calculate_journey_metrics(
        self,
        journey: CandidateJourneyMetrics,
        candidate_data: Dict[str, Any]
    ) -> CandidateJourneyMetrics:
        """
        Calculate metrics for a candidate's journey.
        
        Args:
            journey: Journey metrics object to populate
            candidate_data: Candidate data from database
            
        Returns:
            CandidateJourneyMetrics: Updated journey metrics
        """
        # Set current status from latest event or from candidate data
        if journey.events:
            journey.current_status = journey.events[-1].status
        elif 'stage' in candidate_data:
            # Map stage to status if needed
            stage_to_status = {
                'sourced': CandidateStatus.NEW,
                'reviewed': CandidateStatus.SCREENING,
                'shortlisted': CandidateStatus.INTERVIEWING,
                'interviewed': CandidateStatus.INTERVIEWING,
                'offered': CandidateStatus.OFFER_EXTENDED,
                'hired': CandidateStatus.HIRED,
                'rejected': CandidateStatus.REJECTED,
                'withdrawn': CandidateStatus.WITHDRAWN
            }
            journey.current_status = stage_to_status.get(candidate_data['stage'], CandidateStatus.NEW)
        
        # Calculate time in pipeline if events exist
        if journey.events:
            first_event = journey.events[0]
            last_event = journey.events[-1]
            
            journey.time_in_pipeline = (last_event.timestamp - first_event.timestamp).days
            
            # Find first contact event
            for event in journey.events:
                if event.status == CandidateStatus.CONTACTED:
                    journey.time_to_first_contact = (event.timestamp - first_event.timestamp).days
                    break
            
            # Find decision event (rejected, hired, offer_extended)
            decision_statuses = [
                CandidateStatus.REJECTED,
                CandidateStatus.HIRED,
                CandidateStatus.OFFER_EXTENDED,
                CandidateStatus.OFFER_DECLINED,
                CandidateStatus.OFFER_ACCEPTED
            ]
            
            for event in journey.events:
                if event.status in decision_statuses:
                    journey.time_to_decision = (event.timestamp - first_event.timestamp).days
                    break
        
        # Set interaction count
        journey.interaction_count = len(journey.events)
        
        # Set response rate if available in candidate data
        if 'response_rate' in candidate_data:
            journey.response_rate = candidate_data['response_rate']
        
        # Set match score if available in candidate data
        if 'match_score' in candidate_data:
            journey.match_score = candidate_data['match_score']
        
        return journey
    
    def _calculate_date_range(self, time_frame: TimeFrame) -> Tuple[datetime, datetime]:
        """
        Calculate start and end dates based on time frame.
        
        Args:
            time_frame: Time frame for the metrics
            
        Returns:
            Tuple[datetime, datetime]: Start and end dates
        """
        now = datetime.now()
        end_date = now
        
        if time_frame == TimeFrame.DAY:
            start_date = now - timedelta(days=1)
        elif time_frame == TimeFrame.WEEK:
            start_date = now - timedelta(days=7)
        elif time_frame == TimeFrame.MONTH:
            start_date = now - timedelta(days=30)
        elif time_frame == TimeFrame.QUARTER:
            start_date = now - timedelta(days=90)
        elif time_frame == TimeFrame.YEAR:
            start_date = now - timedelta(days=365)
        elif time_frame == TimeFrame.ALL_TIME:
            # Use a very old date for all-time
            start_date = datetime(2020, 1, 1)
        else:
            raise ValueError(f"Unsupported time frame: {time_frame}")
            
        return start_date, end_date
    
    async def _fetch_cohort_candidates(
        self,
        job_id: Optional[str],
        status: Optional[CandidateStatus],
        start_date: datetime,
        end_date: datetime
    ) -> List[str]:
        """
        Fetch candidate IDs for a cohort based on filters.
        
        Args:
            job_id: Optional job ID to filter candidates
            status: Optional status to filter candidates
            start_date: Start date for the cohort
            end_date: End date for the cohort
            
        Returns:
            List[str]: List of candidate IDs in the cohort
        """
        try:
            # Determine pattern based on filters
            if job_id:
                pattern = f"job:{job_id}:candidate:*"
            else:
                pattern = "candidate:*"
                
            # Exclude journey event keys
            if "journey" in pattern:
                pattern = pattern.replace("journey:", "")
            
            # Get all candidate keys
            candidate_keys = await self.redis_client.keys(pattern)
            
            candidate_ids = []
            for key in candidate_keys:
                # Extract candidate ID from the key
                parts = key.split(":")
                candidate_id = parts[-1]
                
                # Skip non-candidate keys
                if not candidate_id or candidate_id == "journey" or ":" in candidate_id:
                    continue
                
                # Fetch candidate data to check filters
                candidate_data_str = await self.redis_client.get(key)
                if not candidate_data_str:
                    continue
                    
                candidate_data = eval(candidate_data_str)  # In reality, use proper JSON deserialization
                
                # Check status filter if provided
                if status:
                    candidate_status = None
                    
                    # Check current status from data
                    if 'stage' in candidate_data:
                        # Map stage to status if needed
                        stage_to_status = {
                            'sourced': CandidateStatus.NEW,
                            'reviewed': CandidateStatus.SCREENING,
                            'shortlisted': CandidateStatus.INTERVIEWING,
                            'interviewed': CandidateStatus.INTERVIEWING,
                            'offered': CandidateStatus.OFFER_EXTENDED,
                            'hired': CandidateStatus.HIRED,
                            'rejected': CandidateStatus.REJECTED,
                            'withdrawn': CandidateStatus.WITHDRAWN
                        }
                        candidate_status = stage_to_status.get(candidate_data['stage'])
                    
                    # Skip if status doesn't match
                    if candidate_status != status:
                        continue
                
                # Check date filter
                last_activity = candidate_data.get('last_activity_date')
                if not last_activity or not (start_date <= last_activity <= end_date):
                    continue
                
                candidate_ids.append(candidate_id)
            
            return candidate_ids
            
        except Exception as e:
            logger.error(f"Error fetching cohort candidates: {e}")
            return []
    
    def _calculate_cohort_metrics(
        self,
        journeys: List[CandidateJourneyMetrics]
    ) -> Dict[str, Any]:
        """
        Calculate aggregated metrics for a cohort of candidates.
        
        Args:
            journeys: List of journey metrics for candidates in the cohort
            
        Returns:
            Dict[str, Any]: Aggregated metrics
        """
        if not journeys:
            return {
                "count": 0,
                "avg_time_in_pipeline": None,
                "avg_time_to_decision": None,
                "status_distribution": {},
                "conversion_rates": {}
            }
        
        # Initialize metrics
        metrics = {
            "count": len(journeys),
            "avg_time_in_pipeline": None,
            "avg_time_to_first_contact": None,
            "avg_time_to_decision": None,
            "status_distribution": defaultdict(int),
            "conversion_rates": {},
            "avg_interaction_count": 0
        }
        
        # Calculate time-based metrics
        time_in_pipeline = [j.time_in_pipeline for j in journeys if j.time_in_pipeline is not None]
        if time_in_pipeline:
            metrics["avg_time_in_pipeline"] = sum(time_in_pipeline) / len(time_in_pipeline)
        
        time_to_first_contact = [j.time_to_first_contact for j in journeys if j.time_to_first_contact is not None]
        if time_to_first_contact:
            metrics["avg_time_to_first_contact"] = sum(time_to_first_contact) / len(time_to_first_contact)
        
        time_to_decision = [j.time_to_decision for j in journeys if j.time_to_decision is not None]
        if time_to_decision:
            metrics["avg_time_to_decision"] = sum(time_to_decision) / len(time_to_decision)
        
        # Calculate status distribution
        for journey in journeys:
            if journey.current_status:
                metrics["status_distribution"][journey.current_status.value] += 1
        
        # Convert defaultdict to regular dict
        metrics["status_distribution"] = dict(metrics["status_distribution"])
        
        # Calculate percentages for status distribution
        total = len(journeys)
        for status, count in metrics["status_distribution"].items():
            metrics["status_distribution"][status] = {
                "count": count,
                "percentage": (count / total) * 100
            }
        
        # Calculate conversion rates between statuses
        status_order = [
            CandidateStatus.NEW,
            CandidateStatus.CONTACTED,
            CandidateStatus.SCREENING,
            CandidateStatus.INTERVIEWING,
            CandidateStatus.OFFER_PENDING,
            CandidateStatus.OFFER_EXTENDED,
            CandidateStatus.OFFER_ACCEPTED,
            CandidateStatus.HIRED
        ]
        
        for i in range(len(status_order) - 1):
            current_status = status_order[i]
            next_status = status_order[i + 1]
            
            current_count = metrics["status_distribution"].get(current_status.value, {}).get("count", 0)
            next_count = metrics["status_distribution"].get(next_status.value, {}).get("count", 0)
            
            if current_count > 0:
                metrics["conversion_rates"][f"{current_status.value}_to_{next_status.value}"] = (next_count / current_count) * 100
        
        # Calculate average interaction count
        metrics["avg_interaction_count"] = sum(j.interaction_count for j in journeys) / len(journeys)
        
        return metrics
    
    async def generate_synthetic_data(self, candidate_count: int = 100) -> None:
        """
        Generate synthetic data for testing the journey metrics dashboard.
        This is only for development/testing purposes.
        
        Args:
            candidate_count: Number of candidates to generate
        """
        import random
        from uuid import uuid4
        
        logger.info(f"Generating synthetic journey data for {candidate_count} candidates")
        
        # First, make sure we have some jobs in the system
        job_ids = []
        job_keys = await self.redis_client.keys("job:*")
        
        if job_keys:
            # Extract job IDs from keys
            for key in job_keys:
                parts = key.split(":")
                if len(parts) == 2:
                    job_ids.append(parts[1])
        
        # If no jobs found, create some
        if not job_ids:
            for i in range(5):
                job_id = str(uuid4())
                job_data = {
                    'id': job_id,
                    'title': f"Test Job {i+1}",
                    'status': 'active',
                    'posting_date': datetime.now() - timedelta(days=random.randint(10, 90)),
                    'department': random.choice(['Engineering', 'Sales', 'Marketing', 'HR', 'Operations']),
                    'location': random.choice(['Remote', 'New York', 'San Francisco', 'Tokyo', 'London'])
                }
                
                # Store job in Redis
                job_key = f"job:{job_id}"
                await self.redis_client.set(job_key, str(job_data))
                
                job_ids.append(job_id)
        
        # Generate journey data for candidates
        for i in range(candidate_count):
            candidate_id = str(uuid4())
            job_id = random.choice(job_ids)
            
            # Generate random journey progression
            journey_length = random.randint(2, 7)  # Number of status changes
            
            # Status progression options with probabilities
            # Each tuple is (status, agent_type, probability of advancing to next stage)
            progression = [
                (CandidateStatus.NEW, AgentType.SOURCING, 0.9),
                (CandidateStatus.CONTACTED, AgentType.ENGAGEMENT, 0.7),
                (CandidateStatus.SCREENING, AgentType.SCREENING, 0.6),
                (CandidateStatus.INTERVIEWING, None, 0.5),
                (CandidateStatus.OFFER_PENDING, None, 0.8),
                (CandidateStatus.OFFER_EXTENDED, AgentType.ENGAGEMENT, 0.7)
            ]
            
            # Final statuses with probabilities
            final_statuses = [
                (CandidateStatus.OFFER_DECLINED, 0.3),
                (CandidateStatus.OFFER_ACCEPTED, 0.4),
                (CandidateStatus.HIRED, 0.3)
            ]
            
            # Rejection can happen at any stage
            rejection_probs = [0.1, 0.3, 0.4, 0.5, 0.2, 0.0]
            
            # Start date for the journey
            start_date = datetime.now() - timedelta(days=random.randint(10, 90))
            current_date = start_date
            
            # Create initial candidate data
            match_score = random.uniform(60, 95)
            candidate_data = {
                'id': candidate_id,
                'job_id': job_id,
                'name': f"Candidate {i+1}",
                'stage': 'sourced',  # Initial stage
                'match_score': match_score,
                'first_contact_date': None,
                'last_activity_date': current_date,
                'response_rate': None
            }
            
            # Store candidate in Redis
            candidate_key = f"candidate:{candidate_id}"
            job_candidate_key = f"job:{job_id}:candidate:{candidate_id}"
            
            await self.redis_client.set(candidate_key, str(candidate_data))
            await self.redis_client.set(job_candidate_key, str(candidate_data))
            
            # Generate journey events
            events = []
            max_stages = min(journey_length, len(progression))
            
            for stage_idx in range(max_stages):
                status, agent_type, advance_prob = progression[stage_idx]
                
                # Add some random time between stages
                current_date += timedelta(days=random.randint(1, 5), 
                                         hours=random.randint(0, 23),
                                         minutes=random.randint(0, 59))
                
                # Create the event
                description = f"Candidate moved to {status.value} stage"
                metadata = {
                    'job_id': job_id,
                    'match_score': match_score
                }
                
                if status == CandidateStatus.CONTACTED:
                    candidate_data['first_contact_date'] = current_date
                    candidate_data['response_rate'] = random.uniform(0.5, 1.0)
                    metadata['response_rate'] = candidate_data['response_rate']
                
                # Track the event
                await self.track_journey_event(
                    candidate_id=candidate_id,
                    status=status,
                    job_id=job_id,
                    agent_type=agent_type,
                    description=description,
                    metadata=metadata
                )
                
                # Update candidate data
                candidate_data['stage'] = status.value
                candidate_data['last_activity_date'] = current_date
                
                # Check if candidate is rejected at this stage
                if random.random() < rejection_probs[stage_idx]:
                    # Rejected
                    current_date += timedelta(days=random.randint(1, 3))
                    
                    await self.track_journey_event(
                        candidate_id=candidate_id,
                        status=CandidateStatus.REJECTED,
                        job_id=job_id,
                        agent_type=AgentType.SCREENING if stage_idx < 2 else None,
                        description="Candidate was rejected",
                        metadata={
                            'job_id': job_id,
                            'reason': random.choice([
                                'Not enough experience',
                                'Skills mismatch',
                                'Cultural fit concerns',
                                'Salary expectations too high'
                            ])
                        }
                    )
                    
                    candidate_data['stage'] = 'rejected'
                    candidate_data['last_activity_date'] = current_date
                    break
                
                # Check if we should advance to next stage
                if random.random() > advance_prob:
                    break
            
            # If candidate reached the end of progression, assign a final status
            if candidate_data['stage'] not in ['rejected', 'hired', 'withdrawn']:
                final_status, prob = random.choices(final_statuses, weights=[s[1] for s in final_statuses])[0]
                
                current_date += timedelta(days=random.randint(1, 5))
                
                await self.track_journey_event(
                    candidate_id=candidate_id,
                    status=final_status,
                    job_id=job_id,
                    agent_type=AgentType.ENGAGEMENT if final_status in [
                        CandidateStatus.OFFER_ACCEPTED, CandidateStatus.OFFER_DECLINED
                    ] else None,
                    description=f"Candidate {final_status.value}",
                    metadata={
                        'job_id': job_id
                    }
                )
                
                candidate_data['stage'] = final_status.value
                candidate_data['last_activity_date'] = current_date
                
                # If candidate was hired, add hire date
                if final_status == CandidateStatus.HIRED:
                    hire_date = current_date + timedelta(days=random.randint(1, 10))
                    candidate_data['hire_date'] = hire_date
                    
                    # Add one final event for the actual hire
                    await self.track_journey_event(
                        candidate_id=candidate_id,
                        status=CandidateStatus.HIRED,
                        job_id=job_id,
                        description="Candidate was hired",
                        metadata={
                            'job_id': job_id,
                            'hire_date': hire_date,
                            'onboarding_date': hire_date + timedelta(days=random.randint(7, 14))
                        }
                    )
            
            # Update candidate data with final status
            await self.redis_client.set(candidate_key, str(candidate_data))
            await self.redis_client.set(job_candidate_key, str(candidate_data))
            
        logger.info("Synthetic journey data generation completed")
