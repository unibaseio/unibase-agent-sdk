"""mem0 transparent middleware that exposes the native Memory API."""
from typing import Any
from .base import TransparentMemoryMiddleware
from ...core.exceptions import MiddlewareNotAvailableError

# Try to import mem0
try:
    from mem0 import Memory
    HAS_MEM0 = True
except ImportError:
    HAS_MEM0 = False


class Mem0Middleware(TransparentMemoryMiddleware):
    """Transparent mem0 adapter that preserves the native Memory API."""
    
    async def _initialize_middleware(self) -> Any:
        """Initialize the mem0 Memory instance."""
        if not HAS_MEM0:
            raise MiddlewareNotAvailableError("mem0", "pip install mem0ai")
        
        # Check for custom vector store config
        vector_provider = self.config.get("vector_provider")
        
        if vector_provider:
            # Use custom vector store
            config = {
                "vector_store": {
                    "provider": vector_provider,
                    "config": self.config.get("vector_config", {})
                }
            }
            return Memory.from_config(config)
        else:
            # Use default in-memory storage
            return Memory()
