"""Registry module - Thin wrapper around AIP SDK for agent management.

This module provides:
- AgentRegistry: Main interface wrapping AIP SDK AsyncAIPClient

The registry acts as a thin wrapper around the AIP SDK client, providing:
- Local agent instance tracking
- A2A protocol support

Identity and wallet management are handled by the Unibase AIP SDK.
"""

from .registry import AgentRegistry

__all__ = [
    "AgentRegistry",
]
