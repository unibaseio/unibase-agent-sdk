from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, TYPE_CHECKING
from .types import AgentIdentity
from .proxy_utils import TransparentProxy
from ..memory.manager import MemoryManager

if TYPE_CHECKING:
    from ..agent.registry import AgentRegistry


class TransparentAgentProxy(TransparentProxy, ABC):
    """
    Transparent Agent Proxy - Integrated with Registry.

    Inherits from TransparentProxy to reuse async/sync detection and method wrapping.
    """

    # Protected attributes that should not be forwarded
    _protected_attrs = {
        'identity', 'registry', 'memory_manager', 'agent_id',
        '_sdk_instance', '_auto_record', 'initialize', '_initialize_sdk',
        '_auto_record_interaction', '_get_proxied_instance', '_before_call', '_after_call',
        'send_to_agent', 'get_other_agent', 'list_all_agents', 'update_metadata',
        'attach_memory', 'disable_auto_record', 'enable_auto_record',
        '_protected_attrs', '_wrap_method'
    }
    
    def __init__(
        self,
        identity: AgentIdentity,
        registry: 'AgentRegistry',
        memory_manager: Optional[MemoryManager] = None
    ):
        self.identity = identity
        self.registry = registry  # Reference to Registry
        self.memory_manager = memory_manager
        self._sdk_instance = None
        self._auto_record = True
        
        # Automatically register to Registry
        self.registry.register_agent_instance(self)
    
    @property
    def agent_id(self) -> str:
        """Shortcut to access agent_id."""
        return self.identity.agent_id
    
    @abstractmethod
    async def _initialize_sdk(self, **config):
        """Subclass implementation: Initialize native SDK instance."""
        pass
    
    async def initialize(self, **config):
        """Initialize the SDK."""
        self._sdk_instance = await self._initialize_sdk(**config)

    def _get_proxied_instance(self) -> Any:
        """
        Implements the method required by TransparentProxy.

        Returns:
            The proxied SDK instance
        """
        if self._sdk_instance is None:
            raise RuntimeError(
                f"SDK not initialized. Call 'await {type(self).__name__}.initialize()' first."
            )
        return self._sdk_instance

    async def _after_call(self, method_name: str, args: tuple, kwargs: dict, result: Any):
        """
        Hook called after method execution.

        Used for auto-recording interactions to memory.
        """
        if self._auto_record and self.memory_manager:
            await self._auto_record_interaction(method_name, args, kwargs, result)

    async def _auto_record_interaction(
        self,
        method_name: str,
        args: tuple,
        kwargs: dict,
        result: Any
    ):
        """Automatically record interactions (subclass can override)."""
        pass
    
    # ============ Registry Integration Methods ============
    
    async def send_to_agent(
        self,
        to_agent_id: str,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a message to another agent.
        
        Args:
            to_agent_id: Target agent ID
            message: Message content
        
        Returns:
            Response message
        """
        return await self.registry.send_message_to_agent(
            from_agent_id=self.agent_id,
            to_agent_id=to_agent_id,
            message=message
        )
    
    async def get_other_agent(
        self,
        agent_id: str
    ) -> Optional['TransparentAgentProxy']:
        """Get another agent instance."""
        return await self.registry.get_agent(agent_id)
    
    async def list_all_agents(self) -> List[AgentIdentity]:
        """List all available agents."""
        return await self.registry.list_agents(include_remote=True)
    
    async def update_metadata(self, metadata: Dict[str, Any]):
        """Update own metadata."""
        await self.registry.update_agent_metadata(self.agent_id, metadata)
    
    def attach_memory(self, memory_manager: MemoryManager):
        """Attach a memory manager."""
        self.memory_manager = memory_manager
    
    def disable_auto_record(self):
        """Disable automatic recording."""
        self._auto_record = False
    
    def enable_auto_record(self):
        """Enable automatic recording."""
        self._auto_record = True
