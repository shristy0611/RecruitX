"""
Tests for the Advanced LLM Context Manager.

This module tests the context management functionality, including:
- Expiring cache with LRU eviction
- Context retrieval and optimization
- Query similarity evaluation
"""

import unittest
import time
import json
from unittest.mock import patch, MagicMock
from typing import Dict, List, Any

from src.llm.advanced.context_manager import ExpiringCache, ContextManager


class TestExpiringCache(unittest.TestCase):
    """Test the ExpiringCache implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache = ExpiringCache(max_size=3, ttl_seconds=0.1)
        
    def test_basic_set_get(self):
        """Test basic set and get operations."""
        self.cache["key1"] = "value1"
        self.assertEqual(self.cache["key1"], "value1")
        self.assertTrue("key1" in self.cache)
        
    def test_item_expiration(self):
        """Test that items expire after TTL."""
        self.cache["key1"] = "value1"
        self.assertTrue("key1" in self.cache)
        
        # Wait for expiration
        time.sleep(0.2)
        
        self.assertFalse("key1" in self.cache)
        with self.assertRaises(KeyError):
            _ = self.cache["key1"]
            
    def test_lru_eviction(self):
        """Test LRU eviction when max size is reached."""
        # Fill the cache to capacity
        self.cache["key1"] = "value1"
        self.cache["key2"] = "value2"
        self.cache["key3"] = "value3"
        
        # Access key1 to make it most recently used
        _ = self.cache["key1"]
        
        # Add a new item to trigger eviction
        self.cache["key4"] = "value4"
        
        # key2 should be evicted (least recently used)
        self.assertFalse("key2" in self.cache)
        self.assertTrue("key1" in self.cache)
        self.assertTrue("key3" in self.cache)
        self.assertTrue("key4" in self.cache)
        
    def test_custom_ttl(self):
        """Test setting custom TTL for specific items."""
        # Set with default TTL
        self.cache["key1"] = "value1"
        
        # Set with custom TTL (longer)
        self.cache.set("key2", "value2", ttl_seconds=0.3)
        
        # Wait for default TTL to expire
        time.sleep(0.2)
        
        self.assertFalse("key1" in self.cache)  # Should be expired
        self.assertTrue("key2" in self.cache)   # Should still be valid
        
    def test_delete(self):
        """Test explicit deletion of items."""
        self.cache["key1"] = "value1"
        self.assertTrue("key1" in self.cache)
        
        self.cache.delete("key1")
        self.assertFalse("key1" in self.cache)
        
    def test_clear(self):
        """Test clearing the entire cache."""
        self.cache["key1"] = "value1"
        self.cache["key2"] = "value2"
        
        self.cache.clear()
        self.assertFalse("key1" in self.cache)
        self.assertFalse("key2" in self.cache)
        
    def test_get_stats(self):
        """Test statistics tracking."""
        self.cache["key1"] = "value1"
        _ = self.cache["key1"]  # Hit
        
        try:
            _ = self.cache["nonexistent"]  # Miss
        except KeyError:
            pass
            
        stats = self.cache.get_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["size"], 1)
        

class TestContextManager(unittest.TestCase):
    """Test the ContextManager implementation."""
    
    def setUp(self):
        """Set up test fixtures with mocked vector store."""
        # Create mock vector store
        self.mock_vector_store = MagicMock()
        self.mock_vector_store.similarity_search.return_value = [
            {
                "id": "doc1",
                "content": "This is a test document about recruitment.",
                "score": 0.9,
                "metadata": {"title": "Test Document 1"}
            },
            {
                "id": "doc2",
                "content": "Another document about hiring processes.",
                "score": 0.8,
                "metadata": {"title": "Test Document 2"}
            }
        ]
        
        # Create context manager with mock vector store
        with patch("src.llm.advanced.context_manager.get_vector_store", 
                  return_value=self.mock_vector_store):
            self.context_manager = ContextManager(
                vector_store=self.mock_vector_store,
                cache_size=10
            )
    
    def test_get_relevant_context(self):
        """Test retrieval of relevant context."""
        context_info = self.context_manager.get_relevant_context(
            query="recruitment process",
            domain="recruitment",
            max_documents=2
        )
        
        # Verify vector store was called correctly
        self.mock_vector_store.similarity_search.assert_called_once()
        call_args = self.mock_vector_store.similarity_search.call_args[1]
        self.assertEqual(call_args["query"], "recruitment process")
        self.assertEqual(call_args["filter"], {"domain": "recruitment"})
        
        # Verify returned context
        self.assertIn("context_text", context_info)
        self.assertIn("sources", context_info)
        self.assertEqual(len(context_info["sources"]), 2)
        self.assertFalse(context_info["cached"])
        
    def test_context_caching(self):
        """Test caching of context retrieval results."""
        # First call should hit the vector store
        context_info1 = self.context_manager.get_relevant_context(
            query="recruitment process",
            domain="recruitment"
        )
        
        # Reset the mock to verify it's not called again
        self.mock_vector_store.similarity_search.reset_mock()
        
        # Second call with same parameters should use cache
        context_info2 = self.context_manager.get_relevant_context(
            query="recruitment process",
            domain="recruitment"
        )
        
        # Verify vector store was not called again
        self.mock_vector_store.similarity_search.assert_not_called()
        
        # Verify second result indicates it was cached
        self.assertTrue(context_info2["cached"])
        
        # Content should be the same
        self.assertEqual(context_info1["context_text"], context_info2["context_text"])
        
    def test_result_memoization(self):
        """Test memoization of LLM results."""
        prompt = "Test prompt for memoization"
        result = "Test result that should be memoized"
        
        # Memoize a result
        self.context_manager.memoize_result(prompt, result, "test_model")
        
        # Retrieve the memoized result
        memoized = self.context_manager.get_memoized_result(prompt, "test_model")
        
        self.assertEqual(memoized, result)
        
    def test_optimize_prompt(self):
        """Test prompt optimization with context injection."""
        template = "Answer this question: {question}\n\nContext: {context}"
        
        # Mock the get_relevant_context method
        original_method = self.context_manager.get_relevant_context
        self.context_manager.get_relevant_context = MagicMock(return_value={
            "context_text": "Relevant context information here.",
            "sources": [{"id": "doc1", "relevance": 0.9}],
            "token_count": 10,
            "relevance_score": 0.9,
            "cached": False
        })
        
        # Optimize the prompt
        optimized = self.context_manager.optimize_prompt(
            prompt_template=template,
            query="test question",
            domain="recruitment"
        )
        
        # Verify context was injected
        self.assertIn("Relevant context information here.", optimized)
        
        # Restore original method
        self.context_manager.get_relevant_context = original_method
        

if __name__ == "__main__":
    unittest.main()
