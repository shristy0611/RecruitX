"""Analytics manager component."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import numpy as np

from tests.analytics.performance_analyzer import (
    PerformanceAnalyzer,
    PerformanceMetrics,
    PerformanceInsight
)
from tests.analytics.visualizer import AnalyticsVisualizer
from tests.complex_system.state_tracker import SystemState
from tests.complex_system.emergent_detector import EmergentBehavior
from tests.ai_pipeline.test_executor import TestResult

logger = logging.getLogger(__name__)

class AnalyticsManager:
    """Manages analytics components and orchestrates analysis."""
    
    def __init__(
        self,
        output_dir: str,
        analysis_interval: float = 60.0,  # 1 minute
        max_history: int = 1000,
        min_confidence: float = 0.7,
        anomaly_threshold: float = 2.0
    ):
        """Initialize manager.
        
        Args:
            output_dir: Directory for output files
            analysis_interval: Interval between analyses
            max_history: Maximum history size
            min_confidence: Minimum confidence for insights
            anomaly_threshold: Threshold for anomaly detection
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.analysis_interval = analysis_interval
        self.max_history = max_history
        
        # Initialize components
        self.analyzer = PerformanceAnalyzer(
            metrics_window=analysis_interval * 10,
            min_confidence=min_confidence,
            anomaly_threshold=anomaly_threshold
        )
        
        self.visualizer = AnalyticsVisualizer(
            output_dir=output_dir,
            max_history=max_history
        )
        
        # Analysis state
        self.last_analysis: Optional[float] = None
        self.running = False
        self._analysis_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start analytics manager."""
        if self.running:
            logger.warning("Analytics manager already running")
            return
            
        self.running = True
        self._analysis_task = asyncio.create_task(self._analysis_loop())
        logger.info("Started analytics manager")
        
    async def stop(self):
        """Stop analytics manager."""
        if not self.running:
            return
            
        self.running = False
        if self._analysis_task:
            self._analysis_task.cancel()
            try:
                await self._analysis_task
            except asyncio.CancelledError:
                pass
            self._analysis_task = None
            
        logger.info("Stopped analytics manager")
        
    async def analyze_current_state(
        self,
        system_state: SystemState,
        test_results: List[TestResult],
        behaviors: List[EmergentBehavior]
    ) -> Tuple[List[PerformanceInsight], str]:
        """Analyze current system state.
        
        Args:
            system_state: Current system state
            test_results: Recent test results
            behaviors: Detected behaviors
            
        Returns:
            Tuple of insights and dashboard path
        """
        # Run analysis
        insights = await self.analyzer.analyze_performance(
            system_state,
            test_results,
            behaviors
        )
        
        # Update visualizer
        metrics = self.analyzer.metrics_history[-1]
        self.visualizer.add_metrics(metrics)
        self.visualizer.add_insights(insights)
        
        # Generate dashboard
        dashboard_path = self.visualizer.generate_dashboard()
        
        return insights, dashboard_path
        
    async def _analysis_loop(self):
        """Background analysis loop."""
        while self.running:
            try:
                now = datetime.now().timestamp()
                
                # Check if analysis is needed
                if (
                    self.last_analysis is None or
                    now - self.last_analysis >= self.analysis_interval
                ):
                    await self._run_scheduled_analysis()
                    self.last_analysis = now
                    
                # Sleep until next analysis
                sleep_time = max(
                    0.0,
                    self.analysis_interval - (
                        datetime.now().timestamp() - self.last_analysis
                    )
                )
                await asyncio.sleep(sleep_time)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}", exc_info=True)
                await asyncio.sleep(self.analysis_interval)
                
    async def _run_scheduled_analysis(self):
        """Run scheduled analysis."""
        try:
            # Get current state
            system_state = await self._get_current_state()
            test_results = await self._get_recent_test_results()
            behaviors = await self._get_detected_behaviors()
            
            # Run analysis
            insights, dashboard_path = await self.analyze_current_state(
                system_state,
                test_results,
                behaviors
            )
            
            # Log results
            if insights:
                logger.info(
                    f"Generated {len(insights)} insights - "
                    f"Dashboard: {dashboard_path}"
                )
                
            # Generate report if needed
            if self._should_generate_report():
                report_path = self.visualizer.generate_report()
                logger.info(f"Generated analytics report: {report_path}")
                
        except Exception as e:
            logger.error(f"Error in scheduled analysis: {e}", exc_info=True)
            
    async def _get_current_state(self) -> SystemState:
        """Get current system state.
        
        Returns:
            Current state
        """
        # TODO: Implement state retrieval
        return SystemState()
        
    async def _get_recent_test_results(self) -> List[TestResult]:
        """Get recent test results.
        
        Returns:
            List of results
        """
        # TODO: Implement result retrieval
        return []
        
    async def _get_detected_behaviors(self) -> List[EmergentBehavior]:
        """Get detected behaviors.
        
        Returns:
            List of behaviors
        """
        # TODO: Implement behavior retrieval
        return []
        
    def _should_generate_report(self) -> bool:
        """Check if report should be generated.
        
        Returns:
            True if report needed
        """
        # Generate report every hour
        if not self.last_analysis:
            return False
            
        now = datetime.now().timestamp()
        hours_since_last = (now - self.last_analysis) / 3600
        
        return hours_since_last >= 1.0 