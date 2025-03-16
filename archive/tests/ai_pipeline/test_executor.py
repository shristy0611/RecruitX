"""AI-first test executor for running generated tests."""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import traceback
import pytest
import json

from tests.ai_pipeline.test_generator import GeneratedTest

logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Result of a test execution."""
    test_id: str
    success: bool
    duration: float
    error: Optional[str] = None
    traceback: Optional[str] = None
    metadata: Dict[str, Any] = None

class AITestExecutor:
    """Executes generated test cases in parallel."""
    
    def __init__(self, max_workers: int = 4):
        """Initialize the test executor.
        
        Args:
            max_workers: Maximum number of parallel test workers
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.results_cache: Dict[str, List[TestResult]] = {}
        
    async def execute_tests(
        self,
        tests: List[GeneratedTest],
        target: Any,
        timeout: float = 30.0,
        retry_count: int = 2
    ) -> List[TestResult]:
        """Execute a batch of test cases.
        
        Args:
            tests: List of test cases to execute
            target: Target being tested
            timeout: Timeout per test in seconds
            retry_count: Number of retries for failed tests
            
        Returns:
            List of test results
        """
        # Check cache
        cache_key = self._get_cache_key(tests, target)
        if cache_key in self.results_cache:
            return self.results_cache[cache_key]
        
        # Group tests by category for optimal execution
        test_groups = self._group_tests(tests)
        
        # Execute test groups in parallel
        results = []
        tasks = []
        
        for category, group_tests in test_groups.items():
            task = asyncio.create_task(
                self._execute_test_group(
                    group_tests,
                    target,
                    timeout,
                    retry_count
                )
            )
            tasks.append(task)
        
        # Wait for all test groups to complete
        group_results = await asyncio.gather(*tasks)
        for group_result in group_results:
            results.extend(group_result)
            
        # Cache results
        self.results_cache[cache_key] = results
        
        return results
    
    def _get_cache_key(
        self,
        tests: List[GeneratedTest],
        target: Any
    ) -> str:
        """Generate cache key for test execution.
        
        Args:
            tests: List of test cases
            target: Target being tested
            
        Returns:
            Cache key string
        """
        test_ids = sorted([test.test_id for test in tests])
        target_hash = hash(str(target))
        return f"{target_hash}-{'-'.join(test_ids)}"
    
    def _group_tests(
        self,
        tests: List[GeneratedTest]
    ) -> Dict[str, List[GeneratedTest]]:
        """Group tests by category for optimal execution.
        
        Args:
            tests: List of test cases
            
        Returns:
            Dictionary mapping categories to test lists
        """
        groups: Dict[str, List[GeneratedTest]] = {}
        for test in tests:
            if test.category not in groups:
                groups[test.category] = []
            groups[test.category].append(test)
        return groups
    
    async def _execute_test_group(
        self,
        tests: List[GeneratedTest],
        target: Any,
        timeout: float,
        retry_count: int
    ) -> List[TestResult]:
        """Execute a group of tests in parallel.
        
        Args:
            tests: List of test cases in the group
            target: Target being tested
            timeout: Timeout per test
            retry_count: Number of retries for failed tests
            
        Returns:
            List of test results
        """
        results = []
        loop = asyncio.get_event_loop()
        
        # Submit tests to thread pool
        futures = []
        for test in tests:
            future = loop.run_in_executor(
                self.executor,
                self._execute_single_test,
                test,
                target,
                timeout,
                retry_count
            )
            futures.append(future)
            
        # Wait for all tests to complete
        for future in asyncio.as_completed(futures):
            result = await future
            results.append(result)
            
        return results
    
    def _execute_single_test(
        self,
        test: GeneratedTest,
        target: Any,
        timeout: float,
        retry_count: int
    ) -> TestResult:
        """Execute a single test case with retries.
        
        Args:
            test: Test case to execute
            target: Target being tested
            timeout: Test timeout in seconds
            retry_count: Number of retries
            
        Returns:
            Test execution result
        """
        start_time = time.time()
        error = None
        tb = None
        
        for attempt in range(retry_count + 1):
            try:
                # Set up test environment
                if test.setup_code:
                    exec(test.setup_code)
                
                # Create test function
                test_code = self._create_test_code(test, target)
                test_globals = {'target': target, **test.inputs}
                
                # Execute test with timeout
                with pytest.raises(Exception) as exc_info:
                    pytest.main(['-v', '--timeout', str(timeout)], test_code)
                    
                # Test passed if no exception
                if exc_info is None:
                    duration = time.time() - start_time
                    return TestResult(
                        test_id=test.test_id,
                        success=True,
                        duration=duration,
                        metadata={'attempt': attempt + 1}
                    )
                    
            except Exception as e:
                error = str(e)
                tb = traceback.format_exc()
                
                # Don't retry if it's a syntax error
                if isinstance(e, SyntaxError):
                    break
                    
                # Wait before retry
                if attempt < retry_count:
                    time.sleep(1)
                    
            finally:
                # Clean up test environment
                if test.cleanup_code:
                    try:
                        exec(test.cleanup_code)
                    except Exception as e:
                        logger.warning(
                            f"Error in cleanup code for {test.test_id}: {str(e)}"
                        )
                        
        # Test failed after all retries
        duration = time.time() - start_time
        return TestResult(
            test_id=test.test_id,
            success=False,
            duration=duration,
            error=error,
            traceback=tb,
            metadata={'attempt': attempt + 1}
        )
    
    def _create_test_code(self, test: GeneratedTest, target: Any) -> str:
        """Create executable test code from test case.
        
        Args:
            test: Test case to convert
            target: Target being tested
            
        Returns:
            String containing test code
        """
        # Create test function
        code = f"""
def {test.name}():
    \"\"\"
    {test.description}
    \"\"\"
    # Set up test inputs
    inputs = {json.dumps(test.inputs)}
    expected = {json.dumps(test.expected_outputs)}
    
    # Execute test
    result = target(**inputs)
    
    # Run assertions
    {chr(10).join(test.assertions)}
"""
        return code 