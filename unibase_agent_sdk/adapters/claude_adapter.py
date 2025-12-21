from typing import Any, Optional, TYPE_CHECKING
from anthropic import AsyncAnthropic
from ..core.base_agent import TransparentAgentProxy
from ..core.types import AgentIdentity, MemoryRecord
from ..utils.logger import get_logger
import time

logger = get_logger("adapters.claude")

if TYPE_CHECKING:
    from ..agent.registry import AgentRegistry

class ClaudeAdapter(TransparentAgentProxy):
    """
    Claude transparent adapter - Integrated with Registry.
    """
    
    def __init__(
        self,
        identity: AgentIdentity,
        registry: 'AgentRegistry',
        memory_manager: Optional['MemoryManager'] = None
    ):
        super().__init__(identity, registry, memory_manager)
    
    async def _initialize_sdk(self, **config):
        """Initialize the native Claude SDK."""
        return AsyncAnthropic(
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
        """Automatically record Claude interactions."""
        if "create" in method_name or "stream" in method_name:
            try:
                messages = kwargs.get("messages", [])
                
                record = MemoryRecord(
                    session_id=kwargs.get("session_id", "default"),
                    agent_id=self.agent_id,
                    content={
                        "messages": messages,
                        "response": result.content[0].text if hasattr(result, 'content') else str(result),
                        "model": kwargs.get("model", "unknown"),
                        "source": "claude"
                    },
                    timestamp=time.time(),
                    metadata={
                        "method": method_name,
                        "agent_type": "claude"
                    }
                )
                
                await self.memory_manager.save(record)

            except Exception as e:
                logger.warning("Auto-record failed", exc_info=True)
