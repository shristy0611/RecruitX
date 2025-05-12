"""
Simplified tests for the Advanced LLM Integration.

This module provides basic functionality tests without heavy dependencies
to verify that the core implementation works as expected.
"""

import unittest
from unittest.mock import patch, MagicMock


class TestAdvancedLLMBasics(unittest.TestCase):
    """Basic tests for the Advanced LLM Integration components."""
    
    def test_expiring_cache(self):
        """Test the ExpiringCache implementation with basic operations."""
        # Import here to avoid heavy dependencies
        from src.llm.advanced.context_manager import ExpiringCache
        
        # Create a cache with small size for testing
        cache = ExpiringCache(max_size=3, ttl_seconds=3600)
        
        # Test basic operations
        cache["key1"] = "value1"
        self.assertEqual(cache["key1"], "value1")
        self.assertTrue("key1" in cache)
        
        # Test get default
        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.get("nonexistent", "default"), "default")
        
        # Test deletion
        cache.delete("key1")
        self.assertFalse("key1" in cache)
        
        # Test LRU eviction when max size is reached
        cache["key1"] = "value1"
        cache["key2"] = "value2"
        cache["key3"] = "value3"
        
        # Access key1 to make it recently used
        _ = cache["key1"]
        
        # Add a new item to trigger eviction
        cache["key4"] = "value4"
        
        # key2 should be evicted (least recently used)
        self.assertFalse("key2" in cache)
        self.assertTrue("key1" in cache)
        self.assertTrue("key3" in cache)
        self.assertTrue("key4" in cache)
    
    @patch("src.llm.advanced.prompt_manager.get_context_manager")
    def test_prompt_template(self, mock_get_context_manager):
        """Test PromptTemplate with basic operations."""
        # Mock context manager to avoid dependencies
        mock_get_context_manager.return_value = MagicMock()
        
        # Import here to avoid heavy dependencies
        from src.llm.advanced.prompt_manager import PromptTemplate
        
        # Create a template
        template = PromptTemplate(
            id="test_template",
            name="Test Template",
            template="Hello, {name}! Welcome to {service}.",
            parameters=["name", "service"]
        )
        
        # Test basic properties
        self.assertEqual(template.id, "test_template")
        self.assertEqual(template.name, "Test Template")
        
        # Test formatting
        formatted = template.format(name="User", service="RecruitPro")
        self.assertEqual(formatted, "Hello, User! Welcome to RecruitPro.")
        
        # Test to_dict conversion
        template_dict = template.to_dict()
        self.assertEqual(template_dict["id"], "test_template")
        self.assertEqual(template_dict["name"], "Test Template")
        
        # Test from_dict conversion
        new_template = PromptTemplate.from_dict(template_dict)
        self.assertEqual(new_template.id, "test_template")
        self.assertEqual(new_template.template, "Hello, {name}! Welcome to {service}.")
    
    @patch("src.llm.advanced.prompt_manager.get_context_manager")
    def test_prompt_manager_basics(self, mock_get_context_manager):
        """Test basic PromptManager operations."""
        # Mock context manager to avoid dependencies
        mock_get_context_manager.return_value = MagicMock()
        
        # Import here to avoid heavy dependencies
        from src.llm.advanced.prompt_manager import PromptManager
        
        # Create manager
        manager = PromptManager()
        
        # Verify default templates are loaded
        self.assertIn("base_resume_analysis", manager.templates)
        self.assertIn("skill_extraction", manager.templates)
        
        # Test template creation
        template = manager.create_template(
            name="Test Template",
            template="This is a {test} template."
        )
        
        self.assertEqual(template.name, "Test Template")
        self.assertIn("test", template.parameters)  # Auto-detected parameter
        
        # Test template formatting
        formatted = manager.format_prompt(
            template_id=template.id,
            params={"test": "simple"}
        )
        
        self.assertEqual(formatted, "This is a simple template.")
    
    @patch("src.llm.advanced.advanced_llm_service.get_gemini_service")
    @patch("src.llm.advanced.advanced_llm_service.get_gemma_service")
    @patch("src.llm.advanced.advanced_llm_service.get_context_manager")
    @patch("src.llm.advanced.advanced_llm_service.get_prompt_manager")
    def test_advanced_llm_service_basics(
        self, 
        mock_get_prompt_manager,
        mock_get_context_manager,
        mock_get_gemma_service,
        mock_get_gemini_service
    ):
        """Test basic AdvancedLLMService operations."""
        # Set up mocks to avoid dependencies
        mock_gemini = MagicMock()
        mock_gemini.generate_content.return_value = "Gemini response"
        mock_get_gemini_service.return_value = mock_gemini
        
        mock_gemma = MagicMock()
        mock_gemma.generate_content.return_value = "Gemma response"
        mock_get_gemma_service.return_value = mock_gemma
        
        mock_context = MagicMock()
        mock_context.get_memoized_result.return_value = None
        mock_get_context_manager.return_value = mock_context
        
        mock_prompt = MagicMock()
        mock_prompt.format_prompt.return_value = "Formatted prompt"
        mock_get_prompt_manager.return_value = mock_prompt
        
        # Import dependent on mocks being set up
        from src.llm.advanced.advanced_llm_service import AdvancedLLMService
        from src.utils.config import GEMINI_PRO_MODEL, GEMMA_MODEL
        
        # Patch config values to ensure test stability
        with patch("src.llm.advanced.advanced_llm_service.GEMINI_API_KEYS", ["test_key"]), \
             patch("src.llm.advanced.advanced_llm_service.GEMMA_API_KEYS", ["test_key"]):
            
            # Create service
            service = AdvancedLLMService()
            
            # Test basic content generation with Gemini
            response = service.generate_content(
                prompt="Test prompt",
                model=GEMINI_PRO_MODEL
            )
            
            self.assertEqual(response, "Gemini response")
            mock_gemini.generate_content.assert_called_once()
            
            # Reset mock
            mock_gemini.generate_content.reset_mock()
            
            # Test basic content generation with Gemma
            response = service.generate_content(
                prompt="Test prompt",
                model=GEMMA_MODEL
            )
            
            self.assertEqual(response, "Gemma response")
            mock_gemma.generate_content.assert_called_once()


if __name__ == "__main__":
    unittest.main()
