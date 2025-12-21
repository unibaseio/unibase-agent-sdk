"""Base class for transparent memory middlewares."""
from abc import ABC, abstractmethod
from typing import Any
from ...core.proxy_utils import TransparentProxy


class TransparentMemoryMiddleware(TransparentProxy, ABC):
    """
    Transparent memory middleware proxy.

    Design principle: Users can use it exactly like the native SDK.

    Example:
        # Initialize
        mem0 = Mem0Middleware(agent_id="agent_123")
        await mem0.initialize()

        # Use native API (completely transparent!)
        mem0.add("User likes Python", user_id="agent_123")
        results = mem0.search("Python", user_id="agent_123")
        all_memories = mem0.get_all(user_id="agent_123")
    """

    # Protected attributes list (not forwarded to native SDK)
    _protected_attrs = {
        'agent_id', 'config', 'initialize', '_middleware_instance',
        '_initialize_middleware', 'get_middleware_name',
        'get_native_instance', '_get_proxied_instance', '_before_call', '_after_call',
        '_protected_attrs', '_wrap_method'
    }

    def __init__(self, agent_id: str, **config):
        self.agent_id = agent_id
        self.config = config
        self._middleware_instance = None

    @abstractmethod
    async def _initialize_middleware(self) -> Any:
        """
        Subclass implementation: Initialize native middleware.

        Returns:
            Native middleware instance
        """
        pass

    async def initialize(self) -> None:
        """Initialize the middleware."""
        self._middleware_instance = await self._initialize_middleware()

    def get_native_instance(self) -> Any:
        """Get the native middleware instance."""
        if self._middleware_instance is None:
            raise RuntimeError("Middleware not initialized. Call initialize() first.")
        return self._middleware_instance

    def _get_proxied_instance(self) -> Any:
        """
        Implements the method required by TransparentProxy.

        Returns:
            The proxied middleware instance
        """
        if self._middleware_instance is None:
            raise RuntimeError(
                f"Middleware not initialized. Call 'await {type(self).__name__}.initialize()' first."
            )
        return self._middleware_instance

    def get_middleware_name(self) -> str:
        """Get the middleware name."""
        return self.__class__.__name__


# Alias for backward compatibility
BaseMemoryMiddleware = TransparentMemoryMiddleware
