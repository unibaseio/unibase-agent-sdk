# Unibase Agent SDK
"""Unibase Agent SDK - Expose any agent as an A2A service."""

__version__ = "0.1.0"
__author__ = "Unibase Team"

# Core types
from unibase_agent_sdk.core.types import (
    AgentType,
    AgentIdentity,
)

# Generic Wrappers (wrap ANY agent as A2A service)
from unibase_agent_sdk.wrappers import expose_as_a2a, wrap_agent, AgentWrapper

# A2A Server and extensions
from unibase_agent_sdk.a2a import A2AServer, StreamResponse, A2AClient

# Registry (AIP platform integration)
from unibase_agent_sdk.registry import AgentRegistryClient as AgentRegistry, RegistrationMode

__all__ = [
    # Version
    "__version__",
    # Core Types
    "AgentType",
    "AgentIdentity",
    # Generic Wrappers (expose ANY agent as A2A)
    "expose_as_a2a",
    "wrap_agent",
    "AgentWrapper",
    # A2A Server and extensions
    "A2AServer",
    "StreamResponse",
    "A2AClient",
    # Registry (AIP platform integration)
    "AgentRegistry",
    "RegistrationMode",
]
