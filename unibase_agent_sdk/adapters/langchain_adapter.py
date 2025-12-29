"""LangChain transparent adapter."""
from typing import Any, Optional, TYPE_CHECKING
from ..core.base_agent import TransparentAgentProxy
from ..core.types import AgentIdentity, MemoryRecord
from ..core.exceptions import InitializationError, ConfigurationError
from ..utils.logger import get_logger
import time

logger = get_logger("adapters.langchain")

if TYPE_CHECKING:
    from ..registry.registry import AgentRegistryClient
    from ..memory.manager import MemoryManager

# Try to import LangChain with OpenAI (primary) or Anthropic (fallback)
HAS_LANGCHAIN_OPENAI = False
HAS_LANGCHAIN_ANTHROPIC = False

try:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, AIMessage
    HAS_LANGCHAIN_OPENAI = True
except ImportError:
    pass

try:
    from langchain_anthropic import ChatAnthropic
    from langchain.schema import HumanMessage, AIMessage
    HAS_LANGCHAIN_ANTHROPIC = True
except ImportError:
    pass


class LangChainAdapter(TransparentAgentProxy):
    """
    LangChain transparent adapter - Integrated with Registry.
    Supports OpenAI and Anthropic models.
    """
    
    def __init__(
        self,
        identity: AgentIdentity,
        registry: 'AgentRegistryClient',
        memory_manager: Optional['MemoryManager'] = None,
        provider: str = "openai"  # "openai" or "anthropic"
    ):
        super().__init__(identity, registry, memory_manager)
        self.provider = provider
    
    async def _initialize_sdk(self, **config):
        """Initialize the native LangChain SDK."""
        provider = config.get("provider", self.provider)
        
        if provider == "openai":
            if not HAS_LANGCHAIN_OPENAI:
                raise InitializationError(
                    "LangChain OpenAI not available. Install with: pip install langchain-openai"
                )
            
            return ChatOpenAI(
                api_key=config.get("api_key"),
                model=config.get("model", "gpt-4o-mini"),
                **config.get("extra_params", {})
            )
        
        elif provider == "anthropic":
            if not HAS_LANGCHAIN_ANTHROPIC:
                raise InitializationError(
                    "LangChain Anthropic not available. Install with: pip install langchain-anthropic"
                )
            
            return ChatAnthropic(
                anthropic_api_key=config.get("api_key"),
                model=config.get("model", "claude-3-5-sonnet-20241022"),
                **config.get("extra_params", {})
            )
        else:
            raise ConfigurationError(f"Unknown provider: {provider}. Use 'openai' or 'anthropic'")
    
    async def _auto_record_interaction(
        self,
        method_name: str,
        args: tuple,
        kwargs: dict,
        result: Any
    ):
        """Automatically record LangChain interactions."""
        if method_name in ["invoke", "ainvoke", "stream", "astream"]:
            try:
                # Extract messages
                messages = args[0] if args else []
                
                record = MemoryRecord(
                    session_id=kwargs.get("session_id", "default"),
                    agent_id=self.identity.agent_id,
                    content={
                        "messages": [
                            m.content if hasattr(m, 'content') else str(m) 
                            for m in messages
                        ] if isinstance(messages, list) else str(messages),
                        "response": result.content if hasattr(result, 'content') else str(result),
                        "source": "langchain",
                        "provider": self.provider
                    },
                    timestamp=time.time(),
                    metadata={
                        "method": method_name,
                        "agent_type": "langchain",
                        "provider": self.provider
                    }
                )
                
                if self.memory_manager:
                    await self.memory_manager.save(record)
                
            except Exception as e:
                logger.warning("Auto-record failed", exc_info=True)
