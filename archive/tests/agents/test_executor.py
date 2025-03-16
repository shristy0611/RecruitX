"""Test Executor Agent that runs generated test cases."""

import asyncio
import importlib
import inspect
import logging
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pytest
import coverage

from .base_test_agent import BaseTestAgent, TestResult

logger = logging.getLogger(__name__)

class TestExecutorAgent(BaseTestAgent):
    """Executes test cases with comprehensive monitoring."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the test executor.
        
        Args:
            db_path: Path to SQLite database for test results
        """
        super().__init__('test_executor', db_path)
        self.coverage = coverage.Coverage()
        self.current_tests = {}
        
    async def _run_test(self, test_data: Dict[str, Any]) -> TestResult:
        """Execute a test case with monitoring.
        
        Args:
            test_data: Dictionary containing test case data
            
        Returns:
            TestResult object containing test execution results
        """
        start_time = datetime.now()
        test_id = test_data.get('id', 'unknown')
        
        try:
            # Start coverage
            self.coverage.start()
            
            # Execute test
            result = await self._execute_test_case(test_data)
            
            # Stop coverage
            self.coverage.stop()
            
            # Get coverage data
            coverage_data = self.coverage.get_data()
            coverage_percent = self.coverage.report()
            
            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_id=test_id,
                agent_id=self.agent_id,
                status='pass' if result[0] else 'fail',
                name=test_data.get('name', 'unknown'),
                category=test_data.get('category', 'unknown'),
                duration=duration,
                timestamp=datetime.now(),
                details={
                    'coverage': coverage_percent,
                    'output': result[1],
                    'memory_usage': result[2],
                    'cpu_usage': result[3]
                },
                error_message=result[4] if not result[0] else None,
                memory_usage=result[2],
                cpu_usage=result[3]
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_id=test_id,
                agent_id=self.agent_id,
                status='error',
                name=test_data.get('name', 'unknown'),
                category=test_data.get('category', 'unknown'),
                duration=duration,
                timestamp=datetime.now(),
                details={},
                error_message=str(e),
                stacktrace=traceback.format_exc()
            )
            
        finally:
            self.coverage.erase()
    
    async def _execute_test_case(
        self,
        test_case: Dict[str, Any]
    ) -> Tuple[bool, str, float, float, Optional[str]]:
        """Execute a single test case.
        
        Args:
            test_case: Dictionary containing test case data
            
        Returns:
            Tuple containing:
            - Success flag
            - Test output
            - Memory usage
            - CPU usage
            - Error message (if any)
        """
        # Import target module/function
        target = self._import_target(test_case.get('target'))
        if not target:
            return False, "", 0.0, 0.0, "Failed to import target"
        
        # Create test environment
        test_env = {}
        
        try:
            # Execute setup code
            if setup_code := test_case.get('setup'):
                exec(setup_code, test_env)
            
            # Start monitoring
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            # Execute test
            test_code = self._generate_test_code(test_case, target)
            exec(test_code, test_env)
            
            # Calculate resource usage
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            memory_usage = end_memory - start_memory
            cpu_usage = (end_time - start_time) * 100  # Rough estimate
            
            # Execute cleanup code
            if cleanup_code := test_case.get('cleanup'):
                exec(cleanup_code, test_env)
            
            return True, str(test_env.get('output', '')), memory_usage, cpu_usage, None
            
        except AssertionError as e:
            return False, "", 0.0, 0.0, f"Assertion failed: {str(e)}"
            
        except Exception as e:
            return False, "", 0.0, 0.0, str(e)
    
    def _import_target(self, target_path: str) -> Optional[Any]:
        """Import target module, class, or function.
        
        Args:
            target_path: Dot-separated path to target
            
        Returns:
            Imported target or None if import fails
        """
        try:
            if '.' in target_path:
                module_path, target_name = target_path.rsplit('.', 1)
                module = importlib.import_module(module_path)
                return getattr(module, target_name)
            else:
                return importlib.import_module(target_path)
                
        except Exception as e:
            logger.error(f"Failed to import {target_path}: {str(e)}")
            return None
    
    def _generate_test_code(self, test_case: Dict[str, Any], target: Any) -> str:
        """Generate executable test code.
        
        Args:
            test_case: Dictionary containing test case data
            target: Target object to test
            
        Returns:
            String containing executable test code
        """
        code = []
        
        # Import statements
        code.append("import pytest")
        code.append("import asyncio")
        
        # Test function definition
        code.append(f"async def test_{test_case['id']}():")
        
        # Setup inputs
        for name, value in test_case.get('inputs', {}).items():
            code.append(f"    {name} = {repr(value)}")
        
        # Call target
        if inspect.iscoroutinefunction(target):
            code.append("    result = await target(**inputs)")
        else:
            code.append("    result = target(**inputs)")
        
        # Add assertions
        for assertion in test_case.get('assertions', []):
            code.append(f"    {assertion}")
        
        return "\n".join(code)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    async def run_pytest(self, test_file: str) -> TestResult:
        """Run tests using pytest.
        
        Args:
            test_file: Path to test file
            
        Returns:
            TestResult object containing pytest results
        """
        start_time = datetime.now()
        
        try:
            # Run pytest
            result = pytest.main([
                test_file,
                '-v',
                '--tb=short',
                '--cov',
                '--cov-report=term-missing'
            ])
            
            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_id=f"pytest_{test_file}",
                agent_id=self.agent_id,
                status='pass' if result == 0 else 'fail',
                name=f"pytest_{test_file}",
                category='pytest',
                duration=duration,
                timestamp=datetime.now(),
                details={
                    'pytest_exit_code': result,
                    'coverage': self.coverage.report()
                }
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_id=f"pytest_{test_file}",
                agent_id=self.agent_id,
                status='error',
                name=f"pytest_{test_file}",
                category='pytest',
                duration=duration,
                timestamp=datetime.now(),
                details={},
                error_message=str(e),
                stacktrace=traceback.format_exc()
            )
    
    async def run_test_suite(
        self,
        test_cases: List[Dict[str, Any]],
        parallel: bool = True,
        max_workers: int = 5
    ) -> List[TestResult]:
        """Run a suite of tests, optionally in parallel.
        
        Args:
            test_cases: List of test case dictionaries
            parallel: Whether to run tests in parallel
            max_workers: Maximum number of parallel workers
            
        Returns:
            List of TestResult objects
        """
        if parallel:
            # Create task pool
            tasks = []
            semaphore = asyncio.Semaphore(max_workers)
            
            async def run_with_semaphore(test_case):
                async with semaphore:
                    return await self._run_test(test_case)
            
            for test_case in test_cases:
                task = asyncio.create_task(run_with_semaphore(test_case))
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        else:
            # Run tests sequentially
            results = []
            for test_case in test_cases:
                result = await self._run_test(test_case)
                results.append(result)
        
        return results
    
    async def cleanup(self):
        """Cleanup coverage and other resources."""
        self.coverage.stop()
        self.coverage.erase() 