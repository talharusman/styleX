"""
Caching Layer

In-memory cache with TTL support for weather, face analysis, and recommendations.
Can be extended to use Redis in production.
"""

import time
import hashlib
import json
import asyncio
from typing import Optional, Any, Dict, Callable, TypeVar
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheEntry:
    """Single cache entry with TTL"""
    
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
    
    @property
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl


class InMemoryCache:
    """
    Thread-safe in-memory cache with TTL support.
    
    Features:
    - Automatic expiration
    - Key namespacing
    - Cache statistics
    - Background cleanup
    """
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
        self._enabled = True
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._enabled:
            return None
            
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                return None
            
            self._hits += 1
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache with TTL (default 5 minutes)"""
        if not self._enabled:
            return
            
        async with self._lock:
            self._cache[key] = CacheEntry(value, ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries, optionally by pattern"""
        async with self._lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                return count
            
            # Clear matching keys
            keys_to_delete = [k for k in self._cache if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries"""
        async with self._lock:
            expired = [k for k, v in self._cache.items() if v.is_expired]
            for key in expired:
                del self._cache[key]
            return len(expired)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            "enabled": self._enabled,
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%"
        }
    
    def enable(self):
        """Enable caching"""
        self._enabled = True
    
    def disable(self):
        """Disable caching"""
        self._enabled = False


# Global cache instance
_cache = InMemoryCache()


def get_cache() -> InMemoryCache:
    """Get the global cache instance"""
    return _cache


def generate_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments"""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(namespace: str, ttl: int = 300):
    """
    Decorator to cache async function results.
    
    Usage:
        @cached("weather", ttl=600)
        async def get_weather(location: str):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            cache = get_cache()
            
            # Generate cache key
            key = f"{namespace}:{generate_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = await cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {key}")
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(key, result, ttl)
            logger.debug(f"Cache miss: {key}")
            
            return result
        
        return wrapper
    return decorator


# Cache namespaces for different features
class CacheNamespaces:
    WEATHER = "weather"
    FACE_ANALYSIS = "face_analysis"
    RECOMMENDATION = "recommendation"
    USER_PROFILE = "user_profile"
    CALENDAR = "calendar"


async def start_cache_cleanup_task(interval: int = 60):
    """Background task to cleanup expired cache entries"""
    cache = get_cache()
    
    while True:
        await asyncio.sleep(interval)
        cleaned = await cache.cleanup_expired()
        if cleaned > 0:
            logger.debug(f"Cache cleanup: removed {cleaned} expired entries")
