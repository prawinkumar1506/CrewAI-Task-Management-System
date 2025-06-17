import redis
import json
import pickle
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
from functools import wraps
import hashlib

class CacheManager:
    def __init__(self, redis_url: str = "redis://localhost:6379", default_ttl: int = 300):
        """Initialize cache manager with Redis backend"""
        try:
            self.redis_client = redis.from_url(redis_url)
            self.default_ttl = default_ttl
            self.cache_hits = 0
            self.cache_misses = 0
        except Exception as e:
            print(f"Warning: Redis not available, using in-memory cache: {e}")
            self.redis_client = None
            self.memory_cache = {}
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    self.cache_hits += 1
                    return pickle.loads(value)
            else:
                if key in self.memory_cache:
                    data = self.memory_cache[key]
                    if data['expires_at'] > datetime.now():
                        self.cache_hits += 1
                        return data['value']
                    else:
                        del self.memory_cache[key]
            self.cache_misses += 1
            return None
        except Exception:
            self.cache_misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        try:
            ttl = ttl or self.default_ttl
            if self.redis_client:
                return self.redis_client.setex(key, ttl, pickle.dumps(value))
            else:
                self.memory_cache[key] = {
                    'value': value,
                    'expires_at': datetime.now() + timedelta(seconds=ttl)
                }
                return True
        except Exception:
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
            else:
                # Simple pattern matching for memory cache
                keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                return len(keys_to_delete)
        except Exception:
            return 0
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'hit_rate': self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        }

def cache_result(prefix: str, ttl: int = 300):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = CacheManager()
            cache_key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

# Global cache instance
cache_manager = CacheManager() 