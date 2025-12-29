# Unibase Agent Framework
"""
Unibase Agent Framework - A transparent SDK for building AI agents
with integrated memory management and multi-SDK support.

Structure:
- wrappers/: Generic wrappers to expose ANY agent as A2A service
- adapters/: Transparent LLM providers (Claude, OpenAI, LangChain)
- agents/: Framework-specific wrappers (CrewAI, AutoGen, Phidata, LlamaIndex)
- registry/: Agent registration, identity, auth, and wallet management
- memory/middlewares/: Transparent memory backends (mem0, ChromaDB, Redis, etc.)
- a2a/: A2A Protocol server and types

Quick Start:
    # Expose any function as an A2A agent
    from unibase_agent_sdk import expose_as_a2a

    def my_handler(text: str) -> str:
        return f"Processed: {text}"

    server = expose_as_a2a("MyAgent", my_handler, port=8100)
    await server.run()
"""

__version__ = "0.1.0"
__author__ = "Unibase Team"

# Core types
from unibase_agent_sdk.core.types import (
    AgentType,
    AgentIdentity,
    MemoryRecord,
    DAUploadResult,
)

# Canonical A2A Protocol types (use these for tasks, skills, messages)
from unibase_agent_sdk.a2a.types import (
    Task,
    TaskState,
    TaskStatus,
    Message,
    Skill,
    AgentCard,
    Artifact,
)

# Base classes
from unibase_agent_sdk.core.base_agent import TransparentAgentProxy
from unibase_agent_sdk.core.base_memory import BaseMemory

# Agent management
from unibase_agent_sdk.registry.registry import AgentRegistryClient, RegistrationMode

# Memory management
from unibase_agent_sdk.memory.manager import MemoryManager
from unibase_agent_sdk.memory.membase_client import MembaseClient
from unibase_agent_sdk.memory.da_uploader import DAUploader

# LLM Provider Adapters (transparent access to native SDKs)
from unibase_agent_sdk.adapters.claude_adapter import ClaudeAdapter
from unibase_agent_sdk.adapters.langchain_adapter import LangChainAdapter
from unibase_agent_sdk.adapters.openai_adapter import OpenAIAdapter

# Generic Wrappers (wrap ANY agent as A2A service)
from unibase_agent_sdk.wrappers import expose_as_a2a, wrap_agent, AgentWrapper

# A2A Server
from unibase_agent_sdk.a2a.server import A2AServer

# Agent Framework Wrappers (wrapped Agent classes from each framework)
# Import from unibase_agent_sdk.agents instead
# from unibase_agent_sdk.agents import CrewAIAgent, AutoGenAssistant, PhiAgent, LlamaAgent

__all__ = [
    # Version
    "__version__",
    # Core Types
    "AgentType",
    "AgentIdentity",
    "MemoryRecord",
    "DAUploadResult",
    # A2A Protocol Types (canonical for tasks, skills, messages)
    "Task",
    "TaskState",
    "TaskStatus",
    "Message",
    "Skill",
    "AgentCard",
    "Artifact",
    # Base classes
    "TransparentAgentProxy",
    "BaseMemory",
    # Agent management
    "AgentRegistryClient",
    "RegistrationMode",
    # Memory management
    "MemoryManager",
    "MembaseClient",
    "DAUploader",
    # LLM Provider Adapters
    "ClaudeAdapter",
    "LangChainAdapter",
    "OpenAIAdapter",
    # Generic Wrappers (expose ANY agent as A2A)
    "expose_as_a2a",
    "wrap_agent",
    "AgentWrapper",
    # A2A Server
    "A2AServer",
]
