"""
Advanced Context Manager for LLM interactions in RecruitPro AI.

This module provides sophisticated context management for LLM interactions,
implementing prompt context caching, result memoization, and intelligent
context retrieval to optimize LLM performance and reduce token usage.
"""

import json
import logging
import time
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta
from threading import Lock

import numpy as np

# Use lazy imports for SentenceTransformer to avoid dependency issues
_sentence_transformer = None
_st_util = None

def _get_sentence_transformer():
    """Lazy load the SentenceTransformer module."""
    global _sentence_transformer, _st_util
    if _sentence_transformer is None:
        try:
            from sentence_transformers import SentenceTransformer as ST
            from sentence_transformers import util
            _sentence_transformer = ST
            _st_util = util
            logger.info("Successfully loaded SentenceTransformer")
        except ImportError:
            logger.warning("SentenceTransformer not available, similarity functions will be limited")
            _sentence_transformer = None
            _st_util = None
    return _sentence_transformer, _st_util

from src.knowledge_base.vector_store import VectorStore, get_vector_store
from src.utils.config import EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class ExpiringCache:
    """
    Thread-safe cache with item expiration and LRU eviction policy.
    
    Features:
    - Time-based expiration (TTL)
    - LRU eviction when max size is reached
    - Thread-safe operations
    - Optional callback on eviction
    - Statistics tracking
    """
    
    def __init__(
        self, 
        max_size: int = 1000, 
        ttl_seconds: int = 3600,
        on_evict: Optional[Callable[[str, Any], None]] = None
    ):
        """
        Initialize the expiring cache.
        
        Args:
            max_size: Maximum number of items in cache
            ttl_seconds: Time to live in seconds for each item
            on_evict: Optional callback when item is evicted
        """
        self._cache = {}  # {key: (value, expiry_timestamp, access_count)}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._lock = Lock()
        self._on_evict = on_evict
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expired_removals": 0,
            "manual_removals": 0
        }
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache and is not expired."""
        with self._lock:
            if key not in self._cache:
                return False
            
            _, expiry, _ = self._cache[key]
            if time.time() > expiry:
                # Expired, remove it
                self._remove_item(key, "expired")
                return False
                
            return True
    
    def __getitem__(self, key: str) -> Any:
        """Get item from cache, raising KeyError if not found or expired."""
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                raise KeyError(key)
            
            value, expiry, access_count = self._cache[key]
            
            if time.time() > expiry:
                # Expired, remove it
                self._remove_item(key, "expired")
                self._stats["misses"] += 1
                raise KeyError(key)
            
            # Update access count and return value
            self._cache[key] = (value, expiry, access_count + 1)
            self._stats["hits"] += 1
            return value
    
    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set an item in the cache with the configured TTL.
        Evicts least recently used items if max size reached.
        """
        with self._lock:
            # Check if we need to make room
            if key not in self._cache and len(self._cache) >= self._max_size:
                # Find least recently accessed item
                lru_key = min(self._cache, key=lambda k: self._cache[k][2])
                self._remove_item(lru_key, "evicted")
            
            # Add or update item
            self._cache[key] = (value, time.time() + self._ttl_seconds, 0)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get item from cache, returning default if not found or expired."""
        try:
            return self[key]
        except KeyError:
            return default
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set an item in the cache with an optional custom TTL.
        
        Args:
            key: Cache key
            value: Value to store
            ttl_seconds: Optional custom TTL (defaults to configured TTL)
        """
        with self._lock:
            # Use custom TTL if provided, otherwise use default
            actual_ttl = ttl_seconds if ttl_seconds is not None else self._ttl_seconds
            
            # Check if we need to make room
            if key not in self._cache and len(self._cache) >= self._max_size:
                # Find least recently accessed item
                lru_key = min(self._cache, key=lambda k: self._cache[k][2])
                self._remove_item(lru_key, "evicted")
            
            # Add or update item
            self._cache[key] = (value, time.time() + actual_ttl, 0)
    
    def delete(self, key: str) -> bool:
        """Delete an item from the cache, returning True if found and deleted."""
        with self._lock:
            if key in self._cache:
                self._remove_item(key, "manual")
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items from the cache."""
        with self._lock:
            for key in list(self._cache.keys()):
                self._remove_item(key, "manual")
    
    def _remove_item(self, key: str, reason: str) -> None:
        """
        Remove an item from the cache.
        
        Args:
            key: Cache key to remove
            reason: Reason for removal ("expired", "evicted", or "manual")
        """
        if key in self._cache:
            value, _, _ = self._cache[key]
            
            # Call eviction callback if provided
            if self._on_evict:
                try:
                    self._on_evict(key, value)
                except Exception as e:
                    logger.error(f"Error in eviction callback for key {key}: {e}")
            
            # Update stats
            if reason == "expired":
                self._stats["expired_removals"] += 1
            elif reason == "evicted":
                self._stats["evictions"] += 1
            else:  # "manual"
                self._stats["manual_removals"] += 1
            
            # Remove the item
            del self._cache[key]
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        with self._lock:
            stats = self._stats.copy()
            stats["size"] = len(self._cache)
            stats["max_size"] = self._max_size
            return stats
    
    def get_keys(self) -> List[str]:
        """Get all non-expired keys in the cache."""
        with self._lock:
            now = time.time()
            valid_keys = [k for k, (_, exp, _) in self._cache.items() if exp > now]
            return valid_keys


class ContextManager:
    """
    Advanced context management for LLM interactions.
    
    Features:
    - Context caching with automatic expiration
    - Result memoization to avoid repeated LLM calls
    - Hybrid retrieval combining semantic and keyword search
    - Context relevance scoring and ranking
    - Smart context truncation to fit token limits
    - Domain-specific context filtering
    """
    
    def __init__(
        self, 
        vector_store: Optional[VectorStore] = None,
        embedding_model: str = EMBEDDING_MODEL,
        cache_size: int = 1000,
        context_ttl_seconds: int = 3600,  # 1 hour
        result_ttl_seconds: int = 86400    # 24 hours
    ):
        """
        Initialize the context manager.
        
        Args:
            vector_store: Optional vector store for retrieval
            embedding_model: Embedding model to use
            cache_size: Maximum cache size for context and results
            context_ttl_seconds: TTL for context cache items
            result_ttl_seconds: TTL for result cache items
        """
        self.vector_store = vector_store if vector_store else get_vector_store()
        
        # Initialize embedding model for local similarity calculations (lazy loading)
        self.embedding_model = None
        self.embedding_model_name = embedding_model
        self._initialize_embedding_model()
        
        # Initialize caches
        self.context_cache = ExpiringCache(
            max_size=cache_size,
            ttl_seconds=context_ttl_seconds,
            on_evict=self._on_context_evicted
        )
        
        self.result_cache = ExpiringCache(
            max_size=cache_size,
            ttl_seconds=result_ttl_seconds,
            on_evict=self._on_result_evicted
        )
        
        # Statistics tracking
        self.stats = {
            "context_retrievals": 0,
            "result_cache_hits": 0,
            "result_cache_misses": 0,
            "context_bytes_saved": 0
        }
    
    def get_relevant_context(
        self,
        query: str,
        domain: str = "recruitment",
        max_documents: int = 5,
        max_tokens: int = 2000,
        min_relevance: float = 0.65,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get relevant context for a query.
        
        Args:
            query: The query to get context for
            domain: Domain for context filtering
            max_documents: Maximum number of documents to retrieve
            max_tokens: Maximum tokens to include in context
            min_relevance: Minimum relevance score (0-1) for documents
            filters: Additional filters for vector store query
        
        Returns:
            Dictionary with context information:
            {
                "context_text": str,  # Combined relevant context
                "sources": List[Dict],  # Source information
                "token_count": int,  # Estimated token count
                "relevance_score": float,  # Average relevance score
                "cached": bool  # Whether result was from cache
            }
        """
        # Update stats
        self.stats["context_retrievals"] += 1
        
        # Create a deterministic cache key
        cache_key = self._create_context_cache_key(
            query, domain, max_documents, max_tokens, min_relevance, filters
        )
        
        # Check cache first
        cached_context = self.context_cache.get(cache_key)
        if cached_context:
            # Update the bytes saved stat
            self.stats["context_bytes_saved"] += len(json.dumps(cached_context))
            cached_context["cached"] = True
            return cached_context
        
        # Prepare filters
        actual_filters = {"domain": domain}
        if filters:
            actual_filters.update(filters)
        
        # Get relevant documents from vector store
        try:
            results = self.vector_store.similarity_search(
                query=query,
                filter=actual_filters,
                top_k=max_documents + 3  # Get a few extra to allow filtering
            )
        except Exception as e:
            logger.error(f"Vector store query failed: {e}")
            results = []
        
        # If no results, return empty context
        if not results:
            empty_context = {
                "context_text": "",
                "sources": [],
                "token_count": 0,
                "relevance_score": 0.0,
                "cached": False
            }
            # Cache the empty result
            self.context_cache[cache_key] = empty_context
            return empty_context
        
        # Filter results by relevance score
        filtered_results = [r for r in results if r["score"] >= min_relevance]
        
        # Sort by relevance score
        filtered_results = sorted(filtered_results, key=lambda r: r["score"], reverse=True)
        
        # Limit to max_documents
        filtered_results = filtered_results[:max_documents]
        
        # Extract text and sources
        context_texts = []
        sources = []
        estimated_tokens = 0
        
        for result in filtered_results:
            # Estimate tokens (rough approximation: 4 chars ≈ 1 token)
            text = result["content"]
            text_tokens = len(text) // 4
            
            # Check if adding this would exceed max_tokens
            if estimated_tokens + text_tokens > max_tokens:
                continue
                
            context_texts.append(text)
            estimated_tokens += text_tokens
            
            # Add source information
            sources.append({
                "id": result["id"],
                "relevance": result["score"],
                "metadata": result.get("metadata", {})
            })
        
        # Combine context texts
        combined_context = "\n\n".join(context_texts)
        
        # Calculate average relevance score
        avg_relevance = sum(s["relevance"] for s in sources) / max(1, len(sources))
        
        # Create context result
        context_result = {
            "context_text": combined_context,
            "sources": sources,
            "token_count": estimated_tokens,
            "relevance_score": avg_relevance,
            "cached": False
        }
        
        # Cache the result
        self.context_cache[cache_key] = context_result
        
        return context_result
    
    def memoize_result(
        self,
        prompt: str,
        result: str,
        model: str = "default",
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Store a prompt->result pair in the result cache.
        
        Args:
            prompt: The prompt that generated the result
            result: The result to cache
            model: The model used to generate the result
            ttl_seconds: Optional custom TTL
        """
        cache_key = self._create_result_cache_key(prompt, model)
        self.result_cache.set(cache_key, result, ttl_seconds)
    
    def get_memoized_result(
        self,
        prompt: str,
        model: str = "default"
    ) -> Optional[str]:
        """
        Get a cached result for a prompt if available.
        
        Args:
            prompt: The prompt to check
            model: The model to check for
            
        Returns:
            Cached result or None if not found
        """
        cache_key = self._create_result_cache_key(prompt, model)
        result = self.result_cache.get(cache_key)
        
        if result is not None:
            self.stats["result_cache_hits"] += 1
        else:
            self.stats["result_cache_misses"] += 1
            
        return result
    
    def optimize_prompt(
        self,
        prompt_template: str,
        query: str,
        domain: str = "recruitment",
        max_context_tokens: int = 2000,
        include_sources: bool = False
    ) -> str:
        """
        Optimize a prompt by injecting relevant context.
        
        Args:
            prompt_template: Prompt template with {context} placeholder
            query: The query to get context for
            domain: Domain for context filtering
            max_context_tokens: Maximum tokens for injected context
            include_sources: Whether to include source information
            
        Returns:
            Optimized prompt with injected context
        """
        # Get relevant context
        context_info = self.get_relevant_context(
            query=query,
            domain=domain,
            max_tokens=max_context_tokens
        )
        
        # Get context text
        context_text = context_info["context_text"]
        
        # Add source information if requested
        if include_sources and context_info["sources"]:
            source_text = "\n\nSources:\n" + "\n".join(
                f"- {s['metadata'].get('title', 'Document ' + s['id'])}" 
                for s in context_info["sources"]
            )
            context_text += source_text
        
        # Replace {context} placeholder with actual context
        optimized_prompt = prompt_template.replace(
            "{context}", 
            context_text if context_text else "No relevant context found."
        )
        
        return optimized_prompt
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model with lazy loading."""
        if self.embedding_model is None:
            try:
                SentenceTransformer, _ = _get_sentence_transformer()
                if SentenceTransformer:
                    self.embedding_model = SentenceTransformer(self.embedding_model_name)
                    logger.info(f"Initialized embedding model: {self.embedding_model_name}")
                else:
                    logger.warning("SentenceTransformer not available, using fallback similarity")
            except Exception as e:
                logger.error(f"Failed to initialize embedding model: {e}")
                self.embedding_model = None

    def evaluate_query_similarity(
        self,
        query: str,
        previous_queries: List[str],
        threshold: float = 0.8
    ) -> Tuple[bool, float, Optional[int]]:
        """
        Evaluate if a query is semantically similar to previous queries.
        
        Args:
            query: The current query
            previous_queries: List of previous queries
            threshold: Similarity threshold (0-1)
            
        Returns:
            Tuple of (is_similar, max_similarity, index_of_most_similar)
        """
        if not previous_queries:
            return False, 0.0, None
        
        # Try to use SentenceTransformer if available
        if self.embedding_model is None:
            self._initialize_embedding_model()
            
        if self.embedding_model:
            # Get embeddings using SentenceTransformer
            try:
                _, st_util = _get_sentence_transformer()
                query_embedding = self.embedding_model.encode(query, convert_to_tensor=True)
                previous_embeddings = self.embedding_model.encode(
                    previous_queries, 
                    convert_to_tensor=True
                )
                
                # Calculate similarities
                similarities = st_util.pytorch_cos_sim(
                    query_embedding, 
                    previous_embeddings
                )[0].tolist()
                
                # Get max similarity and index
                max_similarity = max(similarities)
                max_index = similarities.index(max_similarity)
                
                return max_similarity >= threshold, max_similarity, max_index
                
            except Exception as e:
                logger.error(f"Error in SentenceTransformer similarity: {e}")
                # Fall back to simple similarity
        
        # Fallback: Simple token-based similarity
        try:
            # Simple token overlap similarity
            query_tokens = set(query.lower().split())
            max_similarity = 0.0
            max_index = 0
            
            for i, prev_query in enumerate(previous_queries):
                prev_tokens = set(prev_query.lower().split())
                if not query_tokens or not prev_tokens:
                    continue
                    
                # Jaccard similarity
                intersection = len(query_tokens.intersection(prev_tokens))
                union = len(query_tokens.union(prev_tokens))
                similarity = intersection / union if union > 0 else 0.0
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    max_index = i
            
            return max_similarity >= threshold, max_similarity, max_index
        except Exception as e:
            logger.error(f"Error in fallback similarity evaluation: {e}")
            return False, 0.0, None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context manager statistics."""
        stats = {
            **self.stats,
            "context_cache": self.context_cache.get_stats(),
            "result_cache": self.result_cache.get_stats()
        }
        return stats
    
    def _create_context_cache_key(
        self,
        query: str,
        domain: str,
        max_documents: int,
        max_tokens: int,
        min_relevance: float,
        filters: Optional[Dict[str, Any]]
    ) -> str:
        """Create a deterministic cache key for context retrieval."""
        key_parts = [
            query,
            domain,
            str(max_documents),
            str(max_tokens),
            str(min_relevance)
        ]
        
        if filters:
            # Sort filter items for deterministic ordering
            filter_str = json.dumps(filters, sort_keys=True)
            key_parts.append(filter_str)
        
        # Create a consolidated string and hash it
        key_str = "|".join(key_parts)
        return f"ctx_{hashlib.md5(key_str.encode()).hexdigest()}"
    
    def _create_result_cache_key(self, prompt: str, model: str) -> str:
        """Create a deterministic cache key for result memoization."""
        key_str = f"{model}|{prompt}"
        return f"res_{hashlib.md5(key_str.encode()).hexdigest()}"
    
    def _on_context_evicted(self, key: str, value: Any) -> None:
        """Callback when an item is evicted from context cache."""
        if DEBUG:
            logger.debug(f"Context cache item evicted: {key[:10]}...")
    
    def _on_result_evicted(self, key: str, value: Any) -> None:
        """Callback when an item is evicted from result cache."""
        if DEBUG:
            logger.debug(f"Result cache item evicted: {key[:10]}...")


# Singleton instance
_context_manager = None

def get_context_manager() -> ContextManager:
    """
    Get or create the ContextManager singleton.
    
    Returns:
        ContextManager instance
    """
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
