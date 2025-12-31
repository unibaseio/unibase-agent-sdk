"""
Shared Proxy Utilities

Consolidates duplicate async/sync detection and method wrapping logic
that was previously duplicated across TransparentAgentProxy and
TransparentMemoryMiddleware.

This module provides:
- ProxyMethodWrapper: Handles async/sync method detection and wrapping
- TransparentProxy: Base class for all transparent proxy patterns
- Hook support for before/after method calls
"""
from typing import Any, Callable, Optional
import asyncio
import inspect
from ..utils.logger import get_logger

logger = get_logger("core.proxy_utils")


class ProxyMethodWrapper:
    """
    Wraps a method to handle both sync and async calls transparently.

    Supports optional before/after hooks for logging, recording, etc.
    """

    def __init__(
        self,
        method_name: str,
        method: Callable,
        before_hook: Optional[Callable] = None,
        after_hook: Optional[Callable] = None
    ):
        """
        Initialize method wrapper.

        Args:
            method_name: Name of the method being wrapped
            method: The original method to wrap
            before_hook: Optional callable to run before method execution
            after_hook: Optional callable to run after method execution
                       Signature: async def hook(method_name, args, kwargs, result)
        """
        self.method_name = method_name
        self.method = method
        self.before_hook = before_hook
        self.after_hook = after_hook
        self.is_async = inspect.iscoroutinefunction(method) or asyncio.iscoroutinefunction(method)

    def __call__(self, *args, **kwargs):
        """Execute the wrapped method."""
        if self.is_async:
            return self._async_call(*args, **kwargs)
        else:
            return self._sync_call(*args, **kwargs)

    async def _async_call(self, *args, **kwargs):
        """Handle async method calls."""
        # Before hook
        if self.before_hook:
            if asyncio.iscoroutinefunction(self.before_hook):
                await self.before_hook(self.method_name, args, kwargs)
            else:
                self.before_hook(self.method_name, args, kwargs)

        # Execute method
        result = await self.method(*args, **kwargs)

        # After hook
        if self.after_hook:
            if asyncio.iscoroutinefunction(self.after_hook):
                await self.after_hook(self.method_name, args, kwargs, result)
            else:
                # Schedule async hook in background for sync context
                asyncio.create_task(
                    self.after_hook(self.method_name, args, kwargs, result)
                )

        return result

    def _sync_call(self, *args, **kwargs):
        """Handle sync method calls."""
        # Before hook
        if self.before_hook:
            if asyncio.iscoroutinefunction(self.before_hook):
                # Can't await in sync context, skip or log warning
                logger.debug(f"Skipping async before_hook for sync method {self.method_name}")
            else:
                self.before_hook(self.method_name, args, kwargs)

        # Execute method
        result = self.method(*args, **kwargs)

        # Check if result is a coroutine (method returned async result)
        if asyncio.iscoroutine(result):
            # Create task to handle it
            return asyncio.create_task(result)

        # After hook
        if self.after_hook:
            if asyncio.iscoroutinefunction(self.after_hook):
                # Schedule async hook in background
                try:
                    asyncio.create_task(
                        self.after_hook(self.method_name, args, kwargs, result)
                    )
                except RuntimeError:
                    # No event loop running, skip
                    logger.debug(f"No event loop for after_hook on {self.method_name}")
            else:
                self.after_hook(self.method_name, args, kwargs, result)

        return result


class TransparentProxy:
    """
    Base class for transparent proxy pattern.

    Automatically forwards attribute access to a proxied instance while
    allowing custom behavior through hooks.

    Subclasses should:
    1. Implement _get_proxied_instance() to return the proxied object
    2. Optionally override _before_call() and _after_call() for hooks
    3. Add class attributes to _protected_attrs set to prevent forwarding
    """

    # Attributes that should not be forwarded to the proxied instance
    _protected_attrs = {
        '_get_proxied_instance', '_wrap_method', '_before_call', '_after_call',
        '_protected_attrs'
    }

    def _get_proxied_instance(self) -> Any:
        """
        Get the instance being proxied.

        Subclasses must implement this to return the object to proxy.

        Returns:
            The proxied instance

        Raises:
            RuntimeError: If the proxied instance is not available
        """
        raise NotImplementedError("Subclass must implement _get_proxied_instance()")

    def __getattr__(self, name: str) -> Any:
        """
        Forward attribute access to the proxied instance.

        This is the core of the transparent proxy pattern.
        """
        # Prevent forwarding of protected attributes
        if name in self._protected_attrs or name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

        # Get proxied instance
        try:
            proxied = self._get_proxied_instance()
        except Exception as e:
            raise RuntimeError(
                f"Cannot access '{name}': {str(e)}"
            )

        # Get attribute from proxied instance
        attr = getattr(proxied, name)

        # Wrap callable attributes
        if callable(attr):
            return self._wrap_method(name, attr)

        return attr

    def _wrap_method(self, method_name: str, method: Callable) -> Callable:
        """
        Wrap a method from the proxied instance.

        Args:
            method_name: Name of the method
            method: The method to wrap

        Returns:
            Wrapped method with hooks
        """
        return ProxyMethodWrapper(
            method_name,
            method,
            before_hook=self._before_call,
            after_hook=self._after_call
        )

    def _before_call(self, method_name: str, args: tuple, kwargs: dict):
        """
        Hook called before method execution.

        Override in subclass to add custom behavior.
        Can be sync or async.
        """
        pass

    async def _after_call(self, method_name: str, args: tuple, kwargs: dict, result: Any):
        """
        Hook called after method execution.

        Override in subclass to add custom behavior.
        Should be async to handle async methods.
        """
        pass
