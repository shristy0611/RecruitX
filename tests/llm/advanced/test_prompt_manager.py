"""
Tests for the Advanced LLM Prompt Manager.

This module tests the prompt management functionality, including:
- Template creation and updating
- Few-shot prompting
- Chain-of-thought prompting
- Template validation
"""

import unittest
import time
import json
import os
from unittest.mock import patch, MagicMock
from typing import Dict, List, Any

from src.llm.advanced.prompt_manager import PromptTemplate, PromptManager


class TestPromptTemplate(unittest.TestCase):
    """Test the PromptTemplate implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.template = PromptTemplate(
            id="test_template",
            name="Test Template",
            template="This is a test template with {parameter1} and {parameter2}.",
            version="1.0",
            description="Test description",
            domain="test",
            tags=["test", "sample"],
            parameters=["parameter1", "parameter2"]
        )
        
    def test_basic_properties(self):
        """Test basic properties of PromptTemplate."""
        self.assertEqual(self.template.id, "test_template")
        self.assertEqual(self.template.name, "Test Template")
        self.assertEqual(self.template.version, "1.0")
        self.assertEqual(self.template.domain, "test")
        self.assertEqual(len(self.template.tags), 2)
        
    def test_format(self):
        """Test template formatting with parameters."""
        formatted = self.template.format(
            parameter1="value1", 
            parameter2="value2"
        )
        
        self.assertEqual(
            formatted, 
            "This is a test template with value1 and value2."
        )
        
    def test_format_missing_parameter(self):
        """Test formatting with missing required parameter raises error."""
        with self.assertRaises(KeyError):
            self.template.format(parameter1="value1")
            
    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        template_dict = self.template.to_dict()
        
        self.assertEqual(template_dict["id"], self.template.id)
        self.assertEqual(template_dict["name"], self.template.name)
        self.assertEqual(template_dict["template"], self.template.template)
        self.assertEqual(template_dict["tags"], self.template.tags)
        
    def test_from_dict_conversion(self):
        """Test creation from dictionary."""
        template_dict = self.template.to_dict()
        new_template = PromptTemplate.from_dict(template_dict)
        
        self.assertEqual(new_template.id, self.template.id)
        self.assertEqual(new_template.name, self.template.name)
        self.assertEqual(new_template.template, self.template.template)
        
    def test_add_example(self):
        """Test adding few-shot examples."""
        self.template.add_example(
            inputs={"parameter1": "example1", "parameter2": "example2"},
            output="Example output"
        )
        
        self.assertEqual(len(self.template.examples), 1)
        self.assertEqual(
            self.template.examples[0]["inputs"]["parameter1"], 
            "example1"
        )
        
    def test_clear_examples(self):
        """Test clearing examples."""
        self.template.add_example(
            inputs={"parameter1": "example1", "parameter2": "example2"},
            output="Example output"
        )
        self.template.clear_examples()
        
        self.assertEqual(len(self.template.examples), 0)
        
    def test_update_metrics(self):
        """Test updating performance metrics."""
        self.template.update_metrics({"accuracy": 0.95, "latency": 120})
        
        self.assertEqual(self.template.performance_metrics["accuracy"], 0.95)
        self.assertEqual(self.template.performance_metrics["latency"], 120)


class TestPromptManager(unittest.TestCase):
    """Test the PromptManager implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_context_manager = MagicMock()
        with patch("src.llm.advanced.prompt_manager.get_context_manager", 
                  return_value=self.mock_context_manager):
            self.prompt_manager = PromptManager()
        
    def test_default_library_initialization(self):
        """Test that default templates are initialized."""
        # Check if some expected default templates exist
        self.assertIn("base_resume_analysis", self.prompt_manager.templates)
        self.assertIn("cot_resume_analysis", self.prompt_manager.templates)
        self.assertIn("skill_extraction", self.prompt_manager.templates)
        
    def test_get_template(self):
        """Test retrieving a template by ID."""
        template = self.prompt_manager.get_template("base_resume_analysis")
        
        self.assertIsNotNone(template)
        self.assertEqual(template.id, "base_resume_analysis")
        
        # Test non-existent template
        template = self.prompt_manager.get_template("nonexistent_template")
        self.assertIsNone(template)
        
    def test_create_template(self):
        """Test creating a new template."""
        template = self.prompt_manager.create_template(
            name="New Test Template",
            template="This is a {test} template.",
            description="Test description",
            domain="testing",
            tags=["test"]
        )
        
        self.assertIsNotNone(template)
        self.assertEqual(template.name, "New Test Template")
        
        # Test parameter auto-detection
        self.assertIn("test", template.parameters)
        
        # Test that template was added to library
        self.assertIn(template.id, self.prompt_manager.templates)
        
    def test_update_template(self):
        """Test updating an existing template."""
        # First create a template
        template = self.prompt_manager.create_template(
            name="Template To Update",
            template="Original {text}.",
            description="Original description"
        )
        
        template_id = template.id
        
        # Update it
        updated = self.prompt_manager.update_template(
            template_id,
            name="Updated Template",
            template="Updated {text} with {new_param}."
        )
        
        self.assertEqual(updated.name, "Updated Template")
        self.assertEqual(updated.template, "Updated {text} with {new_param}.")
        
        # Test parameter auto-update
        self.assertIn("text", updated.parameters)
        self.assertIn("new_param", updated.parameters)
        
    def test_delete_template(self):
        """Test deleting a template."""
        # First create a template
        template = self.prompt_manager.create_template(
            name="Template To Delete",
            template="Delete me {param}."
        )
        
        template_id = template.id
        self.assertIn(template_id, self.prompt_manager.templates)
        
        # Delete it
        result = self.prompt_manager.delete_template(template_id)
        self.assertTrue(result)
        self.assertNotIn(template_id, self.prompt_manager.templates)
        
        # Test deleting non-existent template
        result = self.prompt_manager.delete_template("nonexistent_template")
        self.assertFalse(result)
        
    def test_format_prompt(self):
        """Test formatting a prompt with parameters."""
        template_id = "base_resume_analysis"
        params = {
            "resume_text": "Sample resume",
            "job_description": "Sample job"
        }
        
        formatted = self.prompt_manager.format_prompt(template_id, params)
        
        self.assertIn("Sample resume", formatted)
        self.assertIn("Sample job", formatted)
        
        # Test with non-existent template
        with self.assertRaises(ValueError):
            self.prompt_manager.format_prompt("nonexistent_template", {})
            
    def test_create_few_shot_prompt(self):
        """Test creating a few-shot prompt."""
        # Create a simple template for testing
        template = self.prompt_manager.create_template(
            name="Few-Shot Test",
            template="Question: {question}\nAnswer: "
        )
        
        template_id = template.id
        
        # Create examples
        examples = [
            {
                "inputs": {"question": "What is 1+1?"},
                "output": "2"
            },
            {
                "inputs": {"question": "What is 2+2?"},
                "output": "4"
            }
        ]
        
        # Create query
        query_params = {"question": "What is 3+3?"}
        
        # Generate few-shot prompt
        few_shot = self.prompt_manager.create_few_shot_prompt(
            template_id=template_id,
            examples=examples,
            query_params=query_params
        )
        
        # Verify it contains examples and query
        self.assertIn("What is 1+1?", few_shot)
        self.assertIn("What is 2+2?", few_shot)
        self.assertIn("What is 3+3?", few_shot)
        self.assertIn("Answer: 2", few_shot)
        self.assertIn("Answer: 4", few_shot)
        
    def test_create_cot_prompt(self):
        """Test creating a chain-of-thought prompt."""
        base_prompt = "Solve this math problem: 3 * (4 + 2) - 5"
        
        cot_prompt = self.prompt_manager.create_cot_prompt(
            base_prompt=base_prompt,
            num_steps=3
        )
        
        # Verify it contains the base prompt and steps
        self.assertIn(base_prompt, cot_prompt)
        self.assertIn("Step 1:", cot_prompt)
        self.assertIn("Step 2:", cot_prompt)
        self.assertIn("Step 3:", cot_prompt)
        self.assertIn("Final conclusion", cot_prompt)
        
    def test_create_optimized_prompt(self):
        """Test creating a context-optimized prompt."""
        # Set up mock context manager response
        self.mock_context_manager.get_relevant_context.return_value = {
            "context_text": "This is relevant context.",
            "sources": [{"id": "doc1", "relevance": 0.9}],
            "token_count": 10,
            "relevance_score": 0.9,
            "cached": False
        }
        
        # Create a template with context parameter
        template = self.prompt_manager.create_template(
            name="Context Template",
            template="Question: {question}\nContext: {context}\nAnswer: "
        )
        
        template_id = template.id
        
        # Test optimized prompt creation
        optimized = self.prompt_manager.create_optimized_prompt(
            template_id=template_id,
            params={"question": "Test question"},
            query="Test query",
            domain="test"
        )
        
        # Verify context manager was called
        self.mock_context_manager.get_relevant_context.assert_called_once()
        
        # Verify prompt contains question and context
        self.assertIn("Test question", optimized)
        self.assertIn("This is relevant context.", optimized)
        

if __name__ == "__main__":
    unittest.main()
