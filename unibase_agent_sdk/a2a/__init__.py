"""A2A Protocol support for Unibase Agent Framework."""

from .types import (
    TaskState,
    TaskStatus,
    Task,
    Message,
    Role,
    Part,
    TextPart,
    FilePart,
    DataPart,
    Artifact,
    Skill,
    AgentCard,
    Capability,
    PushNotificationConfig,
    StreamResponse,
)
from .server import A2AServer
from .client import A2AClient
from .agent_card import generate_agent_card

__all__ = [
    # Types
    "TaskState",
    "TaskStatus",
    "Task",
    "Message",
    "Role",
    "Part",
    "TextPart",
    "FilePart",
    "DataPart",
    "Artifact",
    "Skill",
    "AgentCard",
    "Capability",
    "PushNotificationConfig",
    "StreamResponse",
    # Server/Client
    "A2AServer",
    "A2AClient",
    "generate_agent_card",
]
