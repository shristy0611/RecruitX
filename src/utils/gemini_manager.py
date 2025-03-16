import os
import sqlite3
import time
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    capacity: float
    fill_rate: float
    tokens: float = 0.0
    last_update: float = time.time()
    
    def get_tokens(self, now: float) -> float:
        """Update token count based on elapsed time."""
        if self.tokens < self.capacity:
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)
            self.last_update = now
        return self.tokens
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket."""
        now = time.time()
        tokens_available = self.get_tokens(now)
        if tokens_available >= tokens:
            self.tokens -= tokens
            return True
        return False

class GeminiKeyManager:
    """Manages Gemini API keys with advanced rotation and rate limiting."""
    
    # Constants for rate limiting and monitoring
    TOKENS_PER_MINUTE = 60  # Adjust based on Gemini's rate limits
    BUCKET_CAPACITY = 10
    ERROR_THRESHOLD = 0.3  # 30% error rate triggers cooldown
    COOLDOWN_MINUTES = 5
    CACHE_EXPIRY = 300  # 5 minutes
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent.parent / 'data' / 'prototype.db'
        self._setup_database()
        self.api_keys = self._load_api_keys()
        self.rate_limiters = {
            key: TokenBucket(
                capacity=self.BUCKET_CAPACITY,
                fill_rate=self.TOKENS_PER_MINUTE / 60.0
            ) for key in self.api_keys
        }
        self.error_counts = defaultdict(int)
        self.total_counts = defaultdict(int)
        self.cooldown_until = defaultdict(float)
        self.cache = {}
        self.cache_timestamps = {}
        
    def _setup_database(self):
        """Initialize database with enhanced schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS APIUsage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                latency FLOAT,
                tokens_used INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp 
            ON APIUsage(timestamp)
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_api_keys(self) -> List[str]:
        """Load and validate API keys from environment."""
        keys = []
        for i in range(1, 11):
            key = os.getenv(f'GEMINI_API_KEY_{i}')
            if key and len(key) > 20:  # Basic validation
                keys.append(key)
            elif key:
                logger.warning(f"Skipping invalid API key {i}")
        
        if not keys:
            logger.error("No valid API keys found!")
        return keys
    
    async def get_next_key(self) -> Optional[Tuple[str, float]]:
        """Get next available API key with confidence score."""
        if not self.api_keys:
            return None
            
        now = time.time()
        
        # Remove expired cache entries
        self._cleanup_cache(now)
        
        # Score each key based on multiple factors
        key_scores = []
        for key in self.api_keys:
            # Skip keys in cooldown
            if now < self.cooldown_until[key]:
                continue
                
            # Check rate limit
            if not self.rate_limiters[key].consume():
                continue
                
            # Calculate error rate
            total = self.total_counts[key]
            error_rate = self.error_counts[key] / total if total > 0 else 0
            
            # Calculate score based on error rate and usage
            score = 1.0 - error_rate
            
            # Penalize recently used keys slightly
            last_used = await self._get_last_used_time(key)
            if last_used:
                time_since_use = now - last_used
                score *= min(1.0, time_since_use / 60.0)  # Full score after 1 minute
                
            key_scores.append((key, score))
        
        if not key_scores:
            return None
            
        # Return key with highest score
        return max(key_scores, key=lambda x: x[1])
    
    async def _get_last_used_time(self, api_key: str) -> Optional[float]:
        """Get last usage time for a key with caching."""
        cache_key = f"last_used_{api_key}"
        
        # Check cache
        if cache_key in self.cache:
            if time.time() - self.cache_timestamps[cache_key] < self.CACHE_EXPIRY:
                return self.cache[cache_key]
        
        # Query database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT MAX(timestamp) 
            FROM APIUsage 
            WHERE api_key = ?
        ''', (api_key,))
        
        result = cursor.fetchone()[0]
        conn.close()
        
        if result:
            timestamp = datetime.fromisoformat(result).timestamp()
            # Update cache
            self.cache[cache_key] = timestamp
            self.cache_timestamps[cache_key] = time.time()
            return timestamp
        
        return None
    
    def log_api_call(
        self, 
        api_key: str, 
        endpoint: str, 
        success: bool, 
        error_message: Optional[str] = None,
        latency: Optional[float] = None,
        tokens_used: Optional[int] = None
    ):
        """Log API call with enhanced metrics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO APIUsage (
                    api_key, endpoint, success, error_message, latency, tokens_used
                )
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (api_key, endpoint, success, error_message, latency, tokens_used))
            
            conn.commit()
            
            # Update error tracking
            self.total_counts[api_key] += 1
            if not success:
                self.error_counts[api_key] += 1
                
                # Check error threshold
                error_rate = self.error_counts[api_key] / self.total_counts[api_key]
                if error_rate > self.ERROR_THRESHOLD:
                    self.cooldown_until[api_key] = time.time() + (self.COOLDOWN_MINUTES * 60)
                    logger.warning(f"API key {api_key[:8]}... placed in cooldown due to high error rate")
            
        except Exception as e:
            logger.error(f"Failed to log API call: {str(e)}")
        finally:
            conn.close()
    
    def get_usage_stats(self) -> Dict[str, Dict]:
        """Get detailed usage statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get comprehensive stats
        cursor.execute('''
            SELECT 
                api_key,
                COUNT(*) as total_calls,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls,
                AVG(CASE WHEN success = 1 THEN latency ELSE NULL END) as avg_latency,
                SUM(tokens_used) as total_tokens,
                COUNT(DISTINCT endpoint) as unique_endpoints,
                MAX(timestamp) as last_used
            FROM APIUsage
            GROUP BY api_key
        ''')
        
        stats = {}
        for row in cursor.fetchall():
            (api_key, total_calls, successful_calls, avg_latency, 
             total_tokens, unique_endpoints, last_used) = row
            
            stats[api_key] = {
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'success_rate': (successful_calls / total_calls * 100) if total_calls > 0 else 0,
                'avg_latency': round(avg_latency, 3) if avg_latency else None,
                'total_tokens': total_tokens or 0,
                'unique_endpoints': unique_endpoints,
                'last_used': last_used,
                'in_cooldown': time.time() < self.cooldown_until[api_key],
                'available_tokens': self.rate_limiters[api_key].tokens
            }
        
        conn.close()
        return stats
    
    def _cleanup_cache(self, now: float):
        """Remove expired cache entries."""
        expired = [
            k for k, ts in self.cache_timestamps.items()
            if now - ts > self.CACHE_EXPIRY
        ]
        for k in expired:
            del self.cache[k]
            del self.cache_timestamps[k] 