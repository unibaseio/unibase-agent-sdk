"""OpenAI transparent adapter."""
from typing import Any, Optional, TYPE_CHECKING
from ..core.base_agent import TransparentAgentProxy
from ..core.types import AgentIdentity, MemoryRecord
from ..core.exceptions import InitializationError
from ..utils.logger import get_logger
import time

logger = get_logger("adapters.openai")

if TYPE_CHECKING:
    from ..registry.registry import AgentRegistryClient
    from ..memory.manager import MemoryManager

# Try to import OpenAI
try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class OpenAIAdapter(TransparentAgentProxy):
    """Transparent OpenAI adapter integrated with the agent registry."""
    
    def __init__(
        self,
        identity: AgentIdentity,
        registry: 'AgentRegistryClient',
        memory_manager: Optional['MemoryManager'] = None
    ):
        super().__init__(identity, registry, memory_manager)
    
    async def _initialize_sdk(self, **config):
        """Initialize the native OpenAI SDK client."""
        if not HAS_OPENAI:
            raise InitializationError(
                "OpenAI SDK not available. Install with: pip install openai"
            )
        
        return AsyncOpenAI(
            api_key=config.get("api_key"),
            base_url=config.get("base_url"),
            timeout=config.get("timeout", 600.0)
        )
    
    async def _auto_record_interaction(
        self,
        method_name: str,
        args: tuple,
        kwargs: dict,
        result: Any
    ):
        """Automatically record OpenAI interactions for memory storage."""
        if "create" in method_name:
            try:
                messages = kwargs.get("messages", [])
                
                # Extract the first response choice for logging
                response_text = ""
                if hasattr(result, 'choices') and result.choices:
                    response_text = result.choices[0].message.content
                
                record = MemoryRecord(
                    session_id=kwargs.get("session_id", "default"),
                    agent_id=self.identity.agent_id,
                    content={
                        "messages": messages,
                        "response": response_text,
                        "model": kwargs.get("model", "unknown"),
                        "source": "openai"
                    },
                    timestamp=time.time(),
                    metadata={
                        "method": method_name,
                        "agent_type": "openai"
                    }
                )
                
                if self.memory_manager:
                    await self.memory_manager.save(record)

            except Exception as e:
                logger.warning("Auto-record failed", exc_info=True)
