"""
MemGPT Transparent Memory Middleware

Usage:
    # Initialize
    memgpt = MemGPTMiddleware(agent_id="my-agent", base_url="http://localhost:8283")
    await memgpt.initialize()
    
    # Use native MemGPT client API directly!
    # Create agent
    agent = memgpt.create_agent(name="assistant", ...)
    
    # Send messages
    response = memgpt.send_message(agent_id="xxx", message="Hello!")
    
    # Memory operations
    memgpt.insert_archival_memory(agent_id="xxx", memory="Important fact...")
    memories = memgpt.get_archival_memory(agent_id="xxx")
    
    # Get messages
    messages = memgpt.get_messages(agent_id="xxx")
    
    All native MemGPT client APIs are available!
"""
from typing import Any
from .base import TransparentMemoryMiddleware
from ...core.exceptions import MiddlewareNotAvailableError


# Try to import MemGPT
try:
    from memgpt import create_client
    HAS_MEMGPT = True
except ImportError:
    HAS_MEMGPT = False


class MemGPTMiddleware(TransparentMemoryMiddleware):
    """
    MemGPT transparent adapter

    You can use it just like the native MemGPT client:
    - create_agent(name, ...)
    - send_message(agent_id, message, role)
    - get_messages(agent_id)
    - insert_archival_memory(agent_id, memory)
    - get_archival_memory(agent_id)
    - search_archival_memory(agent_id, query)
    - delete_agent(agent_id)

    All native MemGPT APIs remain available.
    """
    
    async def _initialize_middleware(self) -> Any:
        """Initialize the MemGPT client"""
        if not HAS_MEMGPT:
            raise MiddlewareNotAvailableError("memgpt", "pip install pymemgpt")
        
        return create_client(
            base_url=self.config.get("base_url", "http://localhost:8283"),
            token=self.config.get("token")
        )
    
