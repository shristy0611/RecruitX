"""Test Coordinator Agent that orchestrates the testing process."""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import yaml

from .base_test_agent import BaseTestAgent, TestResult
from .test_generator import TestGeneratorAgent
from .test_executor import TestExecutorAgent
from .test_analyzer import TestAnalyzerAgent

logger = logging.getLogger(__name__)

class TestCoordinatorAgent(BaseTestAgent):
    """Coordinates the testing process across multiple agents."""
    
    def __init__(
        self,
        db_path: Optional[Path] = None,
        config_path: Optional[Path] = None
    ):
        """Initialize the test coordinator.
        
        Args:
            db_path: Path to SQLite database for test results
            config_path: Path to YAML config file
        """
        super().__init__('test_coordinator', db_path)
        self.config = self._load_config(config_path)
        
        # Initialize agents
        self.generator = TestGeneratorAgent(db_path)
        self.executor = TestExecutorAgent(db_path)
        self.analyzer = TestAnalyzerAgent(db_path)
        
        # Track test suites
        self.active_suites: Dict[str, Dict[str, Any]] = {}
        self.completed_suites: Set[str] = set()
    
    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to YAML config file
            
        Returns:
            Dictionary containing configuration
        """
        default_config = {
            'max_parallel_tests': 5,
            'test_timeout': 300,  # 5 minutes
            'retry_count': 3,
            'retry_delay': 5,
            'coverage_threshold': 80,
            'performance_threshold': 5.0,  # seconds
            'memory_threshold': 500,  # MB
            'cpu_threshold': 80,  # percent
            'categories': ['unit', 'integration', 'e2e'],
            'report_format': 'markdown',
            'notification_webhook': None
        }
        
        if not config_path or not config_path.exists():
            return default_config
            
        with open(config_path) as f:
            config = yaml.safe_load(f)
            
        # Merge with defaults
        return {**default_config, **config}
    
    async def _run_test(self, test_data: Dict[str, Any]) -> TestResult:
        """Not implemented for coordinator agent."""
        raise NotImplementedError("Coordinator agent does not run tests directly")
    
    async def create_test_suite(
        self,
        suite_id: str,
        targets: List[str],
        categories: Optional[List[str]] = None,
        complexity: str = 'medium',
        edge_cases: bool = True,
        multilingual: bool = False
    ) -> Dict[str, Any]:
        """Create a new test suite.
        
        Args:
            suite_id: Unique identifier for the suite
            targets: List of targets to test
            categories: Optional list of test categories
            complexity: Test complexity level
            edge_cases: Whether to generate edge cases
            multilingual: Whether to generate multilingual tests
            
        Returns:
            Dictionary containing suite information
        """
        if suite_id in self.active_suites:
            raise ValueError(f"Test suite {suite_id} already exists")
            
        # Create suite configuration
        suite = {
            'id': suite_id,
            'targets': targets,
            'categories': categories or self.config['categories'],
            'complexity': complexity,
            'edge_cases': edge_cases,
            'multilingual': multilingual,
            'status': 'created',
            'created_at': datetime.now(),
            'tests': [],
            'results': None
        }
        
        self.active_suites[suite_id] = suite
        return suite
    
    async def run_test_suite(
        self,
        suite_id: str,
        parallel: bool = True
    ) -> Dict[str, Any]:
        """Run a test suite.
        
        Args:
            suite_id: Suite identifier
            parallel: Whether to run tests in parallel
            
        Returns:
            Dictionary containing suite results
        """
        if suite_id not in self.active_suites:
            raise ValueError(f"Test suite {suite_id} not found")
            
        suite = self.active_suites[suite_id]
        suite['status'] = 'running'
        suite['started_at'] = datetime.now()
        
        try:
            # Generate tests
            logger.info(f"Generating tests for suite {suite_id}")
            test_cases = []
            for target in suite['targets']:
                cases = await self._generate_tests(
                    target,
                    suite['categories'],
                    suite['complexity'],
                    suite['edge_cases'],
                    suite['multilingual']
                )
                test_cases.extend(cases)
            
            suite['tests'] = test_cases
            
            # Execute tests
            logger.info(f"Executing {len(test_cases)} tests for suite {suite_id}")
            results = await self.executor.run_test_suite(
                test_cases,
                parallel=parallel,
                max_workers=self.config['max_parallel_tests']
            )
            
            # Analyze results
            logger.info(f"Analyzing results for suite {suite_id}")
            analysis = await self.analyzer.analyze_results(
                categories=suite['categories']
            )
            
            # Generate report
            report = await self.analyzer.generate_report(
                analysis,
                format=self.config['report_format']
            )
            
            # Update suite status
            suite['status'] = 'completed'
            suite['completed_at'] = datetime.now()
            suite['results'] = {
                'test_results': results,
                'analysis': analysis,
                'report': report
            }
            
            self.completed_suites.add(suite_id)
            
            # Send notifications if configured
            if self.config['notification_webhook']:
                await self._send_notification(suite)
            
            return suite
            
        except Exception as e:
            suite['status'] = 'failed'
            suite['error'] = str(e)
            logger.error(f"Suite {suite_id} failed: {e}")
            raise
    
    async def _generate_tests(
        self,
        target: str,
        categories: List[str],
        complexity: str,
        edge_cases: bool,
        multilingual: bool
    ) -> List[Dict[str, Any]]:
        """Generate tests for a target.
        
        Args:
            target: Target to test
            categories: Test categories
            complexity: Test complexity level
            edge_cases: Whether to generate edge cases
            multilingual: Whether to generate multilingual tests
            
        Returns:
            List of test case dictionaries
        """
        test_cases = []
        
        # Generate standard tests
        for category in categories:
            result = await self.generator._run_test({
                'target': target,
                'category': category,
                'complexity': complexity
            })
            if result.status == 'pass':
                test_cases.extend(result.details.get('test_cases', []))
        
        # Generate edge cases if requested
        if edge_cases:
            result = await self.generator.generate_edge_cases(target)
            if result.status == 'pass':
                test_cases.extend(result.details.get('test_cases', []))
        
        # Generate multilingual tests if requested
        if multilingual:
            result = await self.generator.generate_multilingual_tests(target)
            if result.status == 'pass':
                test_cases.extend(result.details.get('test_cases', []))
        
        return test_cases
    
    async def get_suite_status(self, suite_id: str) -> Dict[str, Any]:
        """Get status of a test suite.
        
        Args:
            suite_id: Suite identifier
            
        Returns:
            Dictionary containing suite status
        """
        if suite_id not in self.active_suites:
            raise ValueError(f"Test suite {suite_id} not found")
            
        return self.active_suites[suite_id]
    
    async def list_suites(
        self,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all test suites.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of suite dictionaries
        """
        suites = list(self.active_suites.values())
        
        if status:
            suites = [s for s in suites if s['status'] == status]
            
        return suites
    
    async def retry_failed_tests(
        self,
        suite_id: str,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """Retry failed tests in a suite.
        
        Args:
            suite_id: Suite identifier
            max_retries: Maximum number of retries
            
        Returns:
            Dictionary containing retry results
        """
        if suite_id not in self.active_suites:
            raise ValueError(f"Test suite {suite_id} not found")
            
        suite = self.active_suites[suite_id]
        if not suite['results']:
            raise ValueError(f"Suite {suite_id} has not been run")
            
        # Get failed tests
        failed_tests = [
            r for r in suite['results']['test_results']
            if r.status in ['fail', 'error']
        ]
        
        if not failed_tests:
            return {'message': 'No failed tests to retry'}
            
        # Retry tests
        max_retries = max_retries or self.config['retry_count']
        retry_results = []
        
        for test in failed_tests:
            for i in range(max_retries):
                await asyncio.sleep(self.config['retry_delay'])
                result = await self.executor._run_test(test.details['test_case'])
                if result.status == 'pass':
                    retry_results.append(result)
                    break
                retry_results.append(result)
        
        return {
            'original_failures': len(failed_tests),
            'retried': len(retry_results),
            'results': retry_results
        }
    
    async def _send_notification(self, suite: Dict[str, Any]):
        """Send notification about suite completion.
        
        Args:
            suite: Suite dictionary
        """
        if not self.config['notification_webhook']:
            return
            
        # Implement notification logic here
        # This could use various notification services
        pass
    
    async def cleanup(self):
        """Cleanup resources for all agents."""
        await self.generator.cleanup()
        await self.executor.cleanup()
        await self.analyzer.cleanup() 