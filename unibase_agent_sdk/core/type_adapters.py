"""Type adapters for converting between AIP SDK types and A2A Protocol types.

This module provides bidirectional conversion between:
- AIP SDK types (from aip.sdk.types)
- A2A Protocol types (from unibase_agent_sdk.a2a.types)

The A2A protocol types are the canonical representation for this framework.
AIP SDK types are converted to/from A2A types when communicating with the AIP platform.
"""

from typing import Dict, Any, List, Optional
from enum import Enum

# Import A2A types (canonical)
from ..a2a.types import (
    Task as A2ATask,
    TaskState as A2ATaskState,
    TaskStatus as A2ATaskStatus,
    Skill as A2ASkill,
    Message,
)

# Import AIP SDK types (for platform communication)
try:
    from aip.sdk.types import (
        Task as AIPTask,
        TaskStatus as AIPTaskStatus,
        SkillConfig as AIPSkillConfig,
        AgentConfig as AIPAgentConfig,
    )
    AIP_SDK_AVAILABLE = True
except ImportError:
    AIP_SDK_AVAILABLE = False
    AIPTask = None
    AIPTaskStatus = None
    AIPSkillConfig = None
    AIPAgentConfig = None


# ============================================================
# Task Status Mapping
# ============================================================

class TaskStatusMapping:
    """Bidirectional mapping between AIP SDK TaskStatus and A2A TaskState."""

    # A2A -> AIP SDK mapping
    A2A_TO_AIP = {
        "submitted": "pending",
        "working": "running",
        "input-required": "pending",  # AIP doesn't have input-required
        "completed": "completed",
        "failed": "failed",
        "canceled": "cancelled",
    }

    # AIP SDK -> A2A mapping
    AIP_TO_A2A = {
        "pending": "submitted",
        "running": "working",
        "completed": "completed",
        "failed": "failed",
        "cancelled": "canceled",
    }

    @classmethod
    def a2a_to_aip(cls, a2a_state: str) -> str:
        """Convert A2A TaskState to AIP TaskStatus string."""
        return cls.A2A_TO_AIP.get(a2a_state, "pending")

    @classmethod
    def aip_to_a2a(cls, aip_status: str) -> str:
        """Convert AIP TaskStatus to A2A TaskState string."""
        return cls.AIP_TO_A2A.get(aip_status, "submitted")


# ============================================================
# Skill Conversion
# ============================================================

def a2a_skill_to_aip_config(skill: A2ASkill) -> Optional["AIPSkillConfig"]:
    """Convert A2A Skill to AIP SDK SkillConfig.

    Args:
        skill: A2A protocol Skill

    Returns:
        AIP SDK SkillConfig or None if AIP SDK not available
    """
    if not AIP_SDK_AVAILABLE or not AIPSkillConfig:
        return None

    # A2A skills don't have structured input/output definitions
    # We'll create a simple config based on the skill metadata
    return AIPSkillConfig(
        name=skill.name,
        description=skill.description,
        inputs=[],  # A2A uses flexible input_modes instead
        outputs=[]   # A2A uses flexible output_modes instead
    )


def aip_skill_config_to_a2a(skill_config: "AIPSkillConfig") -> A2ASkill:
    """Convert AIP SDK SkillConfig to A2A Skill.

    Args:
        skill_config: AIP SDK SkillConfig

    Returns:
        A2A protocol Skill
    """
    # Extract input/output types from structured definitions
    input_modes = ["application/json"] if skill_config.inputs else ["text/plain"]
    output_modes = ["application/json"] if skill_config.outputs else ["text/plain"]

    return A2ASkill(
        id=skill_config.name.lower().replace(" ", "_"),
        name=skill_config.name,
        description=skill_config.description,
        tags=[],
        examples=[],
        input_modes=input_modes,
        output_modes=output_modes
    )


def aip_agent_config_skills_to_a2a(agent_config: "AIPAgentConfig") -> List[A2ASkill]:
    """Convert all skills from AIP AgentConfig to A2A Skills.

    Args:
        agent_config: AIP SDK AgentConfig

    Returns:
        List of A2A Skills
    """
    if not agent_config.skills:
        return []

    return [aip_skill_config_to_a2a(skill) for skill in agent_config.skills]


# ============================================================
# Task Conversion
# ============================================================

def a2a_task_to_aip_task(task: A2ATask) -> Optional["AIPTask"]:
    """Convert A2A Task to AIP SDK Task.

    Args:
        task: A2A protocol Task

    Returns:
        AIP SDK Task or None if AIP SDK not available
    """
    if not AIP_SDK_AVAILABLE or not AIPTask:
        return None

    # Extract task description from history
    description = ""
    payload = {}

    if task.history:
        first_message = task.history[0]
        if first_message.parts:
            # Get text from first part
            first_part = first_message.parts[0]
            if hasattr(first_part, 'text'):
                description = first_part.text
            elif hasattr(first_part, 'data'):
                payload = first_part.data

    return AIPTask(
        task_id=task.id,
        name=task.metadata.get("name", "task") if task.metadata else "task",
        description=description,
        payload=payload,
        assigned_agent=task.metadata.get("assigned_agent") if task.metadata else None
    )


def aip_task_to_a2a_task(task: "AIPTask") -> A2ATask:
    """Convert AIP SDK Task to A2A Task.

    Args:
        task: AIP SDK Task

    Returns:
        A2A protocol Task
    """
    # Create initial message from task description
    message = Message.user(task.description)

    # Determine initial state
    state = A2ATaskState.SUBMITTED

    return A2ATask(
        id=task.task_id,
        status=A2ATaskStatus(state=state),
        history=[message],
        metadata={
            "name": task.name,
            "assigned_agent": task.assigned_agent,
            "original_payload": task.payload
        }
    )


# ============================================================
# Metadata Conversion Helpers
# ============================================================

def extract_a2a_capabilities_from_aip_config(config: "AIPAgentConfig") -> List[str]:
    """Extract A2A-compatible capabilities from AIP AgentConfig.

    Args:
        config: AIP SDK AgentConfig

    Returns:
        List of capability strings
    """
    capabilities = []

    # Map AIP capabilities to A2A format
    if config.capabilities:
        capabilities.extend(config.capabilities)

    # Add implicit capabilities
    capabilities.append("streaming")  # Assume streaming support
    capabilities.append("stateTransitionHistory")  # Standard for A2A

    return capabilities


def merge_agent_metadata(
    aip_config: "AIPAgentConfig",
    additional_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Merge AIP AgentConfig with additional metadata.

    Args:
        aip_config: AIP SDK AgentConfig
        additional_metadata: Additional metadata to merge

    Returns:
        Merged metadata dictionary
    """
    metadata = {}

    # Add AIP-specific fields
    if aip_config.handle:
        metadata["handle"] = aip_config.handle
    if aip_config.endpoint_url:
        metadata["endpoint_url"] = aip_config.endpoint_url
    if aip_config.price:
        metadata["price"] = {
            "amount": aip_config.price,
            "currency": aip_config.price_currency
        }
    if aip_config.cost_model:
        metadata["cost_model"] = aip_config.cost_model.to_dict()

    # Merge existing metadata
    if aip_config.metadata:
        metadata.update(aip_config.metadata)

    # Merge additional metadata
    if additional_metadata:
        metadata.update(additional_metadata)

    return metadata


# ============================================================
# Validation Helpers
# ============================================================

def validate_task_state_transition(from_state: str, to_state: str) -> bool:
    """Validate that a task state transition is valid in A2A protocol.

    Args:
        from_state: Current state
        to_state: Target state

    Returns:
        True if transition is valid
    """
    valid_transitions = {
        "submitted": ["working", "failed", "canceled"],
        "working": ["input-required", "completed", "failed", "canceled"],
        "input-required": ["working", "failed", "canceled"],
        "completed": [],  # Terminal state
        "failed": [],      # Terminal state
        "canceled": []     # Terminal state
    }

    return to_state in valid_transitions.get(from_state, [])


def normalize_skill_id(name: str) -> str:
    """Normalize a skill name to a valid skill ID.

    Args:
        name: Skill name

    Returns:
        Normalized skill ID (lowercase, underscores)
    """
    return name.lower().replace(" ", "_").replace("-", "_")
