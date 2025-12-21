"""Custom exceptions for Unibase Framework.

This module defines a hierarchical exception structure for better error handling
and debugging across the framework.
"""


class UnibaseError(Exception):
    """Base exception for all Unibase framework errors.

    All custom exceptions in the framework should inherit from this class.
    """
    pass


class InitializationError(UnibaseError):
    """Raised when component initialization fails.

    This includes SDK initialization, middleware setup, or agent registration failures.
    """
    pass


class ConfigurationError(UnibaseError):
    """Raised when configuration is invalid or incomplete.

    This includes missing required parameters, invalid values, or conflicting settings.
    """
    pass


class RegistryError(UnibaseError):
    """Raised for registry-related errors.

    This includes agent registration failures, identity management issues,
    or communication with the AIP endpoint.
    """
    pass


class AgentNotFoundError(RegistryError):
    """Raised when an agent cannot be found in the registry.

    Args:
        agent_id: The ID of the agent that was not found
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent not found: {agent_id}")


class MemoryError(UnibaseError):
    """Raised for memory operation errors.

    This includes failures in memory storage, retrieval, or synchronization.
    """
    pass


class MiddlewareError(MemoryError):
    """Raised for middleware-specific errors.

    This includes middleware initialization failures or operational issues.
    """
    pass


class MiddlewareNotAvailableError(MiddlewareError):
    """Raised when optional middleware dependency is missing.

    Args:
        middleware: Name of the middleware
        install_cmd: Command to install the missing dependency

    Example:
        >>> raise MiddlewareNotAvailableError("mem0", "pip install mem0ai")
    """

    def __init__(self, middleware: str, install_cmd: str):
        self.middleware = middleware
        self.install_cmd = install_cmd
        super().__init__(
            f"{middleware} is not available. Install with: {install_cmd}"
        )


class A2AProtocolError(UnibaseError):
    """Raised for A2A protocol errors.

    This includes JSON-RPC errors, task management issues, or agent discovery failures.
    """
    pass


class AgentDiscoveryError(A2AProtocolError):
    """Raised when agent discovery fails.

    This includes network errors, invalid agent cards, or unavailable endpoints.
    """
    pass


class TaskExecutionError(A2AProtocolError):
    """Raised when A2A task execution fails.

    This includes task creation, status updates, or message delivery failures.
    """
    pass


class AuthenticationError(UnibaseError):
    """Raised for authentication and authorization errors.

    This includes invalid tokens, signature verification failures, or expired credentials.
    """
    pass


class WalletError(UnibaseError):
    """Raised for Web3 wallet-related errors.

    This includes wallet creation failures, signing errors, or blockchain communication issues.
    """
    pass
