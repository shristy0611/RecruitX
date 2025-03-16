"""Test Generator Agent that uses Gemini to create intelligent test cases."""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import inspect

from .base_test_agent import BaseTestAgent, TestResult

logger = logging.getLogger(__name__)

class TestGeneratorAgent(BaseTestAgent):
    """Generates test cases using Gemini's intelligence."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the test generator.
        
        Args:
            db_path: Path to SQLite database for test results
        """
        super().__init__('test_generator', db_path)
        self.test_templates = {}
        self.generated_tests = set()
    
    async def _run_test(self, test_data: Dict[str, Any]) -> TestResult:
        """Generate test cases based on input parameters.
        
        Args:
            test_data: Dictionary containing generation parameters
            
        Returns:
            TestResult object containing generated test cases
        """
        start_time = datetime.now()
        
        try:
            # Generate test cases
            test_cases = await self._generate_test_cases(test_data)
            
            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_id=test_data.get('test_id', 'unknown'),
                agent_id=self.agent_id,
                status='pass',
                name=test_data.get('name', 'test_generation'),
                category=test_data.get('category', 'generation'),
                duration=duration,
                timestamp=datetime.now(),
                details={'test_cases': test_cases}
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_id=test_data.get('test_id', 'unknown'),
                agent_id=self.agent_id,
                status='error',
                name=test_data.get('name', 'test_generation'),
                category=test_data.get('category', 'generation'),
                duration=duration,
                timestamp=datetime.now(),
                details={},
                error_message=str(e)
            )
    
    async def _generate_test_cases(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate test cases using Gemini.
        
        Args:
            params: Dictionary containing:
                - target: Target to generate tests for (function, class, module)
                - category: Test category (unit, integration, system, etc.)
                - complexity: Desired test complexity
                - edge_cases: Whether to include edge cases
                - multilingual: Whether to test multilingual scenarios
                
        Returns:
            List of generated test cases
        """
        target = params.get('target')
        if not target:
            raise ValueError("Target for test generation is required")
            
        # Get target source code and docs
        if inspect.isfunction(target):
            source = inspect.getsource(target)
            signature = str(inspect.signature(target))
            docs = inspect.getdoc(target) or ""
        elif inspect.isclass(target):
            source = inspect.getsource(target)
            docs = inspect.getdoc(target) or ""
            signature = ""
        else:
            source = str(target)
            docs = ""
            signature = ""
        
        # Create prompt for Gemini
        prompt = self._create_test_generation_prompt(
            source=source,
            signature=signature,
            docs=docs,
            category=params.get('category', 'unit'),
            complexity=params.get('complexity', 'medium'),
            edge_cases=params.get('edge_cases', True),
            multilingual=params.get('multilingual', False)
        )
        
        # Get API key
        api_key = await self.gemini.get_next_key()
        if not api_key:
            raise RuntimeError("No available Gemini API key")
        
        try:
            # Generate test cases using Gemini
            response = await self._call_gemini(api_key[0], prompt)
            
            # Parse and validate test cases
            test_cases = self._parse_test_cases(response)
            
            # Log successful API call
            self.gemini.log_api_call(
                api_key=api_key[0],
                endpoint='test_generation',
                success=True
            )
            
            return test_cases
            
        except Exception as e:
            # Log failed API call
            self.gemini.log_api_call(
                api_key=api_key[0],
                endpoint='test_generation',
                success=False,
                error_message=str(e)
            )
            raise
    
    def _create_test_generation_prompt(
        self,
        source: str,
        signature: str,
        docs: str,
        category: str,
        complexity: str,
        edge_cases: bool,
        multilingual: bool
    ) -> str:
        """Create a detailed prompt for test case generation.
        
        Args:
            source: Source code to generate tests for
            signature: Function signature (if applicable)
            docs: Documentation string
            category: Test category
            complexity: Desired test complexity
            edge_cases: Whether to include edge cases
            multilingual: Whether to test multilingual scenarios
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""
        Generate comprehensive test cases for the following code:
        
        SOURCE CODE:
        {source}
        
        SIGNATURE:
        {signature}
        
        DOCUMENTATION:
        {docs}
        
        REQUIREMENTS:
        - Test Category: {category}
        - Complexity Level: {complexity}
        - Include Edge Cases: {edge_cases}
        - Multilingual Testing: {multilingual}
        
        Please generate test cases in the following JSON format:
        {{
            "test_cases": [
                {{
                    "id": "unique_test_id",
                    "name": "descriptive_test_name",
                    "category": "{category}",
                    "description": "detailed test description",
                    "inputs": {{}},
                    "expected_outputs": {{}},
                    "edge_case": boolean,
                    "multilingual": boolean,
                    "setup": "any setup code needed",
                    "cleanup": "any cleanup code needed",
                    "assertions": [
                        "list of assertions to verify"
                    ]
                }}
            ]
        }}
        
        Focus on:
        1. Comprehensive test coverage
        2. Edge cases and boundary conditions
        3. Error handling scenarios
        4. Performance considerations
        5. Security implications
        """
        
        return prompt
    
    async def _call_gemini(self, api_key: str, prompt: str) -> str:
        """Call Gemini API to generate test cases.
        
        Args:
            api_key: Gemini API key to use
            prompt: Formatted prompt string
            
        Returns:
            Generated test cases as string
        """
        # TODO: Implement actual Gemini API call
        # For now, return a mock response
        return json.dumps({
            "test_cases": [
                {
                    "id": "test_001",
                    "name": "test_basic_functionality",
                    "category": "unit",
                    "description": "Test basic functionality with valid inputs",
                    "inputs": {"x": 1, "y": 2},
                    "expected_outputs": {"result": 3},
                    "edge_case": False,
                    "multilingual": False,
                    "setup": "",
                    "cleanup": "",
                    "assertions": [
                        "assert result == expected_output"
                    ]
                }
            ]
        })
    
    def _parse_test_cases(self, response: str) -> List[Dict[str, Any]]:
        """Parse and validate test cases from Gemini response.
        
        Args:
            response: JSON string from Gemini
            
        Returns:
            List of validated test case dictionaries
        """
        try:
            data = json.loads(response)
            test_cases = data.get('test_cases', [])
            
            # Validate each test case
            required_fields = {
                'id', 'name', 'category', 'description',
                'inputs', 'expected_outputs', 'assertions'
            }
            
            for test_case in test_cases:
                missing_fields = required_fields - set(test_case.keys())
                if missing_fields:
                    raise ValueError(
                        f"Test case missing required fields: {missing_fields}"
                    )
                
                # Ensure unique test IDs
                if test_case['id'] in self.generated_tests:
                    test_case['id'] = f"{test_case['id']}_{len(self.generated_tests)}"
                self.generated_tests.add(test_case['id'])
            
            return test_cases
            
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON response from Gemini")
        except Exception as e:
            raise ValueError(f"Error parsing test cases: {str(e)}")
    
    async def generate_edge_cases(
        self,
        target: Any,
        category: str = 'edge'
    ) -> List[Dict[str, Any]]:
        """Generate specific edge case tests.
        
        Args:
            target: Target to generate edge cases for
            category: Test category
            
        Returns:
            List of edge case test dictionaries
        """
        params = {
            'target': target,
            'category': category,
            'complexity': 'high',
            'edge_cases': True,
            'multilingual': False
        }
        
        result = await self._run_test(params)
        if result.status == 'pass':
            return result.details.get('test_cases', [])
        else:
            raise RuntimeError(
                f"Edge case generation failed: {result.error_message}"
            )
    
    async def generate_multilingual_tests(
        self,
        target: Any,
        languages: List[str] = ['en', 'ja']
    ) -> List[Dict[str, Any]]:
        """Generate multilingual test cases.
        
        Args:
            target: Target to generate tests for
            languages: List of language codes to test
            
        Returns:
            List of multilingual test dictionaries
        """
        params = {
            'target': target,
            'category': 'multilingual',
            'complexity': 'medium',
            'edge_cases': False,
            'multilingual': True,
            'languages': languages
        }
        
        result = await self._run_test(params)
        if result.status == 'pass':
            return result.details.get('test_cases', [])
        else:
            raise RuntimeError(
                f"Multilingual test generation failed: {result.error_message}"
            ) 