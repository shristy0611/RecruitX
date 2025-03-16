"""Scalability Manager

This module implements comprehensive scalability features for the recruitment system.
It follows SOTA practices including:
1. Distributed processing with load balancing
2. Horizontal scaling with worker pools
3. Adaptive resource allocation
4. Fault tolerance and recovery
5. Real-time scaling metrics

The design is inspired by patterns in the OpenManus-main repository.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import aiohttp
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import psutil

logger = logging.getLogger(__name__)

@dataclass
class ScalingMetrics:
    """System scaling metrics."""
    worker_count: int
    active_workers: int
    queue_length: int
    processing_rate: float
    error_rate: float
    resource_utilization: float
    latency: float
    timestamp: datetime

@dataclass
class ScalingConfig:
    """Scalability configuration."""
    min_workers: int = 2
    max_workers: int = 10
    worker_spawn_threshold: float = 0.8
    worker_remove_threshold: float = 0.2
    queue_size_per_worker: int = 100
    scaling_check_interval: float = 5.0
    worker_timeout: float = 30.0
    retry_limit: int = 3

class WorkerNode:
    """Represents a worker node in the distributed system."""
    
    def __init__(self, worker_id: str):
        """Initialize worker node.
        
        Args:
            worker_id: Unique worker identifier
        """
        self.worker_id = worker_id
        self.status = "idle"
        self.current_task = None
        self.last_heartbeat = datetime.now()
        self.tasks_completed = 0
        self.errors = 0
        self.avg_processing_time = 0.0
        
    def update_metrics(self, processing_time: float):
        """Update worker metrics.
        
        Args:
            processing_time: Time taken to process task
        """
        self.tasks_completed += 1
        self.avg_processing_time = (
            (self.avg_processing_time * (self.tasks_completed - 1) + processing_time)
            / self.tasks_completed
        )

class ScalabilityManager:
    def __init__(
        self,
        config: Optional[ScalingConfig] = None,
        metrics_dir: Optional[str] = None
    ):
        """Initialize scalability manager.
        
        Args:
            config: Optional scaling configuration
            metrics_dir: Optional directory for metrics storage
        """
        self.config = config or ScalingConfig()
        self.metrics_dir = Path(metrics_dir) if metrics_dir else None
        if self.metrics_dir:
            self.metrics_dir.mkdir(parents=True, exist_ok=True)
            
        self.task_queue = asyncio.Queue()
        self.workers: Dict[str, WorkerNode] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.worker_pool = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self.scaling_monitor = None
        self._metrics_history: List[ScalingMetrics] = []
        
    async def start(self):
        """Start scalability services."""
        # Initialize minimum workers
        for i in range(self.config.min_workers):
            await self._spawn_worker(f"worker_{i}")
            
        # Start scaling monitor
        self.scaling_monitor = asyncio.create_task(self._monitor_scaling())
        
        logger.info(f"Scalability manager started with {self.config.min_workers} workers")
        
    async def stop(self):
        """Stop scalability services."""
        # Stop scaling monitor
        if self.scaling_monitor:
            self.scaling_monitor.cancel()
            
        # Stop all workers
        for worker_id in list(self.workers.keys()):
            await self._remove_worker(worker_id)
            
        # Shutdown worker pool
        self.worker_pool.shutdown()
        
        logger.info("Scalability manager stopped")
        
    async def submit_task(
        self,
        task_type: str,
        task_data: Any,
        priority: int = 0
    ) -> asyncio.Future:
        """Submit task for processing.
        
        Args:
            task_type: Type of task
            task_data: Task data
            priority: Task priority (higher = more important)
            
        Returns:
            Future for task result
        """
        # Create task future
        future = asyncio.Future()
        
        # Add to queue
        await self.task_queue.put({
            "id": f"task_{len(self.active_tasks)}",
            "type": task_type,
            "data": task_data,
            "priority": priority,
            "future": future,
            "retries": 0
        })
        
        # Scale up if needed
        await self._check_scaling()
        
        return future
        
    async def _spawn_worker(self, worker_id: str):
        """Spawn new worker node.
        
        Args:
            worker_id: Worker identifier
        """
        if len(self.workers) >= self.config.max_workers:
            logger.warning("Maximum workers reached")
            return
            
        # Create worker
        worker = WorkerNode(worker_id)
        self.workers[worker_id] = worker
        
        # Start worker task
        self.active_tasks[worker_id] = asyncio.create_task(
            self._worker_loop(worker)
        )
        
        logger.info(f"Spawned worker {worker_id}")
        
    async def _remove_worker(self, worker_id: str):
        """Remove worker node.
        
        Args:
            worker_id: Worker identifier
        """
        if worker_id not in self.workers:
            return
            
        # Cancel worker task
        if worker_id in self.active_tasks:
            self.active_tasks[worker_id].cancel()
            del self.active_tasks[worker_id]
            
        # Remove worker
        del self.workers[worker_id]
        
        logger.info(f"Removed worker {worker_id}")
        
    async def _worker_loop(self, worker: WorkerNode):
        """Main worker processing loop.
        
        Args:
            worker: Worker node
        """
        while True:
            try:
                # Get task from queue
                task = await self.task_queue.get()
                worker.status = "busy"
                worker.current_task = task
                
                # Process task
                start_time = datetime.now()
                try:
                    result = await self._process_task(task)
                    task["future"].set_result(result)
                    
                    # Update metrics
                    processing_time = (datetime.now() - start_time).total_seconds()
                    worker.update_metrics(processing_time)
                    
                except Exception as e:
                    logger.error(f"Error processing task: {e}")
                    worker.errors += 1
                    
                    # Retry if possible
                    if task["retries"] < self.config.retry_limit:
                        task["retries"] += 1
                        await self.task_queue.put(task)
                    else:
                        task["future"].set_exception(e)
                        
                finally:
                    worker.status = "idle"
                    worker.current_task = None
                    worker.last_heartbeat = datetime.now()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                
    async def _process_task(self, task: Dict[str, Any]) -> Any:
        """Process task in worker pool.
        
        Args:
            task: Task to process
            
        Returns:
            Task result
        """
        # Submit to thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.worker_pool,
            self._execute_task,
            task
        )
        
    def _execute_task(self, task: Dict[str, Any]) -> Any:
        """Execute task in worker thread.
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
        """
        # Implement task execution logic
        pass
        
    async def _monitor_scaling(self):
        """Monitor system and adjust scaling."""
        while True:
            try:
                # Collect metrics
                metrics = self._collect_metrics()
                self._metrics_history.append(metrics)
                
                # Save metrics
                if self.metrics_dir:
                    self._save_metrics(metrics)
                    
                # Check scaling needs
                await self._check_scaling()
                
                # Check worker health
                await self._check_worker_health()
                
                # Wait for next check
                await asyncio.sleep(self.config.scaling_check_interval)
                
            except Exception as e:
                logger.error(f"Error in scaling monitor: {e}")
                
    def _collect_metrics(self) -> ScalingMetrics:
        """Collect current scaling metrics.
        
        Returns:
            Current scaling metrics
        """
        active_workers = sum(1 for w in self.workers.values() if w.status == "busy")
        
        return ScalingMetrics(
            worker_count=len(self.workers),
            active_workers=active_workers,
            queue_length=self.task_queue.qsize(),
            processing_rate=self._calculate_processing_rate(),
            error_rate=self._calculate_error_rate(),
            resource_utilization=self._calculate_resource_utilization(),
            latency=self._calculate_average_latency(),
            timestamp=datetime.now()
        )
        
    def _calculate_processing_rate(self) -> float:
        """Calculate task processing rate.
        
        Returns:
            Tasks processed per second
        """
        total_completed = sum(w.tasks_completed for w in self.workers.values())
        if not self._metrics_history:
            return 0.0
            
        time_window = (datetime.now() - self._metrics_history[0].timestamp).total_seconds()
        return total_completed / time_window if time_window > 0 else 0.0
        
    def _calculate_error_rate(self) -> float:
        """Calculate task error rate.
        
        Returns:
            Error rate (0-1)
        """
        total_errors = sum(w.errors for w in self.workers.values())
        total_tasks = sum(w.tasks_completed for w in self.workers.values())
        return total_errors / total_tasks if total_tasks > 0 else 0.0
        
    def _calculate_resource_utilization(self) -> float:
        """Calculate system resource utilization.
        
        Returns:
            Resource utilization (0-1)
        """
        cpu_usage = psutil.cpu_percent() / 100
        memory_usage = psutil.virtual_memory().percent / 100
        return (cpu_usage + memory_usage) / 2
        
    def _calculate_average_latency(self) -> float:
        """Calculate average task processing latency.
        
        Returns:
            Average latency in seconds
        """
        latencies = [w.avg_processing_time for w in self.workers.values() if w.tasks_completed > 0]
        return np.mean(latencies) if latencies else 0.0
        
    async def _check_scaling(self):
        """Check and adjust system scaling."""
        metrics = self._collect_metrics()
        
        # Check if we need more workers
        if (
            metrics.resource_utilization > self.config.worker_spawn_threshold
            or metrics.queue_length > len(self.workers) * self.config.queue_size_per_worker
        ):
            # Spawn new worker
            worker_id = f"worker_{len(self.workers)}"
            await self._spawn_worker(worker_id)
            
        # Check if we can remove workers
        elif (
            metrics.resource_utilization < self.config.worker_remove_threshold
            and len(self.workers) > self.config.min_workers
        ):
            # Find least active worker
            least_active = min(
                self.workers.items(),
                key=lambda x: x[1].tasks_completed
            )
            await self._remove_worker(least_active[0])
            
    async def _check_worker_health(self):
        """Check health of workers and handle failures."""
        now = datetime.now()
        
        for worker_id, worker in list(self.workers.items()):
            # Check if worker is responsive
            if (now - worker.last_heartbeat).total_seconds() > self.config.worker_timeout:
                logger.warning(f"Worker {worker_id} unresponsive")
                
                # Handle any active task
                if worker.current_task:
                    task = worker.current_task
                    if task["retries"] < self.config.retry_limit:
                        task["retries"] += 1
                        await self.task_queue.put(task)
                    else:
                        task["future"].set_exception(
                            Exception("Worker timeout")
                        )
                        
                # Remove and replace worker
                await self._remove_worker(worker_id)
                await self._spawn_worker(f"worker_{len(self.workers)}")
                
    def _save_metrics(self, metrics: ScalingMetrics):
        """Save scaling metrics to file.
        
        Args:
            metrics: Scaling metrics to save
        """
        if not self.metrics_dir:
            return
            
        try:
            metrics_file = self.metrics_dir / f"scaling_{metrics.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            with open(metrics_file, "w") as f:
                json.dump({
                    "worker_count": metrics.worker_count,
                    "active_workers": metrics.active_workers,
                    "queue_length": metrics.queue_length,
                    "processing_rate": metrics.processing_rate,
                    "error_rate": metrics.error_rate,
                    "resource_utilization": metrics.resource_utilization,
                    "latency": metrics.latency,
                    "timestamp": metrics.timestamp.isoformat()
                }, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving metrics: {e}") 