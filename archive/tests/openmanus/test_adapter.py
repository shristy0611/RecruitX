"""OpenManus test adapter for integrating with the testing framework."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import json

from tests.openmanus.agent_bridge import OpenManusBridge, OpenManusAgent, OpenManusMessage
from tests.complex_system.state_tracker import ComplexStateTracker, SystemState, AgentState
from tests.complex_system.emergent_detector import EmergentDetector, EmergentBehavior
from tests.ai_pipeline.test_generator import AITestGenerator, GeneratedTest
from tests.ai_pipeline.test_executor import AITestExecutor, TestResult

logger = logging.getLogger(__name__)

@dataclass
class TestAdapterConfig:
    """Configuration for OpenManus test adapter."""
    sync_interval: float = 1.0  # Sync interval in seconds
    state_buffer_size: int = 1000  # Maximum states to keep
    message_buffer_size: int = 1000  # Maximum messages to keep
    consensus_threshold: float = 0.67  # 67% for consensus
    retry_limit: int = 3  # Maximum retries for operations

class OpenManusTestAdapter:
    """Adapter for integrating OpenManus with testing framework."""
    
    def __init__(
        self,
        bridge: OpenManusBridge,
        state_tracker: ComplexStateTracker,
        emergent_detector: EmergentDetector,
        test_generator: AITestGenerator,
        test_executor: AITestExecutor,
        config: Optional[TestAdapterConfig] = None
    ):
        """Initialize the test adapter.
        
        Args:
            bridge: OpenManus bridge instance
            state_tracker: State tracker instance
            emergent_detector: Emergent detector instance
            test_generator: Test generator instance
            test_executor: Test executor instance
            config: Adapter configuration
        """
        self.bridge = bridge
        self.state_tracker = state_tracker
        self.emergent_detector = emergent_detector
        self.test_generator = test_generator
        self.test_executor = test_executor
        self.config = config or TestAdapterConfig()
        
        # Synchronization
        self.sync_task: Optional[asyncio.Task] = None
        self.running = False
        
        # State tracking
        self.last_sync: float = 0
        self.sync_errors: int = 0
        self.test_results: List[TestResult] = []
        
    async def start(self):
        """Start the adapter."""
        if self.running:
            logger.warning("Adapter already running")
            return
            
        self.running = True
        self.sync_task = asyncio.create_task(self._sync_loop())
        logger.info("Started OpenManus test adapter")
        
    async def stop(self):
        """Stop the adapter."""
        if not self.running:
            return
            
        self.running = False
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass
            self.sync_task = None
            
        logger.info("Stopped OpenManus test adapter")
        
    async def _sync_loop(self):
        """Main synchronization loop."""
        while self.running:
            try:
                # Sync states
                await self._sync_states()
                
                # Detect behaviors
                await self._detect_behaviors()
                
                # Generate and run tests
                await self._run_tests()
                
                # Update metrics
                self._update_metrics()
                
                # Reset error counter on success
                self.sync_errors = 0
                
            except Exception as e:
                logger.error(f"Error in sync loop: {str(e)}")
                self.sync_errors += 1
                
                # Stop if too many errors
                if self.sync_errors >= self.config.retry_limit:
                    logger.error("Too many sync errors, stopping adapter")
                    await self.stop()
                    break
                    
            # Wait for next sync
            await asyncio.sleep(self.config.sync_interval)
            
    async def _sync_states(self):
        """Synchronize agent states."""
        # Get current OpenManus state
        system_state = await self.bridge.convert_to_system_state()
        
        # Update state tracker
        for agent_id, agent_state in system_state.agents.items():
            await self.state_tracker.update_agent_state(
                agent_id,
                agent_state,
                require_consensus=True
            )
            
        self.last_sync = time.time()
        
    async def _detect_behaviors(self):
        """Detect emergent behaviors."""
        # Get current system state
        system_state = self.state_tracker.current_state
        if not system_state:
            return
            
        # Detect behaviors
        behaviors = await self.emergent_detector.analyze_state(system_state)
        
        # Process each behavior
        for behavior in behaviors:
            await self._process_behavior(behavior)
            
    async def _process_behavior(self, behavior: EmergentBehavior):
        """Process detected behavior.
        
        Args:
            behavior: Detected behavior
        """
        # Log behavior
        logger.info(
            f"Detected behavior: {behavior.type} "
            f"(confidence: {behavior.confidence:.2f})"
        )
        
        # Notify involved agents
        message = {
            'type': 'behavior_detected',
            'behavior_id': behavior.behavior_id,
            'behavior_type': behavior.type,
            'description': behavior.description,
            'confidence': behavior.confidence,
            'metrics': behavior.metrics,
            'timestamp': behavior.timestamp
        }
        
        for agent_id in behavior.agents_involved:
            await self.bridge.send_message(
                sender_id='test_adapter',
                receiver_id=agent_id,
                message_type='behavior_notification',
                content=message,
                context=behavior.context
            )
            
    async def _run_tests(self):
        """Generate and run tests."""
        # Get current system state
        system_state = self.state_tracker.current_state
        if not system_state:
            return
            
        # Generate tests for each agent
        for agent_id, agent_state in system_state.agents.items():
            # Get agent
            agent = self.bridge.agents.get(agent_id)
            if not agent:
                continue
                
            # Generate tests
            tests = await self.test_generator.generate_tests(
                target=agent,
                category='integration',
                complexity='high',
                edge_cases=True,
                max_tests=5
            )
            
            # Execute tests
            results = await self.test_executor.execute_tests(
                tests,
                agent
            )
            
            # Store results
            self.test_results.extend(results)
            
            # Notify agent of results
            await self._notify_test_results(agent_id, results)
            
    async def _notify_test_results(
        self,
        agent_id: str,
        results: List[TestResult]
    ):
        """Notify agent of test results.
        
        Args:
            agent_id: Agent identifier
            results: Test results
        """
        # Create notification
        message = {
            'type': 'test_results',
            'timestamp': time.time(),
            'results': [
                {
                    'test_id': r.test_id,
                    'success': r.success,
                    'duration': r.duration,
                    'error': r.error
                }
                for r in results
            ]
        }
        
        # Send notification
        await self.bridge.send_message(
            sender_id='test_adapter',
            receiver_id=agent_id,
            message_type='test_notification',
            content=message
        )
        
    def _update_metrics(self):
        """Update adapter metrics."""
        metrics = {
            'last_sync': self.last_sync,
            'sync_errors': self.sync_errors,
            'total_tests': len(self.test_results),
            'test_success_rate': self._calculate_success_rate()
        }
        
        # Update bridge metrics
        self.bridge.agents.get('test_adapter', {}).update({
            'metrics': metrics
        })
        
    def _calculate_success_rate(self) -> float:
        """Calculate test success rate.
        
        Returns:
            Success rate [0, 1]
        """
        if not self.test_results:
            return 1.0
            
        return sum(1 for r in self.test_results if r.success) / len(self.test_results)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get adapter status.
        
        Returns:
            Status information
        """
        return {
            'running': self.running,
            'last_sync': self.last_sync,
            'sync_errors': self.sync_errors,
            'total_tests': len(self.test_results),
            'test_success_rate': self._calculate_success_rate(),
            'bridge_agents': len(self.bridge.agents),
            'bridge_messages': len(self.bridge.message_buffer)
        } 