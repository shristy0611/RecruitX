"""AI-first test generator using Gemini Pro."""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import inspect
import ast
import json

from src.utils.gemini_manager import GeminiKeyManager

logger = logging.getLogger(__name__)

@dataclass
class GeneratedTest:
    """Generated test case data."""
    test_id: str
    name: str
    category: str
    description: str
    inputs: Dict[str, Any]
    expected_outputs: Dict[str, Any]
    assertions: List[str]
    setup_code: Optional[str] = None
    cleanup_code: Optional[str] = None
    edge_case: bool = False
    multilingual: bool = False
    metadata: Dict[str, Any] = None

class AITestGenerator:
    """Generates test cases using Gemini Pro."""
    
    def __init__(self):
        """Initialize the test generator."""
        self.gemini = GeminiKeyManager()
        self.test_counter = 0
        self.generation_cache: Dict[str, List[GeneratedTest]] = {}
        
    async def generate_tests(
        self,
        target: Any,
        category: str = 'unit',
        complexity: str = 'medium',
        edge_cases: bool = True,
        multilingual: bool = False,
        max_tests: int = 10
    ) -> List[GeneratedTest]:
        """Generate test cases for a target.
        
        Args:
            target: Target to test (function, class, module)
            category: Test category
            complexity: Test complexity level
            edge_cases: Whether to generate edge cases
            multilingual: Whether to generate multilingual tests
            max_tests: Maximum number of tests to generate
            
        Returns:
            List of generated test cases
        """
        # Check cache
        cache_key = self._get_cache_key(target, category, complexity)
        if cache_key in self.generation_cache:
            return self.generation_cache[cache_key]
        
        # Get target info
        target_info = self._get_target_info(target)
        
        # Create prompt
        prompt = self._create_test_prompt(
            target_info,
            category,
            complexity,
            edge_cases,
            multilingual
        )
        
        # Get API key
        api_key = await self.gemini.get_next_key()
        if not api_key:
            raise RuntimeError("No available Gemini API key")
        
        try:
            # Generate tests
            response = await self._call_gemini(api_key[0], prompt)
            
            # Parse and validate tests
            tests = self._parse_tests(response, target_info)
            
            # Limit number of tests
            tests = tests[:max_tests]
            
            # Cache results
            self.generation_cache[cache_key] = tests
            
            # Log successful API call
            self.gemini.log_api_call(
                api_key=api_key[0],
                endpoint='test_generation',
                success=True
            )
            
            return tests
            
        except Exception as e:
            # Log failed API call
            self.gemini.log_api_call(
                api_key=api_key[0],
                endpoint='test_generation',
                success=False,
                error_message=str(e)
            )
            raise
    
    def _get_cache_key(
        self,
        target: Any,
        category: str,
        complexity: str
    ) -> str:
        """Generate cache key for test generation.
        
        Args:
            target: Test target
            category: Test category
            complexity: Test complexity
            
        Returns:
            Cache key string
        """
        target_hash = hash(str(self._get_target_info(target)))
        return f"{target_hash}-{category}-{complexity}"
    
    def _get_target_info(self, target: Any) -> Dict[str, Any]:
        """Get information about test target.
        
        Args:
            target: Target to analyze
            
        Returns:
            Dictionary containing target info
        """
        info = {
            'name': getattr(target, '__name__', str(target)),
            'type': type(target).__name__,
            'doc': inspect.getdoc(target) or '',
            'source': None,
            'signature': None,
            'module': None,
            'class': None,
            'methods': [],
            'attributes': []
        }
        
        try:
            # Get source code
            info['source'] = inspect.getsource(target)
            
            # Get signature for functions
            if inspect.isfunction(target):
                info['signature'] = str(inspect.signature(target))
                info['module'] = target.__module__
                
            # Get class info
            elif inspect.isclass(target):
                info['module'] = target.__module__
                info['methods'] = [
                    (name, str(inspect.signature(method)))
                    for name, method in inspect.getmembers(target, inspect.isfunction)
                    if not name.startswith('_')
                ]
                info['attributes'] = [
                    name for name, _ in inspect.getmembers(target)
                    if not name.startswith('_') and not callable(getattr(target, name))
                ]
                
            # Get module info
            elif inspect.ismodule(target):
                info['module'] = target.__name__
                ast_tree = ast.parse(info['source'])
                for node in ast.walk(ast_tree):
                    if isinstance(node, ast.ClassDef):
                        info['class'] = node.name
                        
        except Exception as e:
            logger.warning(f"Error getting target info: {str(e)}")
            
        return info
    
    def _create_test_prompt(
        self,
        target_info: Dict[str, Any],
        category: str,
        complexity: str,
        edge_cases: bool,
        multilingual: bool
    ) -> str:
        """Create prompt for test generation.
        
        Args:
            target_info: Target information
            category: Test category
            complexity: Test complexity
            edge_cases: Whether to generate edge cases
            multilingual: Whether to generate multilingual tests
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""
        Generate comprehensive test cases for the following code:
        
        TARGET INFO:
        Name: {target_info['name']}
        Type: {target_info['type']}
        
        DOCUMENTATION:
        {target_info['doc']}
        
        SOURCE CODE:
        {target_info['source']}
        
        {f"SIGNATURE: {target_info['signature']}" if target_info['signature'] else ""}
        
        {f"METHODS: {target_info['methods']}" if target_info['methods'] else ""}
        
        {f"ATTRIBUTES: {target_info['attributes']}" if target_info['attributes'] else ""}
        
        REQUIREMENTS:
        - Test Category: {category}
        - Complexity Level: {complexity}
        - Include Edge Cases: {edge_cases}
        - Multilingual Testing: {multilingual}
        
        Generate test cases in the following JSON format:
        {{
            "test_cases": [
                {{
                    "test_id": "unique_test_id",
                    "name": "descriptive_test_name",
                    "category": "{category}",
                    "description": "detailed test description",
                    "inputs": {{}},
                    "expected_outputs": {{}},
                    "assertions": [
                        "list of assertions to verify"
                    ],
                    "setup_code": "optional setup code",
                    "cleanup_code": "optional cleanup code",
                    "edge_case": boolean,
                    "multilingual": boolean,
                    "metadata": {{}}
                }}
            ]
        }}
        
        Focus on:
        1. Comprehensive test coverage
        2. Edge cases and boundary conditions
        3. Error handling scenarios
        4. Performance considerations
        5. Security implications
        6. Multilingual scenarios (if enabled)
        
        For assertions, use standard Python assert statements or pytest assertions.
        Include detailed descriptions explaining the purpose of each test.
        """
        
        return prompt
    
    async def _call_gemini(self, api_key: str, prompt: str) -> str:
        """Call Gemini API to generate tests.
        
        Args:
            api_key: Gemini API key
            prompt: Formatted prompt string
            
        Returns:
            Generated test cases as string
        """
        # TODO: Implement actual Gemini API call
        # For now, return a mock response
        return json.dumps({
            "test_cases": [
                {
                    "test_id": f"test_{self.test_counter + 1}",
                    "name": "test_basic_functionality",
                    "category": "unit",
                    "description": "Test basic functionality with valid inputs",
                    "inputs": {"x": 1, "y": 2},
                    "expected_outputs": {"result": 3},
                    "assertions": [
                        "assert result == expected_output"
                    ],
                    "edge_case": False,
                    "multilingual": False,
                    "metadata": {}
                }
            ]
        })
    
    def _parse_tests(
        self,
        response: str,
        target_info: Dict[str, Any]
    ) -> List[GeneratedTest]:
        """Parse and validate generated tests.
        
        Args:
            response: JSON response from Gemini
            target_info: Target information
            
        Returns:
            List of validated test cases
        """
        try:
            data = json.loads(response)
            tests = []
            
            for test_data in data.get('test_cases', []):
                # Validate required fields
                required_fields = {
                    'test_id', 'name', 'category', 'description',
                    'inputs', 'expected_outputs', 'assertions'
                }
                missing_fields = required_fields - set(test_data.keys())
                if missing_fields:
                    logger.warning(
                        f"Test case missing required fields: {missing_fields}"
                    )
                    continue
                
                # Create test case
                test = GeneratedTest(
                    test_id=test_data['test_id'],
                    name=test_data['name'],
                    category=test_data['category'],
                    description=test_data['description'],
                    inputs=test_data['inputs'],
                    expected_outputs=test_data['expected_outputs'],
                    assertions=test_data['assertions'],
                    setup_code=test_data.get('setup_code'),
                    cleanup_code=test_data.get('cleanup_code'),
                    edge_case=test_data.get('edge_case', False),
                    multilingual=test_data.get('multilingual', False),
                    metadata=test_data.get('metadata', {})
                )
                
                # Validate test case
                if self._validate_test(test, target_info):
                    tests.append(test)
                    self.test_counter += 1
            
            return tests
            
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON response from Gemini")
        except Exception as e:
            raise ValueError(f"Error parsing test cases: {str(e)}")
    
    def _validate_test(
        self,
        test: GeneratedTest,
        target_info: Dict[str, Any]
    ) -> bool:
        """Validate a generated test case.
        
        Args:
            test: Test case to validate
            target_info: Target information
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Validate test ID format
            if not test.test_id.startswith('test_'):
                return False
            
            # Validate inputs match signature
            if target_info['signature']:
                sig = inspect.signature(eval(target_info['signature']))
                for param in sig.parameters:
                    if param not in test.inputs:
                        return False
            
            # Validate assertions
            for assertion in test.assertions:
                ast.parse(assertion)
            
            # Validate setup/cleanup code
            if test.setup_code:
                ast.parse(test.setup_code)
            if test.cleanup_code:
                ast.parse(test.cleanup_code)
            
            return True
            
        except Exception as e:
            logger.warning(f"Test validation failed: {str(e)}")
            return False 