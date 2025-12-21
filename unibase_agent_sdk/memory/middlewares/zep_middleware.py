"""
Zep Transparent Memory Middleware

Usage:
    # Initialize
    zep = ZepMiddleware(agent_id="my-agent", base_url="http://localhost:8000")
    await zep.initialize()
    
    # Use native Zep API directly!
    # Memory operations
    zep.memory.add(session_id="session_123", messages=[...])
    memory = zep.memory.get(session_id="session_123")
    zep.memory.search(session_id="session_123", text="query", limit=10)
    
    # User operations
    zep.user.add(user_id="user_123", ...)
    user = zep.user.get(user_id="user_123")
    
    All native Zep client APIs are available!
"""
from typing import Any
from .base import TransparentMemoryMiddleware
from ...core.exceptions import MiddlewareNotAvailableError

# Try to import Zep
try:
    from zep_python.client import Zep
    from zep_python import Message
    HAS_ZEP = True
except ImportError:
    HAS_ZEP = False


class ZepMiddleware(TransparentMemoryMiddleware):
    """
    Zep transparent adapter

    You can use it just like the native Zep client:
    - memory.add(session_id, messages)
    - memory.get(session_id)
    - memory.search(session_id, text, limit)
    - memory.delete(session_id)
    - user.add(user_id, ...)
    - user.get(user_id)
    - user.delete(user_id)

    All native Zep APIs remain available.
    """
    
    async def _initialize_middleware(self) -> Any:
        """Initialize the Zep client"""
        if not HAS_ZEP:
            raise MiddlewareNotAvailableError("zep", "pip install zep-python")
        
        base_url = self.config.get("base_url", "http://localhost:8000")
        api_key = self.config.get("api_key")
        
        if api_key:
            return Zep(base_url=base_url, api_key=api_key)
        else:
            # Self-hosted mode without API key
            return Zep(base_url=base_url, api_key="")
