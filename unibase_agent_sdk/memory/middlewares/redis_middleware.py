"""
Redis Transparent Memory Middleware

Usage:
    # Initialize
    redis_mem = RedisMiddleware(
        agent_id="my-agent",
        redis_url="redis://localhost:6379"
    )
    await redis_mem.initialize()
    
    # Use native Redis API directly!
    # Basic operations
    redis_mem.set("key", "value")
    value = redis_mem.get("key")
    
    # Hash operations (great for structured memory)
    redis_mem.hset("user:123", mapping={"name": "Alice", "preference": "dark_mode"})
    user = redis_mem.hgetall("user:123")
    
    # List operations (for conversation history)
    redis_mem.lpush("chat:session1", "message1", "message2")
    messages = redis_mem.lrange("chat:session1", 0, -1)
    
    # JSON operations (if RedisJSON is available)
    redis_mem.json().set("memory:1", "$", {"text": "User likes Python", "category": "preference"})
    memory = redis_mem.json().get("memory:1")
    
    # Vector search (if RediSearch is available)
    # redis_mem.ft("idx:memories").search(query)
    
    All native Redis APIs are available!
"""
from typing import Any
from .base import TransparentMemoryMiddleware
from ...core.exceptions import MiddlewareNotAvailableError
import os

# Try to import Redis
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class RedisMiddleware(TransparentMemoryMiddleware):
    """
    Redis transparent adapter

    You can use it just like a native Redis client:
    - set(key, value, ex, px, nx, xx)
    - get(key)
    - delete(*keys)
    - hset(name, key, value, mapping)
    - hget(name, key)
    - hgetall(name)
    - lpush(name, *values)
    - rpush(name, *values)
    - lrange(name, start, end)
    - zadd(name, mapping)
    - zrange(name, start, end)
    - json().set/get (if RedisJSON)
    - ft().search (if RediSearch)

    All native Redis APIs remain available.
    """
    
    async def _initialize_middleware(self) -> Any:
        """Initialize the Redis client"""
        if not HAS_REDIS:
            raise MiddlewareNotAvailableError("redis", "pip install redis")
        
        redis_url = self.config.get("redis_url") or os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # Create Redis client
        client = redis.from_url(
            redis_url,
            decode_responses=self.config.get("decode_responses", True),
            **self.config.get("extra_params", {})
        )
        
        # Test connection
        client.ping()

        return client
