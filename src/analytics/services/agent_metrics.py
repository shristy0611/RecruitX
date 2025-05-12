"""
Agent performance metrics service for RecruitPro AI.

This service tracks and analyzes the performance of various AI agents
in the system, including accuracy, response times, and throughput.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from src.analytics.models.metrics import (
    AgentPerformanceMetrics,
    AgentType,
    AgentMetricType,
    TimeFrame
)
from src.utils.config import REDIS_HOST, REDIS_PORT, REDIS_DB
from src.utils.redis_client import RedisClient

# Configure logging
logger = logging.getLogger(__name__)


class AgentMetricsService:
    """Service for tracking and analyzing agent performance metrics."""
    
    def __init__(self, redis_client: Optional[RedisClient] = None):
        """
        Initialize the AgentMetricsService.
        
        Args:
            redis_client: Optional Redis client for metrics storage
        """
        self.redis_client = redis_client or RedisClient(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB
        )
    
    async def get_agent_metrics(
        self,
        agent_type: AgentType,
        time_frame: TimeFrame,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        compare_with_previous: bool = True
    ) -> AgentPerformanceMetrics:
        """
        Get performance metrics for a specific agent.
        
        Args:
            agent_type: Type of agent to get metrics for
            time_frame: Time frame for the metrics
            start_date: Start date for custom time frame
            end_date: End date for custom time frame
            compare_with_previous: Whether to include comparison with previous period
            
        Returns:
            AgentPerformanceMetrics: Performance metrics for the agent
        """
        # Determine date range based on time frame
        if time_frame == TimeFrame.CUSTOM and (not start_date or not end_date):
            raise ValueError("Custom time frame requires start_date and end_date")
            
        if not start_date or not end_date:
            start_date, end_date = self._calculate_date_range(time_frame)
        
        # Initialize metrics object
        metrics = AgentPerformanceMetrics(
            agent_type=agent_type,
            time_frame=time_frame,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get agent request logs
        agent_logs = await self._fetch_agent_logs(agent_type, start_date, end_date)
        
        if not agent_logs:
            logger.warning(f"No logs found for agent {agent_type} in period "
                          f"{start_date} to {end_date}")
            return metrics
        
        # Calculate basic metrics
        metrics.request_count = len(agent_logs)
        metrics.success_count = sum(1 for log in agent_logs if log.get('status') == 'success')
        metrics.error_count = metrics.request_count - metrics.success_count
        
        # Calculate response times
        response_times = [log.get('response_time', 0) for log in agent_logs if 'response_time' in log]
        if response_times:
            metrics.average_response_time = sum(response_times) / len(response_times)
            metrics.peak_response_time = max(response_times)
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(agent_logs)
        metrics.metrics = performance_metrics
        
        # Compare with previous period if requested
        if compare_with_previous:
            previous_metrics = await self._get_previous_period_metrics(
                agent_type, start_date, end_date
            )
            
            if previous_metrics:
                # Calculate comparison percentages
                for metric_type, value in metrics.metrics.items():
                    if metric_type in previous_metrics.metrics and previous_metrics.metrics[metric_type] > 0:
                        prev_value = previous_metrics.metrics[metric_type]
                        change = ((value - prev_value) / prev_value) * 100
                        metrics.comparison[metric_type.value] = change
                
                # Compare request counts
                if previous_metrics.request_count > 0:
                    change = ((metrics.request_count - previous_metrics.request_count) / 
                             previous_metrics.request_count) * 100
                    metrics.comparison['request_count'] = change
                
                # Compare response times
                if (previous_metrics.average_response_time and 
                    previous_metrics.average_response_time > 0):
                    change = ((metrics.average_response_time - previous_metrics.average_response_time) / 
                             previous_metrics.average_response_time) * 100
                    metrics.comparison['average_response_time'] = change
        
        return metrics
    
    async def track_agent_request(
        self,
        agent_type: AgentType,
        request_id: str,
        status: str,
        response_time: Optional[float] = None,
        additional_metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track a single agent request for metrics purposes.
        
        Args:
            agent_type: Type of agent making the request
            request_id: Unique identifier for the request
            status: Status of the request (success, error)
            response_time: Time taken to process the request (ms)
            additional_metrics: Any additional metrics to track
        """
        try:
            log_data = {
                'timestamp': datetime.now(),
                'agent_type': agent_type.value,
                'request_id': request_id,
                'status': status,
                'response_time': response_time
            }
            
            # Add any additional metrics
            if additional_metrics:
                log_data.update(additional_metrics)
                
            # Store in Redis with TTL (e.g., 30 days)
            log_key = f"agent_log:{agent_type.value}:{request_id}"
            await self.redis_client.set(log_key, str(log_data), expire_seconds=30*24*60*60)
            
            # Update summary metrics
            await self._update_summary_metrics(agent_type, log_data)
                
        except Exception as e:
            logger.error(f"Error tracking agent request: {e}")
    
    def _calculate_date_range(self, time_frame: TimeFrame) -> tuple:
        """
        Calculate start and end dates based on time frame.
        
        Args:
            time_frame: Time frame for the metrics
            
        Returns:
            tuple: Start and end dates
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
    
    async def _fetch_agent_logs(
        self,
        agent_type: AgentType,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch agent request logs from Redis for the specified parameters.
        
        Args:
            agent_type: Type of agent to get logs for
            start_date: Start date for the query
            end_date: End date for the query
            
        Returns:
            List[Dict[str, Any]]: List of agent log records
        """
        try:
            # Get all logs for this agent type
            pattern = f"agent_log:{agent_type.value}:*"
            log_keys = await self.redis_client.keys(pattern)
            
            logs = []
            for key in log_keys:
                log_data_str = await self.redis_client.get(key)
                if log_data_str:
                    log_data = eval(log_data_str)  # In reality, use proper JSON deserialization
                    
                    # Check if log timestamp is within the date range
                    log_timestamp = log_data.get('timestamp')
                    if log_timestamp and start_date <= log_timestamp <= end_date:
                        logs.append(log_data)
            
            return logs
            
        except Exception as e:
            logger.error(f"Error fetching agent logs: {e}")
            return []
    
    def _calculate_performance_metrics(
        self,
        agent_logs: List[Dict[str, Any]]
    ) -> Dict[AgentMetricType, float]:
        """
        Calculate performance metrics from agent logs.
        
        Args:
            agent_logs: List of agent log records
            
        Returns:
            Dict[AgentMetricType, float]: Dictionary of calculated metrics
        """
        metrics = {}
        
        # Calculate success rate (can be used as a proxy for accuracy)
        success_count = sum(1 for log in agent_logs if log.get('status') == 'success')
        total_count = len(agent_logs)
        
        if total_count > 0:
            accuracy = (success_count / total_count) * 100
            metrics[AgentMetricType.ACCURACY] = accuracy
        
        # Calculate latency metrics
        response_times = [log.get('response_time', 0) for log in agent_logs if 'response_time' in log]
        if response_times:
            metrics[AgentMetricType.LATENCY] = sum(response_times) / len(response_times)
        
        # Calculate throughput (requests per day)
        if agent_logs:
            first_log = min(agent_logs, key=lambda log: log.get('timestamp', datetime.min))
            last_log = max(agent_logs, key=lambda log: log.get('timestamp', datetime.min))
            
            first_timestamp = first_log.get('timestamp', datetime.min)
            last_timestamp = last_log.get('timestamp', datetime.min)
            
            time_span = (last_timestamp - first_timestamp).total_seconds()
            if time_span > 0:
                # Calculate requests per day
                throughput = (total_count / time_span) * 86400  # 86400 seconds in a day
                metrics[AgentMetricType.THROUGHPUT] = throughput
        
        # Calculate error rate
        if total_count > 0:
            error_rate = ((total_count - success_count) / total_count) * 100
            metrics[AgentMetricType.ERROR_RATE] = error_rate
        
        # Extract additional metrics if available
        for log in agent_logs:
            if 'precision' in log:
                metrics.setdefault(AgentMetricType.PRECISION, 0)
                metrics[AgentMetricType.PRECISION] += log['precision']
                
            if 'recall' in log:
                metrics.setdefault(AgentMetricType.RECALL, 0)
                metrics[AgentMetricType.RECALL] += log['recall']
                
            if 'f1_score' in log:
                metrics.setdefault(AgentMetricType.F1_SCORE, 0)
                metrics[AgentMetricType.F1_SCORE] += log['f1_score']
                
            if 'explanation_quality' in log:
                metrics.setdefault(AgentMetricType.EXPLANATION_QUALITY, 0)
                metrics[AgentMetricType.EXPLANATION_QUALITY] += log['explanation_quality']
        
        # Average out any accumulated metrics
        for metric_type in [
            AgentMetricType.PRECISION,
            AgentMetricType.RECALL,
            AgentMetricType.F1_SCORE,
            AgentMetricType.EXPLANATION_QUALITY
        ]:
            if metric_type in metrics:
                metrics[metric_type] = metrics[metric_type] / total_count
        
        return metrics
    
    async def _get_previous_period_metrics(
        self,
        agent_type: AgentType,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[AgentPerformanceMetrics]:
        """
        Get metrics for the previous period for comparison.
        
        Args:
            agent_type: Type of agent
            start_date: Start date of current period
            end_date: End date of current period
            
        Returns:
            Optional[AgentPerformanceMetrics]: Metrics for previous period
        """
        # Calculate the previous period
        period_length = end_date - start_date
        prev_end = start_date
        prev_start = start_date - period_length
        
        # Get metrics for the previous period
        previous_metrics = await self.get_agent_metrics(
            agent_type=agent_type,
            time_frame=TimeFrame.CUSTOM,
            start_date=prev_start,
            end_date=prev_end,
            compare_with_previous=False  # Avoid recursive comparison
        )
        
        return previous_metrics
    
    async def _update_summary_metrics(
        self,
        agent_type: AgentType,
        log_data: Dict[str, Any]
    ) -> None:
        """
        Update summary metrics in Redis for real-time tracking.
        
        Args:
            agent_type: Type of agent
            log_data: Log data to incorporate
        """
        try:
            # Get current date for daily metrics
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Update request count
            daily_count_key = f"agent_metrics:{agent_type.value}:count:{today}"
            await self.redis_client.incr(daily_count_key)
            
            # Set TTL for daily metrics (30 days)
            await self.redis_client.expire(daily_count_key, 30*24*60*60)
            
            # Update success count if applicable
            if log_data.get('status') == 'success':
                success_key = f"agent_metrics:{agent_type.value}:success:{today}"
                await self.redis_client.incr(success_key)
                await self.redis_client.expire(success_key, 30*24*60*60)
            
            # Update response time metrics if available
            response_time = log_data.get('response_time')
            if response_time is not None:
                # Store response times in a sorted set for percentile calculations
                response_time_key = f"agent_metrics:{agent_type.value}:response_times:{today}"
                await self.redis_client.zadd(response_time_key, {str(datetime.now().timestamp()): response_time})
                await self.redis_client.expire(response_time_key, 30*24*60*60)
                
        except Exception as e:
            logger.error(f"Error updating summary metrics: {e}")
    
    async def generate_synthetic_data(self, days_back: int = 30) -> None:
        """
        Generate synthetic data for testing the agent metrics dashboard.
        This is only for development/testing purposes.
        
        Args:
            days_back: Number of days of historical data to generate
        """
        import random
        from uuid import uuid4
        
        logger.info(f"Generating synthetic agent metrics data for {days_back} days")
        
        # Generate data for each agent type
        for agent_type in AgentType:
            # Generate varying numbers of requests per day
            for day in range(days_back, 0, -1):
                # Date for this batch of logs
                log_date = datetime.now() - timedelta(days=day)
                
                # Number of requests for this agent on this day (with some variability)
                base_requests = {
                    AgentType.SOURCING: 50,
                    AgentType.MATCHING: 80,
                    AgentType.SCREENING: 60,
                    AgentType.ENGAGEMENT: 100,
                    AgentType.ORCHESTRATOR: 200
                }
                
                # Add randomness to request count
                request_count = int(base_requests[agent_type] * random.uniform(0.8, 1.2))
                
                # Generate logs for each request
                for i in range(request_count):
                    request_id = str(uuid4())
                    
                    # Most requests succeed, but some fail
                    status = "success" if random.random() < 0.95 else "error"
                    
                    # Generate response time with some variability
                    response_time = None
                    if status == "success":
                        base_time = {
                            AgentType.SOURCING: 2000,  # 2 seconds
                            AgentType.MATCHING: 1500,  # 1.5 seconds
                            AgentType.SCREENING: 3000,  # 3 seconds
                            AgentType.ENGAGEMENT: 1000,  # 1 second
                            AgentType.ORCHESTRATOR: 500   # 0.5 seconds
                        }
                        response_time = base_time[agent_type] * random.uniform(0.7, 1.5)
                    
                    # Additional metrics for some agent types
                    additional_metrics = {}
                    
                    if agent_type in [AgentType.MATCHING, AgentType.SCREENING]:
                        # Add ML-related metrics
                        additional_metrics['precision'] = random.uniform(0.85, 0.98)
                        additional_metrics['recall'] = random.uniform(0.80, 0.95)
                        additional_metrics['f1_score'] = (
                            2 * additional_metrics['precision'] * additional_metrics['recall'] /
                            (additional_metrics['precision'] + additional_metrics['recall'])
                        )
                    
                    if agent_type in [AgentType.MATCHING, AgentType.SOURCING, AgentType.SCREENING]:
                        # Add explanation quality metric
                        additional_metrics['explanation_quality'] = random.uniform(0.70, 0.95)
                    
                    # Create log data
                    timestamp = log_date + timedelta(
                        hours=random.randint(8, 17),  # Business hours
                        minutes=random.randint(0, 59),
                        seconds=random.randint(0, 59)
                    )
                    
                    log_data = {
                        'timestamp': timestamp,
                        'agent_type': agent_type.value,
                        'request_id': request_id,
                        'status': status,
                        'response_time': response_time,
                        **additional_metrics
                    }
                    
                    # Store in Redis with TTL (e.g., 30 days)
                    log_key = f"agent_log:{agent_type.value}:{request_id}"
                    await self.redis_client.set(log_key, str(log_data), expire_seconds=30*24*60*60)
                    
                    # Update summary metrics
                    await self._update_summary_metrics(agent_type, log_data)
                    
        logger.info("Synthetic agent metrics data generation completed")
