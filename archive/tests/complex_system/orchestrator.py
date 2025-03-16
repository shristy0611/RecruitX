"""Complex system test orchestrator."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import json

from tests.complex_system.state_tracker import ComplexStateTracker, SystemState, AgentState
from tests.complex_system.emergent_detector import EmergentDetector, EmergentBehavior
from tests.ai_pipeline.test_generator import AITestGenerator, GeneratedTest
from tests.ai_pipeline.test_executor import AITestExecutor, TestResult

logger = logging.getLogger(__name__)

@dataclass
class TestSession:
    """Complex system test session."""
    session_id: str
    start_time: float
    config: Dict[str, Any]
    agents: Dict[str, Any]
    state_tracker: ComplexStateTracker
    emergent_detector: EmergentDetector
    test_generator: AITestGenerator
    test_executor: AITestExecutor
    behaviors: List[EmergentBehavior] = field(default_factory=list)
    test_results: List[TestResult] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

class ComplexTestOrchestrator:
    """Orchestrates complex system testing."""
    
    def __init__(
        self,
        state_tracker: Optional[ComplexStateTracker] = None,
        emergent_detector: Optional[EmergentDetector] = None,
        test_generator: Optional[AITestGenerator] = None,
        test_executor: Optional[AITestExecutor] = None
    ):
        """Initialize the orchestrator.
        
        Args:
            state_tracker: State tracker instance
            emergent_detector: Emergent detector instance
            test_generator: Test generator instance
            test_executor: Test executor instance
        """
        self.state_tracker = state_tracker or ComplexStateTracker()
        self.emergent_detector = emergent_detector or EmergentDetector()
        self.test_generator = test_generator or AITestGenerator()
        self.test_executor = test_executor or AITestExecutor()
        
        self.sessions: Dict[str, TestSession] = {}
        self.session_counter = 0
        
    async def create_session(
        self,
        agents: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new test session.
        
        Args:
            agents: Dictionary of agents to test
            config: Session configuration
            
        Returns:
            Session ID
        """
        session_id = f"session_{self.session_counter}"
        self.session_counter += 1
        
        session = TestSession(
            session_id=session_id,
            start_time=time.time(),
            config=config or {},
            agents=agents,
            state_tracker=self.state_tracker,
            emergent_detector=self.emergent_detector,
            test_generator=self.test_generator,
            test_executor=self.test_executor
        )
        
        self.sessions[session_id] = session
        return session_id
        
    async def run_session(
        self,
        session_id: str,
        duration: float = 3600.0,  # 1 hour default
        update_interval: float = 1.0  # 1 second updates
    ) -> Dict[str, Any]:
        """Run a test session.
        
        Args:
            session_id: Session ID
            duration: Session duration in seconds
            update_interval: State update interval
            
        Returns:
            Session results
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        try:
            # Initialize agents
            await self._initialize_agents(session)
            
            # Main test loop
            end_time = time.time() + duration
            while time.time() < end_time:
                # Update agent states
                state = await self._update_agent_states(session)
                
                # Detect emergent behaviors
                behaviors = await self._detect_behaviors(session, state)
                
                # Generate and execute tests
                if behaviors:
                    await self._run_behavior_tests(session, behaviors)
                    
                # Update metrics
                self._update_session_metrics(session)
                
                # Wait for next update
                await asyncio.sleep(update_interval)
                
            return self._get_session_results(session)
            
        except Exception as e:
            logger.error(f"Error in session {session_id}: {str(e)}")
            raise
            
    async def _initialize_agents(self, session: TestSession):
        """Initialize agents for testing.
        
        Args:
            session: Test session
        """
        for agent_id, agent in session.agents.items():
            # Create initial state
            state = AgentState(
                agent_id=agent_id,
                timestamp=time.time(),
                status="active",
                metrics=self._get_agent_metrics(agent)
            )
            
            # Update state tracker
            await session.state_tracker.update_agent_state(
                agent_id,
                state,
                require_consensus=False
            )
            
    def _get_agent_metrics(self, agent: Any) -> Dict[str, Any]:
        """Get metrics from an agent.
        
        Args:
            agent: Agent instance
            
        Returns:
            Dictionary of metrics
        """
        metrics = {}
        
        # Get any available metrics
        if hasattr(agent, 'get_metrics'):
            try:
                metrics.update(agent.get_metrics())
            except Exception as e:
                logger.warning(f"Error getting metrics: {str(e)}")
                
        return metrics
        
    async def _update_agent_states(
        self,
        session: TestSession
    ) -> SystemState:
        """Update agent states.
        
        Args:
            session: Test session
            
        Returns:
            Current system state
        """
        for agent_id, agent in session.agents.items():
            # Get current state
            state = AgentState(
                agent_id=agent_id,
                timestamp=time.time(),
                status=self._get_agent_status(agent),
                metrics=self._get_agent_metrics(agent)
            )
            
            # Update position if available
            if hasattr(agent, 'get_position'):
                try:
                    state.position = agent.get_position()
                except Exception as e:
                    logger.warning(f"Error getting position: {str(e)}")
                    
            # Update state tracker
            await session.state_tracker.update_agent_state(
                agent_id,
                state
            )
            
        return session.state_tracker.current_state
        
    def _get_agent_status(self, agent: Any) -> str:
        """Get agent status.
        
        Args:
            agent: Agent instance
            
        Returns:
            Status string
        """
        if hasattr(agent, 'get_status'):
            try:
                return agent.get_status()
            except Exception:
                pass
                
        return "active"
        
    async def _detect_behaviors(
        self,
        session: TestSession,
        state: SystemState
    ) -> List[EmergentBehavior]:
        """Detect emergent behaviors.
        
        Args:
            session: Test session
            state: Current system state
            
        Returns:
            List of detected behaviors
        """
        behaviors = await session.emergent_detector.analyze_state(state)
        
        # Store new behaviors
        session.behaviors.extend(behaviors)
        
        return behaviors
        
    async def _run_behavior_tests(
        self,
        session: TestSession,
        behaviors: List[EmergentBehavior]
    ):
        """Run tests for detected behaviors.
        
        Args:
            session: Test session
            behaviors: Detected behaviors
        """
        for behavior in behaviors:
            # Generate tests
            tests = await self._generate_behavior_tests(session, behavior)
            
            # Execute tests
            for agent_id in behavior.agents_involved:
                agent = session.agents[agent_id]
                results = await session.test_executor.execute_tests(
                    tests,
                    agent
                )
                session.test_results.extend(results)
                
    async def _generate_behavior_tests(
        self,
        session: TestSession,
        behavior: EmergentBehavior
    ) -> List[GeneratedTest]:
        """Generate tests for behavior.
        
        Args:
            session: Test session
            behavior: Emergent behavior
            
        Returns:
            List of generated tests
        """
        # Get test categories based on behavior type
        categories = self._get_behavior_test_categories(behavior)
        
        tests = []
        for category in categories:
            # Generate tests for each involved agent
            for agent_id in behavior.agents_involved:
                agent = session.agents[agent_id]
                
                category_tests = await session.test_generator.generate_tests(
                    target=agent,
                    category=category,
                    complexity="high",
                    edge_cases=True,
                    max_tests=5
                )
                tests.extend(category_tests)
                
        return tests
        
    def _get_behavior_test_categories(
        self,
        behavior: EmergentBehavior
    ) -> List[str]:
        """Get test categories for behavior.
        
        Args:
            behavior: Emergent behavior
            
        Returns:
            List of test categories
        """
        if behavior.type == "spatial_clustering":
            return ["position", "movement", "coordination"]
        elif behavior.type == "periodic_updates":
            return ["timing", "synchronization"]
        elif behavior.type == "strong_interaction_group":
            return ["interaction", "communication"]
        elif behavior.type == "metric_clustering":
            return ["performance", "stability"]
        else:
            return ["functional"]
            
    def _update_session_metrics(self, session: TestSession):
        """Update session metrics.
        
        Args:
            session: Test session
        """
        metrics = {
            'duration': time.time() - session.start_time,
            'num_agents': len(session.agents),
            'num_behaviors': len(session.behaviors),
            'num_tests': len(session.test_results),
            'test_success_rate': self._calculate_success_rate(session.test_results)
        }
        
        # Behavior metrics
        behavior_types = {}
        for behavior in session.behaviors:
            behavior_types[behavior.type] = behavior_types.get(behavior.type, 0) + 1
            
        metrics['behavior_types'] = behavior_types
        
        # Test metrics
        test_categories = {}
        for result in session.test_results:
            category = result.test_id.split('_')[0]
            test_categories[category] = test_categories.get(category, 0) + 1
            
        metrics['test_categories'] = test_categories
        
        session.metrics = metrics
        
    def _calculate_success_rate(
        self,
        results: List[TestResult]
    ) -> float:
        """Calculate test success rate.
        
        Args:
            results: List of test results
            
        Returns:
            Success rate [0, 1]
        """
        if not results:
            return 1.0
            
        return sum(1 for r in results if r.success) / len(results)
        
    def _get_session_results(
        self,
        session: TestSession
    ) -> Dict[str, Any]:
        """Get session results.
        
        Args:
            session: Test session
            
        Returns:
            Dictionary of results
        """
        return {
            'session_id': session.session_id,
            'duration': time.time() - session.start_time,
            'config': session.config,
            'metrics': session.metrics,
            'behaviors': [
                {
                    'id': b.behavior_id,
                    'type': b.type,
                    'description': b.description,
                    'confidence': b.confidence,
                    'agents': b.agents_involved,
                    'metrics': b.metrics
                }
                for b in session.behaviors
            ],
            'test_results': [
                {
                    'id': r.test_id,
                    'success': r.success,
                    'duration': r.duration,
                    'error': r.error
                }
                for r in session.test_results
            ]
        } 