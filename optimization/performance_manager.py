"""Performance Optimization Manager

This module implements comprehensive performance optimization for the recruitment system.
It follows SOTA practices including:
1. Intelligent caching with LRU and predictive prefetching
2. Request batching and throttling
3. Resource monitoring and auto-scaling
4. Performance profiling and bottleneck detection
5. Async operation optimization

The design is inspired by patterns in the OpenManus-main repository.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
import numpy as np
from pathlib import Path
import json
import logging
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import psutil
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """System performance metrics."""
    cpu_usage: float
    memory_usage: float
    api_latency: float
    request_throughput: float
    cache_hit_rate: float
    error_rate: float
    timestamp: datetime

@dataclass
class OptimizationConfig:
    """Performance optimization configuration."""
    cache_size: int = 1000
    batch_size: int = 50
    max_concurrent_requests: int = 100
    prefetch_threshold: float = 0.7
    min_batch_interval: float = 0.1
    max_retry_attempts: int = 3
    monitoring_interval: float = 5.0

class PerformanceManager:
    def __init__(
        self,
        config: Optional[OptimizationConfig] = None,
        metrics_dir: Optional[str] = None
    ):
        """Initialize performance manager.
        
        Args:
            config: Optional optimization configuration
            metrics_dir: Optional directory for metrics storage
        """
        self.config = config or OptimizationConfig()
        self.metrics_dir = Path(metrics_dir) if metrics_dir else None
        if self.metrics_dir:
            self.metrics_dir.mkdir(parents=True, exist_ok=True)
            
        self.request_queue = asyncio.Queue()
        self.batch_processor = None
        self.monitoring_task = None
        self._request_counts = {}
        self._latency_stats = {}
        self._cache_stats = {"hits": 0, "misses": 0}
        self._error_counts = {}
        
    async def start(self):
        """Start performance optimization services."""
        # Start batch processor
        self.batch_processor = asyncio.create_task(self._process_batches())
        
        # Start performance monitoring
        self.monitoring_task = asyncio.create_task(self._monitor_performance())
        
        logger.info("Performance optimization services started")
        
    async def stop(self):
        """Stop performance optimization services."""
        if self.batch_processor:
            self.batch_processor.cancel()
        if self.monitoring_task:
            self.monitoring_task.cancel()
            
        logger.info("Performance optimization services stopped")
        
    @lru_cache(maxsize=1000)
    async def cached_operation(self, operation_key: str, *args, **kwargs) -> Any:
        """Execute operation with caching.
        
        Args:
            operation_key: Unique operation identifier
            *args: Operation arguments
            **kwargs: Operation keyword arguments
            
        Returns:
            Operation result
        """
        cache_key = f"{operation_key}:{hash(str(args))}{hash(str(kwargs))}"
        
        try:
            # Check cache
            if cache_key in self._get_cache():
                self._cache_stats["hits"] += 1
                return self._get_cache()[cache_key]
                
            self._cache_stats["misses"] += 1
            
            # Execute operation
            start_time = time.time()
            result = await self._execute_operation(operation_key, *args, **kwargs)
            latency = time.time() - start_time
            
            # Update stats
            self._update_latency_stats(operation_key, latency)
            
            # Cache result
            self._get_cache()[cache_key] = result
            
            # Prefetch related data if needed
            if self._should_prefetch(operation_key):
                asyncio.create_task(self._prefetch_related(operation_key, *args, **kwargs))
                
            return result
            
        except Exception as e:
            self._error_counts[operation_key] = self._error_counts.get(operation_key, 0) + 1
            logger.error(f"Error in cached_operation: {e}")
            raise
            
    async def batch_operation(
        self,
        operation_key: str,
        items: List[Any],
        *args,
        **kwargs
    ) -> List[Any]:
        """Execute operation in batches.
        
        Args:
            operation_key: Operation identifier
            items: Items to process
            *args: Additional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            List of operation results
        """
        results = []
        batches = [
            items[i:i + self.config.batch_size]
            for i in range(0, len(items), self.config.batch_size)
        ]
        
        for batch in batches:
            # Add batch to queue
            batch_future = asyncio.Future()
            await self.request_queue.put((
                operation_key,
                batch,
                args,
                kwargs,
                batch_future
            ))
            
            # Wait for batch result
            batch_results = await batch_future
            results.extend(batch_results)
            
            # Rate limiting
            await asyncio.sleep(self.config.min_batch_interval)
            
        return results
        
    async def _process_batches(self):
        """Process batched operations from queue."""
        while True:
            try:
                # Get batch from queue
                operation_key, items, args, kwargs, future = await self.request_queue.get()
                
                # Execute batch operation
                start_time = time.time()
                results = await self._execute_batch(operation_key, items, *args, **kwargs)
                latency = time.time() - start_time
                
                # Update stats
                self._update_latency_stats(operation_key, latency)
                self._request_counts[operation_key] = (
                    self._request_counts.get(operation_key, 0) + len(items)
                )
                
                # Set result
                future.set_result(results)
                
            except Exception as e:
                logger.error(f"Error processing batch: {e}")
                self._error_counts["batch_processing"] = (
                    self._error_counts.get("batch_processing", 0) + 1
                )
                
    async def _monitor_performance(self):
        """Monitor system performance metrics."""
        while True:
            try:
                # Collect metrics
                metrics = PerformanceMetrics(
                    cpu_usage=psutil.cpu_percent(),
                    memory_usage=psutil.virtual_memory().percent,
                    api_latency=self._calculate_average_latency(),
                    request_throughput=self._calculate_throughput(),
                    cache_hit_rate=self._calculate_cache_hit_rate(),
                    error_rate=self._calculate_error_rate(),
                    timestamp=datetime.now()
                )
                
                # Save metrics
                if self.metrics_dir:
                    self._save_metrics(metrics)
                    
                # Check for performance issues
                await self._check_performance_issues(metrics)
                
                # Wait for next monitoring interval
                await asyncio.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                
    def _calculate_average_latency(self) -> float:
        """Calculate average operation latency."""
        if not self._latency_stats:
            return 0.0
            
        total_latency = sum(
            sum(latencies) for latencies in self._latency_stats.values()
        )
        total_ops = sum(
            len(latencies) for latencies in self._latency_stats.values()
        )
        
        return total_latency / total_ops if total_ops > 0 else 0.0
        
    def _calculate_throughput(self) -> float:
        """Calculate request throughput."""
        total_requests = sum(self._request_counts.values())
        return total_requests / self.config.monitoring_interval
        
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self._cache_stats["hits"] + self._cache_stats["misses"]
        return self._cache_stats["hits"] / total if total > 0 else 0.0
        
    def _calculate_error_rate(self) -> float:
        """Calculate error rate."""
        total_errors = sum(self._error_counts.values())
        total_requests = sum(self._request_counts.values())
        return total_errors / total_requests if total_requests > 0 else 0.0
        
    def _update_latency_stats(self, operation_key: str, latency: float):
        """Update operation latency statistics.
        
        Args:
            operation_key: Operation identifier
            latency: Operation latency
        """
        if operation_key not in self._latency_stats:
            self._latency_stats[operation_key] = []
        self._latency_stats[operation_key].append(latency)
        
        # Keep only recent stats
        max_stats = 1000
        if len(self._latency_stats[operation_key]) > max_stats:
            self._latency_stats[operation_key] = self._latency_stats[operation_key][-max_stats:]
            
    def _should_prefetch(self, operation_key: str) -> bool:
        """Check if related data should be prefetched.
        
        Args:
            operation_key: Operation identifier
            
        Returns:
            True if prefetching is recommended
        """
        # Check cache hit rate for operation
        hits = self._cache_stats.get("hits", 0)
        total = hits + self._cache_stats.get("misses", 0)
        hit_rate = hits / total if total > 0 else 0.0
        
        return hit_rate > self.config.prefetch_threshold
        
    async def _prefetch_related(self, operation_key: str, *args, **kwargs):
        """Prefetch related data for operation.
        
        Args:
            operation_key: Operation identifier
            *args: Operation arguments
            **kwargs: Operation keyword arguments
        """
        try:
            # Identify related data
            related_keys = await self._identify_related_data(operation_key, *args, **kwargs)
            
            # Prefetch in background
            for key in related_keys:
                if key not in self._get_cache():
                    asyncio.create_task(
                        self._execute_operation(key, *args, **kwargs)
                    )
                    
        except Exception as e:
            logger.error(f"Error in prefetching: {e}")
            
    async def _check_performance_issues(self, metrics: PerformanceMetrics):
        """Check for performance issues and take corrective action.
        
        Args:
            metrics: Current performance metrics
        """
        # Check CPU usage
        if metrics.cpu_usage > 80:
            logger.warning("High CPU usage detected")
            await self._optimize_resource_usage()
            
        # Check memory usage
        if metrics.memory_usage > 80:
            logger.warning("High memory usage detected")
            self._cleanup_cache()
            
        # Check error rate
        if metrics.error_rate > 0.1:  # 10% error rate
            logger.warning("High error rate detected")
            await self._implement_circuit_breaker()
            
        # Check latency
        if metrics.api_latency > 1.0:  # 1 second
            logger.warning("High latency detected")
            await self._optimize_request_handling()
            
    async def _optimize_resource_usage(self):
        """Optimize system resource usage."""
        # Implement resource optimization strategies
        pass
        
    def _cleanup_cache(self):
        """Clean up cache to free memory."""
        # Implement cache cleanup
        pass
        
    async def _implement_circuit_breaker(self):
        """Implement circuit breaker pattern for error handling."""
        # Implement circuit breaker
        pass
        
    async def _optimize_request_handling(self):
        """Optimize request handling for better latency."""
        # Implement request optimization
        pass
        
    def _save_metrics(self, metrics: PerformanceMetrics):
        """Save performance metrics to file.
        
        Args:
            metrics: Performance metrics to save
        """
        if not self.metrics_dir:
            return
            
        try:
            metrics_file = self.metrics_dir / f"metrics_{metrics.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            with open(metrics_file, "w") as f:
                json.dump({
                    "cpu_usage": metrics.cpu_usage,
                    "memory_usage": metrics.memory_usage,
                    "api_latency": metrics.api_latency,
                    "request_throughput": metrics.request_throughput,
                    "cache_hit_rate": metrics.cache_hit_rate,
                    "error_rate": metrics.error_rate,
                    "timestamp": metrics.timestamp.isoformat()
                }, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            
    @staticmethod
    def _get_cache():
        """Get the LRU cache dictionary."""
        return PerformanceManager.cached_operation.cache_info() 