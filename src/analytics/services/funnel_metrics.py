"""
Recruitment funnel metrics service for RecruitPro AI.

This service provides analytics on the recruitment funnel, including
candidate progression through stages, conversion rates, and time metrics.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict

from src.analytics.models.metrics import (
    RecruitmentMetrics,
    FunnelStage,
    FunnelStageMetrics,
    TimeFrame
)
from src.utils.config import REDIS_HOST, REDIS_PORT, REDIS_DB
from src.utils.redis_client import RedisClient

# Configure logging
logger = logging.getLogger(__name__)


class FunnelMetricsService:
    """Service for calculating and retrieving recruitment funnel metrics."""
    
    def __init__(self, redis_client: Optional[RedisClient] = None):
        """
        Initialize the FunnelMetricsService.
        
        Args:
            redis_client: Optional Redis client for metrics storage
        """
        self.redis_client = redis_client or RedisClient(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB
        )
        
    async def get_funnel_metrics(
        self,
        time_frame: TimeFrame,
        job_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        compare_with_previous: bool = True
    ) -> RecruitmentMetrics:
        """
        Get recruitment funnel metrics for the specified parameters.
        
        Args:
            time_frame: Time frame for the metrics
            job_id: Optional job ID to filter metrics
            start_date: Start date for custom time frame
            end_date: End date for custom time frame
            compare_with_previous: Whether to include comparison with previous period
            
        Returns:
            RecruitmentMetrics: Calculated recruitment metrics
        """
        # Determine date range based on time frame
        if time_frame == TimeFrame.CUSTOM and (not start_date or not end_date):
            raise ValueError("Custom time frame requires start_date and end_date")
            
        if not start_date or not end_date:
            start_date, end_date = self._calculate_date_range(time_frame)
        
        # Initialize metrics object
        metrics = RecruitmentMetrics(
            job_id=job_id,
            time_frame=time_frame,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get raw data
        candidates_data = await self._fetch_candidate_data(job_id, start_date, end_date)
        
        if not candidates_data:
            logger.warning(f"No candidate data found for the specified parameters: "
                          f"job_id={job_id}, start_date={start_date}, end_date={end_date}")
            return metrics
        
        # Calculate funnel stage metrics
        funnel_metrics = self._calculate_funnel_stages(candidates_data)
        metrics.funnel_stages = funnel_metrics
        
        # Calculate time-to-fill and time-to-hire
        time_metrics = self._calculate_time_metrics(candidates_data)
        metrics.time_to_fill = time_metrics.get('time_to_fill')
        metrics.time_to_hire = time_metrics.get('time_to_hire')
        
        # Calculate additional metrics
        metrics.total_candidates = len(candidates_data)
        metrics.total_hires = funnel_metrics.get(FunnelStage.HIRED, FunnelStageMetrics(stage=FunnelStage.HIRED)).count
        
        if metrics.total_hires > 0:
            metrics.candidates_per_hire = metrics.total_candidates / metrics.total_hires
        
        # Calculate offer acceptance rate
        offers = funnel_metrics.get(FunnelStage.OFFERED, FunnelStageMetrics(stage=FunnelStage.OFFERED)).count
        if offers > 0:
            metrics.offer_acceptance_rate = (metrics.total_hires / offers) * 100
        
        # Get active jobs count
        metrics.total_active_jobs = await self._get_active_jobs_count(job_id)
        
        # Compare with previous period if requested
        if compare_with_previous:
            prev_start, prev_end = self._calculate_previous_period(start_date, end_date)
            previous_metrics = await self.get_funnel_metrics(
                time_frame=TimeFrame.CUSTOM,
                job_id=job_id,
                start_date=prev_start,
                end_date=prev_end,
                compare_with_previous=False  # Avoid recursive comparison
            )
            
            # Update comparison values in funnel stages
            for stage, stage_metrics in metrics.funnel_stages.items():
                if stage in previous_metrics.funnel_stages and previous_metrics.funnel_stages[stage].count > 0:
                    prev_count = previous_metrics.funnel_stages[stage].count
                    curr_count = stage_metrics.count
                    stage_metrics.comparison_to_previous = ((curr_count - prev_count) / prev_count) * 100
        
        return metrics
    
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
    
    def _calculate_previous_period(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Tuple[datetime, datetime]:
        """
        Calculate the previous period based on current period dates.
        
        Args:
            start_date: Start date of current period
            end_date: End date of current period
            
        Returns:
            Tuple[datetime, datetime]: Start and end dates for previous period
        """
        period_length = end_date - start_date
        prev_end = start_date
        prev_start = start_date - period_length
        
        return prev_start, prev_end
    
    async def _fetch_candidate_data(
        self,
        job_id: Optional[str],
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch candidate data from the database for the specified parameters.
        
        Args:
            job_id: Optional job ID to filter candidates
            start_date: Start date for the query
            end_date: End date for the query
            
        Returns:
            List[Dict[str, Any]]: List of candidate data records
        """
        # In a real implementation, this would fetch data from a database
        # For this demo, we'll generate synthetic data
        try:
            # For demo purposes, we're returning synthetic data
            # In a real implementation, this would query the database
            candidates = []
            
            # Get candidate IDs from Redis (all candidates or filtered by job)
            pattern = f"candidate:*" if not job_id else f"job:{job_id}:candidate:*"
            candidate_keys = await self.redis_client.keys(pattern)
            
            for key in candidate_keys:
                candidate_data = await self.redis_client.get(key)
                if candidate_data:
                    candidate = eval(candidate_data)  # In reality, use proper JSON deserialization
                    
                    # Check if candidate's activity falls within date range
                    candidate_date = candidate.get('last_activity_date', None)
                    if candidate_date and start_date <= candidate_date <= end_date:
                        candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error fetching candidate data: {e}")
            return []
    
    def _calculate_funnel_stages(
        self,
        candidates_data: List[Dict[str, Any]]
    ) -> Dict[FunnelStage, FunnelStageMetrics]:
        """
        Calculate metrics for each stage in the recruitment funnel.
        
        Args:
            candidates_data: List of candidate data records
            
        Returns:
            Dict[FunnelStage, FunnelStageMetrics]: Metrics for each funnel stage
        """
        # Initialize counters for each stage
        stage_counts = {stage: 0 for stage in FunnelStage}
        stage_times = {stage: [] for stage in FunnelStage}
        
        # Count candidates in each stage and collect time data
        for candidate in candidates_data:
            stage = candidate.get('stage', None)
            if stage and stage in FunnelStage:
                stage_counts[stage] += 1
                
                # Collect time in stage data if available
                time_in_stage = candidate.get('time_in_stage', None)
                if time_in_stage is not None:
                    stage_times[stage].append(time_in_stage)
        
        # Calculate total candidates for percentage calculation
        total_candidates = sum(stage_counts.values())
        
        # Initialize metrics for each stage
        funnel_metrics = {}
        
        for stage, count in stage_counts.items():
            metrics = FunnelStageMetrics(stage=stage, count=count)
            
            # Calculate percentage of total
            if total_candidates > 0:
                metrics.percentage = (count / total_candidates) * 100
                
            # Calculate average time in stage
            if stage_times[stage]:
                metrics.average_time_in_stage = sum(stage_times[stage]) / len(stage_times[stage])
                
            # Calculate conversion rate to next stage
            stages_list = list(FunnelStage)
            stage_index = stages_list.index(stage)
            
            if stage_index < len(stages_list) - 1:
                next_stage = stages_list[stage_index + 1]
                if count > 0:
                    metrics.conversion_rate = (stage_counts[next_stage] / count) * 100
            
            funnel_metrics[stage] = metrics
            
        return funnel_metrics
    
    def _calculate_time_metrics(
        self,
        candidates_data: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate time-based recruitment metrics.
        
        Args:
            candidates_data: List of candidate data records
            
        Returns:
            Dict[str, float]: Dictionary of calculated time metrics
        """
        fill_times = []
        hire_times = []
        
        for candidate in candidates_data:
            if candidate.get('stage') == FunnelStage.HIRED:
                # Time to fill: from job posting to hire
                if 'posting_date' in candidate and 'hire_date' in candidate:
                    fill_time = (candidate['hire_date'] - candidate['posting_date']).days
                    fill_times.append(fill_time)
                
                # Time to hire: from first contact to hire
                if 'first_contact_date' in candidate and 'hire_date' in candidate:
                    hire_time = (candidate['hire_date'] - candidate['first_contact_date']).days
                    hire_times.append(hire_time)
        
        metrics = {}
        
        if fill_times:
            metrics['time_to_fill'] = sum(fill_times) / len(fill_times)
            
        if hire_times:
            metrics['time_to_hire'] = sum(hire_times) / len(hire_times)
            
        return metrics
    
    async def _get_active_jobs_count(self, job_id: Optional[str] = None) -> int:
        """
        Get the count of active jobs in the system.
        
        Args:
            job_id: Optional job ID to check if active
            
        Returns:
            int: Count of active jobs
        """
        try:
            if job_id:
                # Check if specific job is active
                job_key = f"job:{job_id}"
                job_data = await self.redis_client.get(job_key)
                if job_data:
                    job = eval(job_data)  # In reality, use proper JSON deserialization
                    return 1 if job.get('status') == 'active' else 0
                return 0
            else:
                # Count all active jobs
                job_keys = await self.redis_client.keys("job:*")
                active_count = 0
                
                for key in job_keys:
                    job_data = await self.redis_client.get(key)
                    if job_data:
                        job = eval(job_data)  # In reality, use proper JSON deserialization
                        if job.get('status') == 'active':
                            active_count += 1
                
                return active_count
                
        except Exception as e:
            logger.error(f"Error fetching active jobs count: {e}")
            return 0
    
    async def generate_synthetic_data(self, job_count: int = 5, candidates_per_job: int = 50) -> None:
        """
        Generate synthetic data for testing the analytics dashboard.
        This is only for development/testing purposes.
        
        Args:
            job_count: Number of jobs to generate
            candidates_per_job: Number of candidates per job
        """
        import random
        from uuid import uuid4
        
        logger.info(f"Generating synthetic data: {job_count} jobs with {candidates_per_job} candidates each")
        
        # Generate job data
        for i in range(job_count):
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
            
            # Generate candidates for this job
            stages = list(FunnelStage)
            stage_distribution = [50, 30, 20, 15, 10, 5, 10, 5]  # Progressive filtering through stages
            
            candidates_left = candidates_per_job
            for stage_idx, count_in_stage in enumerate(stage_distribution):
                if stage_idx >= len(stages) or candidates_left <= 0:
                    break
                    
                # Adjust count to not exceed candidates_left
                actual_count = min(count_in_stage, candidates_left)
                candidates_left -= actual_count
                
                stage = stages[stage_idx]
                
                for j in range(actual_count):
                    candidate_id = str(uuid4())
                    
                    # Calculate dates for the candidate's journey
                    posting_date = job_data['posting_date']
                    first_contact_date = posting_date + timedelta(days=random.randint(1, 10))
                    current_date = first_contact_date
                    
                    # Add time for each previous stage
                    for k in range(stage_idx):
                        current_date += timedelta(days=random.randint(3, 7))
                    
                    # Set hire date if hired
                    hire_date = None
                    if stage == FunnelStage.HIRED:
                        hire_date = current_date + timedelta(days=random.randint(1, 5))
                    
                    # Create candidate data
                    candidate_data = {
                        'id': candidate_id,
                        'job_id': job_id,
                        'name': f"Candidate {job_id[:4]}-{j+1}",
                        'stage': stage.value,
                        'posting_date': posting_date,
                        'first_contact_date': first_contact_date,
                        'last_activity_date': current_date,
                        'hire_date': hire_date,
                        'time_in_stage': random.randint(1, 14),  # days
                        'match_score': random.uniform(60, 95),
                        'skills': ['Python', 'FastAPI', 'Redis'] if random.random() > 0.5 else ['Java', 'Spring', 'SQL']
                    }
                    
                    # Store candidate in Redis
                    candidate_key = f"candidate:{candidate_id}"
                    job_candidate_key = f"job:{job_id}:candidate:{candidate_id}"
                    
                    await self.redis_client.set(candidate_key, str(candidate_data))
                    await self.redis_client.set(job_candidate_key, str(candidate_data))
                    
        logger.info("Synthetic data generation completed")
