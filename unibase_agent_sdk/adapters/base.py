# Adapter base class
from abc import abstractmethod
from typing import Any, Dict
from ..core.base_agent import TransparentAgentProxy
from ..core.types import AgentIdentity

class BaseAdapter(TransparentAgentProxy):
    """Base adapter that preserves access to the native SDK API."""
    
    def __init__(self, identity: AgentIdentity):
        super().__init__(identity)
    
    @abstractmethod
    async def _create_native_client(self, **config):
        """Create the native SDK client. Subclasses must implement this."""
        pass
    
    async def initialize(self, **config) -> None:
        """Initialize the adapter and create the native client."""
        self._native_client = await self._create_native_client(**config)
