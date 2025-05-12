"""
Tests for the Advanced LLM Service.

This module tests the advanced LLM integration functionality, including:
- Intelligent model selection
- Context-aware content generation
- Chain-of-thought reasoning
- Metrics tracking
- Fallback strategies
"""

import unittest
import time
import json
from unittest.mock import patch, MagicMock, PropertyMock
from typing import Dict, List, Any

from src.llm.advanced.advanced_llm_service import (
    AdvancedLLMService,
    ModelSelectionStrategy
)
from src.utils.config import (
    GEMINI_PRO_MODEL,
    GEMINI_THINKING_MODEL,
    GEMMA_MODEL
)


class TestModelSelectionStrategy(unittest.TestCase):
    """Test the ModelSelectionStrategy implementation."""
    
    def test_model_selection_defaults(self):
        """Test model selection with default strategies."""
        # Test quality-optimized strategy for reasoning
        model = ModelSelectionStrategy.select_model(
            task_type="reasoning",
            strategy=ModelSelectionStrategy.QUALITY_OPTIMIZED
        )
        self.assertIn(model, [GEMINI_PRO_MODEL, GEMINI_THINKING_MODEL, GEMMA_MODEL])
        
        # Test cost-optimized strategy
        model = ModelSelectionStrategy.select_model(
            task_type="multilingual",
            strategy=ModelSelectionStrategy.COST_OPTIMIZED
        )
        self.assertIn(model, [GEMINI_PRO_MODEL, GEMINI_THINKING_MODEL, GEMMA_MODEL])
        
    def test_model_selection_with_constraints(self):
        """Test model selection with available model constraints."""
        # Test with limited available models
        model = ModelSelectionStrategy.select_model(
            task_type="reasoning",
            strategy=ModelSelectionStrategy.QUALITY_OPTIMIZED,
            available_models=[GEMMA_MODEL]
        )
        self.assertEqual(model, GEMMA_MODEL)
        
        # Test with multiple available models
        model = ModelSelectionStrategy.select_model(
            task_type="code_generation",
            strategy=ModelSelectionStrategy.BALANCED,
            available_models=[GEMINI_PRO_MODEL, GEMMA_MODEL]
        )
        self.assertIn(model, [GEMINI_PRO_MODEL, GEMMA_MODEL])


class TestAdvancedLLMService(unittest.TestCase):
    """Test the AdvancedLLMService implementation."""
    
    def setUp(self):
        """Set up test fixtures with mocked dependencies."""
        # Mock dependencies
        self.mock_gemini_service = MagicMock()
        self.mock_gemini_service.generate_content.return_value = "Gemini response"
        
        self.mock_gemma_service = MagicMock()
        self.mock_gemma_service.generate_content.return_value = "Gemma response"
        
        self.mock_context_manager = MagicMock()
        self.mock_context_manager.get_memoized_result.return_value = None
        self.mock_context_manager.get_relevant_context.return_value = {
            "context_text": "Relevant context for testing",
            "sources": [{"id": "doc1", "relevance": 0.9}],
            "token_count": 10,
            "relevance_score": 0.9,
            "cached": False
        }
        
        self.mock_prompt_manager = MagicMock()
        self.mock_prompt_manager.format_prompt.return_value = "Formatted prompt"
        self.mock_prompt_manager.get_template.return_value = MagicMock(parameters=["param1", "context"])
        
        # Apply patches
        self.patches = [
            patch("src.llm.advanced.advanced_llm_service.get_gemini_service", 
                  return_value=self.mock_gemini_service),
            patch("src.llm.advanced.advanced_llm_service.get_gemma_service", 
                  return_value=self.mock_gemma_service),
            patch("src.llm.advanced.advanced_llm_service.get_context_manager", 
                  return_value=self.mock_context_manager),
            patch("src.llm.advanced.advanced_llm_service.get_prompt_manager", 
                  return_value=self.mock_prompt_manager),
            patch("src.llm.advanced.advanced_llm_service.GEMINI_API_KEYS", 
                  ["test_key"]),
            patch("src.llm.advanced.advanced_llm_service.GEMMA_API_KEYS", 
                  ["test_key"])
        ]
        
        for p in self.patches:
            p.start()
            
        # Create service instance
        self.service = AdvancedLLMService()
        
    def tearDown(self):
        """Clean up patches."""
        for p in self.patches:
            p.stop()
            
    def test_initialization(self):
        """Test service initialization."""
        self.assertIsNotNone(self.service.gemini_service)
        self.assertIsNotNone(self.service.gemma_service)
        self.assertIsNotNone(self.service.context_manager)
        self.assertIsNotNone(self.service.prompt_manager)
        self.assertTrue(self.service.gemini_available)
        self.assertTrue(self.service.gemma_available)
        self.assertIn(GEMINI_PRO_MODEL, self.service.available_models)
        self.assertIn(GEMINI_THINKING_MODEL, self.service.available_models)
        self.assertIn(GEMMA_MODEL, self.service.available_models)
        
    def test_generate_content_with_gemini(self):
        """Test content generation using Gemini."""
        response = self.service.generate_content(
            prompt="Test prompt",
            model=GEMINI_PRO_MODEL
        )
        
        self.assertEqual(response, "Gemini response")
        self.mock_gemini_service.generate_content.assert_called_once()
        args = self.mock_gemini_service.generate_content.call_args[1]
        self.assertEqual(args["prompt"], "Test prompt")
        self.assertEqual(args["model"], GEMINI_PRO_MODEL)
        
    def test_generate_content_with_gemma(self):
        """Test content generation using Gemma."""
        response = self.service.generate_content(
            prompt="Test prompt",
            model=GEMMA_MODEL
        )
        
        self.assertEqual(response, "Gemma response")
        self.mock_gemma_service.generate_content.assert_called_once()
        args = self.mock_gemma_service.generate_content.call_args[1]
        self.assertEqual(args["prompt"], "Test prompt")
        
    def test_generate_content_with_auto_selection(self):
        """Test content generation with automatic model selection."""
        response = self.service.generate_content(
            prompt="Test prompt",
            model=None,  # Auto-select
            task_type="reasoning"
        )
        
        # Should have used either Gemini or Gemma
        self.assertTrue(
            self.mock_gemini_service.generate_content.called or
            self.mock_gemma_service.generate_content.called
        )
        self.assertIn(response, ["Gemini response", "Gemma response"])
        
    def test_generate_with_cache(self):
        """Test content generation with cache hit."""
        # Mock a cache hit
        self.mock_context_manager.get_memoized_result.return_value = "Cached response"
        
        response = self.service.generate_content(
            prompt="Test prompt",
            use_cache=True
        )
        
        self.assertEqual(response, "Cached response")
        self.mock_context_manager.get_memoized_result.assert_called_once()
        
        # Neither service should be called on cache hit
        self.mock_gemini_service.generate_content.assert_not_called()
        self.mock_gemma_service.generate_content.assert_not_called()
        
    def test_generate_with_prompt_template(self):
        """Test generation using a prompt template."""
        response = self.service.generate_with_prompt_template(
            template_id="test_template",
            params={"param1": "value1"}
        )
        
        # Verify prompt manager was used to format template
        self.mock_prompt_manager.format_prompt.assert_called_once_with(
            "test_template", {"param1": "value1"}
        )
        
        # Verify formatted prompt was passed to generate_content
        self.assertEqual(response, "Gemini response")  # Assuming Gemini was selected
        
    def test_generate_with_context(self):
        """Test context-aware content generation."""
        result = self.service.generate_with_context(
            query="Test query",
            template_id="test_template",
            params={"param1": "value1"}
        )
        
        # Verify context was retrieved
        self.mock_context_manager.get_relevant_context.assert_called_once()
        
        # Verify prompt was formatted with context
        self.mock_prompt_manager.format_prompt.assert_called_once()
        
        # Verify result structure
        self.assertIn("content", result)
        self.assertIn("context_info", result)
        self.assertIn("model", result)
        self.assertIn("cache_hit", result)
        
    def test_generate_chain_of_thought(self):
        """Test chain-of-thought generation."""
        # Mock a CoT response with steps and conclusion
        self.mock_gemini_service.generate_content.return_value = (
            "Step 1: First I need to understand the problem.\n"
            "Step 2: Now I'll solve part of it.\n"
            "Step 3: Finally, I'll complete the solution.\n\n"
            "Final conclusion: The answer is 42."
        )
        
        result = self.service.generate_chain_of_thought(
            prompt="Solve this problem",
            num_steps=3
        )
        
        # Verify result structure
        self.assertIn("reasoning", result)
        self.assertIn("steps", result)
        self.assertIn("conclusion", result)
        self.assertIn("model", result)
        
        # Verify steps and conclusion extraction
        self.assertEqual(len(result["steps"]), 3)
        self.assertIn("The answer is 42", result["conclusion"])
        
    def test_generate_multilingual(self):
        """Test multilingual content generation."""
        response = self.service.generate_multilingual(
            prompt="Translate this text",
            language="es"  # Spanish
        )
        
        # Verify language instruction was added if not in original prompt
        generate_args = None
        if self.mock_gemini_service.generate_content.called:
            generate_args = self.mock_gemini_service.generate_content.call_args[1]
        elif self.mock_gemma_service.generate_content.called:
            generate_args = self.mock_gemma_service.generate_content.call_args[1]
            
        self.assertIsNotNone(generate_args)
        self.assertIn("respond in es", generate_args["prompt"].lower())
        
    def test_parallel_query(self):
        """Test parallel query execution."""
        prompts = ["Query 1", "Query 2"]
        
        # Test without combining results
        results = self.service.parallel_query(
            prompts=prompts,
            combine_results=False
        )
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        
        # Test with combining results
        combined = self.service.parallel_query(
            prompts=prompts,
            combine_results=True
        )
        
        self.assertIsInstance(combined, str)
        self.assertIn("Result 1", combined)
        self.assertIn("Result 2", combined)
        
    def test_metrics_tracking(self):
        """Test metrics tracking functionality."""
        # Generate content to create metrics
        self.service.generate_content("Test prompt 1")
        self.service.generate_content("Test prompt 2")
        
        # Mock a cache hit
        self.mock_context_manager.get_memoized_result.return_value = "Cached response"
        self.service.generate_content("Test prompt 3")
        
        # Get metrics
        metrics = self.service.get_metrics()
        
        # Verify basic metrics
        self.assertEqual(metrics["requests"], 3)
        self.assertEqual(metrics["successful_requests"], 3)
        self.assertEqual(metrics["cache_hits"], 1)
        
        # Model usage should be tracked
        model_usage = metrics["model_usage"]
        total_model_usage = sum(model_usage.values())
        self.assertEqual(total_model_usage, 2)  # Two direct LLM calls
        
    def test_fallback_strategy(self):
        """Test fallback strategy when primary model fails."""
        # Make Gemini service fail
        self.mock_gemini_service.generate_content.side_effect = Exception("Gemini error")
        
        # Should fall back to Gemma service
        response = self.service.generate_content(
            prompt="Test prompt",
            model=None  # Auto-select, which should trigger fallback
        )
        
        self.assertEqual(response, "Gemma response")
        self.mock_gemini_service.generate_content.assert_called()
        self.mock_gemma_service.generate_content.assert_called()


# Only run these integration tests if environment is properly configured
@unittest.skipUnless(
    os.environ.get("RUN_INTEGRATION_TESTS") == "1",
    "Skipping integration tests; set RUN_INTEGRATION_TESTS=1 to run"
)
class TestAdvancedLLMServiceIntegration(unittest.TestCase):
    """Integration tests for the AdvancedLLMService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = AdvancedLLMService()
        
    def test_basic_generation(self):
        """Test basic content generation with real LLMs."""
        response = self.service.generate_content(
            prompt="What is the capital of France?",
            max_output_tokens=100
        )
        
        self.assertIn("Paris", response)
        
    def test_context_aware_generation(self):
        """Test context-aware generation with real LLMs."""
        # This is a simplified test that will work even without proper vector store setup
        # In a complete integration test, we would ensure the vector store has relevant documents
        result = self.service.generate_with_context(
            query="What is recruitment?",
            template_id="context_aware_matching",  # Assuming this template exists in the default library
            params={
                "resume_text": "Sample resume text",
                "job_description": "Sample job description"
            }
        )
        
        # Should return a structured result with content
        self.assertIn("content", result)
        self.assertIsInstance(result["content"], str)
        self.assertIn("context_info", result)


if __name__ == "__main__":
    import os
    unittest.main()
