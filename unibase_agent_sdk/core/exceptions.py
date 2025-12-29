"""Custom exceptions for Unibase Agent SDK.

This module defines a hierarchical exception structure for better error handling.
Common exceptions are imported from aip_sdk for consistency across SDKs.
Agent-SDK-specific exceptions are defined here.
"""

# Import common exceptions from aip_sdk for consistency
from aip_sdk.exceptions import (
    AIPError,
    AuthenticationError as AIPAuthenticationError,
    RegistrationError as AIPRegistrationError,
    ValidationError,
    AgentNotFoundError as AIPAgentNotFoundError,
)


class UnibaseError(AIPError):
    """Base exception for all Unibase Agent SDK errors.

    Extends AIPError for consistency with the platform SDK.
    All custom exceptions in the agent SDK should inherit from this class.
    """

    def __init__(self, message: str, code: str = None, **kwargs):
        super().__init__(message, code=code, **kwargs)


class InitializationError(UnibaseError):
    """Raised when component initialization fails.

    This includes SDK initialization, middleware setup, or agent registration failures.
    """

    def __init__(self, message: str = "Initialization failed", code: str = "INIT_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)


class ConfigurationError(UnibaseError):
    """Raised when configuration is invalid or incomplete.

    This includes missing required parameters, invalid values, or conflicting settings.
    """

    def __init__(self, message: str = "Configuration error", code: str = "CONFIG_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)


class RegistryError(UnibaseError):
    """Raised for registry-related errors.

    This includes agent registration failures, identity management issues,
    or communication with the AIP endpoint.
    """

    def __init__(self, message: str = "Registry error", code: str = "REGISTRY_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)


class AgentNotFoundError(RegistryError):
    """Raised when an agent cannot be found in the registry.

    Args:
        agent_id: The ID of the agent that was not found
    """

    def __init__(self, agent_id: str, **kwargs):
        self.agent_id = agent_id
        super().__init__(f"Agent not found: {agent_id}", code="AGENT_NOT_FOUND", **kwargs)
        self.details["agent_id"] = agent_id


class MemoryError(UnibaseError):
    """Raised for memory operation errors.

    This includes failures in memory storage, retrieval, or synchronization.
    """

    def __init__(self, message: str = "Memory operation failed", code: str = "MEMORY_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)


class MiddlewareError(MemoryError):
    """Raised for middleware-specific errors.

    This includes middleware initialization failures or operational issues.
    """

    def __init__(self, message: str = "Middleware error", code: str = "MIDDLEWARE_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)


class MiddlewareNotAvailableError(MiddlewareError):
    """Raised when optional middleware dependency is missing.

    Args:
        middleware: Name of the middleware
        install_cmd: Command to install the missing dependency

    Example:
        >>> raise MiddlewareNotAvailableError("mem0", "pip install mem0ai")
    """

    def __init__(self, middleware: str, install_cmd: str, **kwargs):
        self.middleware = middleware
        self.install_cmd = install_cmd
        message = f"{middleware} is not available. Install with: {install_cmd}"
        super().__init__(message, code="MIDDLEWARE_NOT_AVAILABLE", **kwargs)
        self.details["middleware"] = middleware
        self.details["install_cmd"] = install_cmd


class A2AProtocolError(UnibaseError):
    """Raised for A2A protocol errors.

    This includes JSON-RPC errors, task management issues, or agent discovery failures.
    """

    def __init__(self, message: str = "A2A protocol error", code: str = "A2A_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)


class AgentDiscoveryError(A2AProtocolError):
    """Raised when agent discovery fails.

    This includes network errors, invalid agent cards, or unavailable endpoints.
    """

    def __init__(self, message: str = "Agent discovery failed", code: str = "DISCOVERY_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)


class TaskExecutionError(A2AProtocolError):
    """Raised when A2A task execution fails.

    This includes task creation, status updates, or message delivery failures.
    """

    def __init__(self, message: str = "Task execution failed", code: str = "TASK_EXEC_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)


class AuthenticationError(UnibaseError):
    """Raised for authentication and authorization errors.

    This includes invalid tokens, signature verification failures, or expired credentials.
    """

    def __init__(self, message: str = "Authentication failed", code: str = "AUTH_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)


class WalletError(UnibaseError):
    """Raised for Web3 wallet-related errors.

    This includes wallet creation failures, signing errors, or blockchain communication issues.
    """

    def __init__(self, message: str = "Wallet error", code: str = "WALLET_ERROR", **kwargs):
        super().__init__(message, code=code, **kwargs)


# Re-export common exceptions for convenience
__all__ = [
    # Base errors
    "AIPError",
    "UnibaseError",
    # Initialization and config
    "InitializationError",
    "ConfigurationError",
    # Registry
    "RegistryError",
    "AgentNotFoundError",
    # Memory
    "MemoryError",
    "MiddlewareError",
    "MiddlewareNotAvailableError",
    # A2A Protocol
    "A2AProtocolError",
    "AgentDiscoveryError",
    "TaskExecutionError",
    # Auth
    "AuthenticationError",
    # Wallet
    "WalletError",
    # Validation
    "ValidationError",
]
