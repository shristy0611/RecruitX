"""Test Manager Agent that orchestrates the testing workflow."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type

from .base_test_agent import BaseTestAgent, TestResult

logger = logging.getLogger(__name__)

class TestManagerAgent(BaseTestAgent):
    """Orchestrates the testing workflow across all test agents."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the test manager.
        
        Args:
            db_path: Path to SQLite database for test results
        """
        super().__init__('test_manager', db_path)
        self.test_agents: Dict[str, BaseTestAgent] = {}
        self.test_queue: asyncio.Queue = asyncio.Queue()
        self.running_tests: Set[str] = set()
        self.max_concurrent_tests = 5
        
    def register_agent(self, agent: BaseTestAgent):
        """Register a test agent with the manager.
        
        Args:
            agent: Test agent instance to register
        """
        self.test_agents[agent.agent_id] = agent
        logger.info(f"Registered test agent: {agent.agent_id}")
    
    async def schedule_test(self, test_data: Dict[str, Any]):
        """Schedule a test for execution.
        
        Args:
            test_data: Dictionary containing test parameters
        """
        await self.test_queue.put(test_data)
        logger.info(f"Scheduled test: {test_data.get('test_id', 'unknown')}")
    
    async def _run_test(self, test_data: Dict[str, Any]) -> TestResult:
        """Execute a test using the appropriate agent.
        
        Args:
            test_data: Dictionary containing test parameters
            
        Returns:
            TestResult object containing the test outcome
        """
        agent_id = test_data.get('agent_id')
        if not agent_id or agent_id not in self.test_agents:
            raise ValueError(f"Invalid agent ID: {agent_id}")
        
        agent = self.test_agents[agent_id]
        return await agent.execute_test(test_data)
    
    async def run_test_suite(self, test_suite: List[Dict[str, Any]]) -> List[TestResult]:
        """Run a suite of tests with parallel execution.
        
        Args:
            test_suite: List of test data dictionaries
            
        Returns:
            List of TestResult objects
        """
        # Schedule all tests
        for test_data in test_suite:
            await self.schedule_test(test_data)
        
        # Create worker tasks
        workers = [
            asyncio.create_task(self._test_worker())
            for _ in range(self.max_concurrent_tests)
        ]
        
        # Wait for all tests to complete
        await self.test_queue.join()
        
        # Cancel workers
        for worker in workers:
            worker.cancel()
        
        # Get results
        results = []
        for test_data in test_suite:
            test_id = test_data.get('test_id')
            if test_id:
                history = await self.get_test_history(test_id=test_id, limit=1)
                if history:
                    results.append(history[0])
        
        return results
    
    async def _test_worker(self):
        """Worker coroutine for executing tests from the queue."""
        while True:
            try:
                # Get test from queue
                test_data = await self.test_queue.get()
                test_id = test_data.get('test_id', 'unknown')
                
                if test_id in self.running_tests:
                    logger.warning(f"Test {test_id} is already running")
                    self.test_queue.task_done()
                    continue
                
                self.running_tests.add(test_id)
                
                try:
                    # Execute test
                    await self._run_test(test_data)
                    
                except Exception as e:
                    logger.error(f"Error executing test {test_id}: {str(e)}")
                    
                finally:
                    self.running_tests.remove(test_id)
                    self.test_queue.task_done()
                    
            except asyncio.CancelledError:
                break
            
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
    
    async def generate_test_report(self) -> Dict[str, Any]:
        """Generate a comprehensive test report.
        
        Returns:
            Dictionary containing test report data:
            - overall_stats: Overall test statistics
            - agent_stats: Per-agent statistics
            - failure_analysis: Analysis of test failures
            - performance_metrics: Performance metrics
        """
        # Get overall test patterns
        overall_stats = await self.analyze_test_patterns()
        
        # Get per-agent statistics
        agent_stats = {}
        for agent_id, agent in self.test_agents.items():
            agent_stats[agent_id] = await agent.analyze_test_patterns()
        
        # Additional analysis
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get test duration distribution
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN duration < 1 THEN '<1s'
                    WHEN duration < 5 THEN '1-5s'
                    WHEN duration < 10 THEN '5-10s'
                    ELSE '>10s'
                END as duration_range,
                COUNT(*) as count
            FROM test_results
            GROUP BY duration_range
        ''')
        
        duration_dist = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get category-wise success rates
        cursor.execute('''
            SELECT 
                category,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) as passed
            FROM test_results
            GROUP BY category
        ''')
        
        category_stats = {}
        for row in cursor.fetchall():
            category, total, passed = row
            category_stats[category] = {
                'total': total,
                'passed': passed,
                'success_rate': (passed / total * 100) if total > 0 else 0
            }
        
        conn.close()
        
        return {
            'overall_stats': overall_stats,
            'agent_stats': agent_stats,
            'performance_metrics': {
                'duration_distribution': duration_dist,
                'category_stats': category_stats
            }
        }
    
    async def cleanup(self):
        """Cleanup resources used by all agents."""
        for agent in self.test_agents.values():
            await agent.cleanup() 