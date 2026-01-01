"""A2A Protocol support for Unibase Agent Framework."""

# Unibase A2A extensions
from .types import StreamResponse, A2AErrorCode

# Unibase A2A server
from .server import A2AServer, create_simple_handler, create_async_handler

# Unibase A2A client
from .client import A2AClient, AgentDiscoveryError, TaskExecutionError

# Agent card generator utility
from .agent_card import generate_agent_card, agent_card_from_metadata

__all__ = [
    # Unibase extensions
    "StreamResponse",
    "A2AErrorCode",
    # Server
    "A2AServer",
    "create_simple_handler",
    "create_async_handler",
    # Client
    "A2AClient",
    "AgentDiscoveryError",
    "TaskExecutionError",
    # Utilities
    "generate_agent_card",
    "agent_card_from_metadata",
]
