"""Tests for A2A Protocol Implementation.

Tests cover:
- A2A type serialization/deserialization
- Agent Card generation
- A2A server endpoints
- A2A client operations
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock

# Import A2A types
from unibase_agent_sdk.a2a.types import (
    TaskState,
    TaskStatus,
    Task,
    Message,
    Role,
    TextPart,
    FilePart,
    DataPart,
    Artifact,
    Skill,
    AgentCard,
    Capability,
    StreamResponse,
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    A2AErrorCode,
)

from unibase_agent_sdk.a2a.agent_card import generate_agent_card
from unibase_agent_sdk.a2a.client import A2AClient, AgentDiscoveryError
from unibase_agent_sdk.core.types import AgentIdentity, AgentType


class TestA2ATypes:
    """Test A2A type definitions and serialization."""
    
    def test_task_state_enum(self):
        """Test TaskState enum values match spec."""
        assert TaskState.SUBMITTED.value == "submitted"
        assert TaskState.WORKING.value == "working"
        assert TaskState.INPUT_REQUIRED.value == "input-required"
        assert TaskState.COMPLETED.value == "completed"
        assert TaskState.FAILED.value == "failed"
        assert TaskState.CANCELED.value == "canceled"
    
    def test_role_enum(self):
        """Test Role enum values."""
        assert Role.USER.value == "user"
        assert Role.AGENT.value == "agent"
    
    def test_text_part_serialization(self):
        """Test TextPart to_dict."""
        part = TextPart(text="Hello, world!")
        data = part.to_dict()
        
        assert data["type"] == "text"
        assert data["text"] == "Hello, world!"
    
    def test_file_part_serialization(self):
        """Test FilePart to_dict."""
        part = FilePart(
            name="test.txt",
            mime_type="text/plain",
            bytes="SGVsbG8="
        )
        data = part.to_dict()
        
        assert data["type"] == "file"
        assert data["file"]["name"] == "test.txt"
        assert data["file"]["mimeType"] == "text/plain"
        assert data["file"]["bytes"] == "SGVsbG8="
    
    def test_data_part_serialization(self):
        """Test DataPart to_dict."""
        part = DataPart(data={"key": "value"})
        data = part.to_dict()
        
        assert data["type"] == "data"
        assert data["data"] == {"key": "value"}
    
    def test_message_serialization(self):
        """Test Message to_dict and from_dict."""
        message = Message(
            role=Role.USER,
            parts=[TextPart(text="Hello")],
            metadata={"session": "123"}
        )
        data = message.to_dict()
        
        assert data["role"] == "user"
        assert len(data["parts"]) == 1
        assert data["parts"][0]["text"] == "Hello"
        assert data["metadata"] == {"session": "123"}
        
        # Test deserialization
        restored = Message.from_dict(data)
        assert restored.role == Role.USER
        assert len(restored.parts) == 1
    
    def test_message_user_factory(self):
        """Test Message.user() factory method."""
        message = Message.user("Hello")
        
        assert message.role == Role.USER
        assert len(message.parts) == 1
        assert message.parts[0].text == "Hello"
    
    def test_message_agent_factory(self):
        """Test Message.agent() factory method."""
        message = Message.agent("Response")
        
        assert message.role == Role.AGENT
        assert len(message.parts) == 1
        assert message.parts[0].text == "Response"
    
    def test_task_status_serialization(self):
        """Test TaskStatus to_dict and from_dict."""
        status = TaskStatus(
            state=TaskState.WORKING,
            message=Message.agent("Processing...")
        )
        data = status.to_dict()
        
        assert data["state"] == "working"
        assert data["message"]["role"] == "agent"
        assert "timestamp" in data
        
        # Test deserialization
        restored = TaskStatus.from_dict(data)
        assert restored.state == TaskState.WORKING
    
    def test_task_serialization(self):
        """Test Task to_dict and from_dict."""
        task = Task(
            id="task-123",
            status=TaskStatus(state=TaskState.SUBMITTED),
            context_id="ctx-456",
            history=[Message.user("Hello")]
        )
        data = task.to_dict()
        
        assert data["id"] == "task-123"
        assert data["status"]["state"] == "submitted"
        assert data["contextId"] == "ctx-456"
        assert len(data["history"]) == 1
        
        # Test deserialization
        restored = Task.from_dict(data)
        assert restored.id == "task-123"
        assert restored.context_id == "ctx-456"
    
    def test_task_create_factory(self):
        """Test Task.create() factory method."""
        message = Message.user("Start task")
        task = Task.create(message)
        
        assert task.id is not None
        assert task.status.state == TaskState.SUBMITTED
        assert len(task.history) == 1
    
    def test_artifact_serialization(self):
        """Test Artifact to_dict and from_dict."""
        artifact = Artifact(
            name="result.txt",
            parts=[TextPart(text="Result content")],
            index=0
        )
        data = artifact.to_dict()
        
        assert data["name"] == "result.txt"
        assert len(data["parts"]) == 1
        assert data["index"] == 0
        
        restored = Artifact.from_dict(data)
        assert restored.name == "result.txt"


class TestAgentCard:
    """Test Agent Card and Skill types."""
    
    def test_skill_serialization(self):
        """Test Skill to_dict and from_dict."""
        skill = Skill(
            id="research",
            name="Web Research",
            description="Research topics on the web",
            tags=["research", "web"],
            examples=["Research AI trends"]
        )
        data = skill.to_dict()
        
        assert data["id"] == "research"
        assert data["name"] == "Web Research"
        assert "research" in data["tags"]
        
        restored = Skill.from_dict(data)
        assert restored.id == "research"
    
    def test_capability_serialization(self):
        """Test Capability to_dict and from_dict."""
        cap = Capability(
            streaming=True,
            push_notifications=False,
            state_transition_history=True
        )
        data = cap.to_dict()
        
        assert data["streaming"] is True
        assert data["pushNotifications"] is False
        
        restored = Capability.from_dict(data)
        assert restored.streaming is True
    
    def test_agent_card_serialization(self):
        """Test AgentCard to_dict and from_dict."""
        card = AgentCard(
            name="Test Agent",
            description="A test agent",
            url="http://localhost:8000",
            version="1.0.0"
        )
        data = card.to_dict()
        
        assert data["name"] == "Test Agent"
        assert data["protocolVersion"] == "0.3.0"
        assert len(data["supportedInterfaces"]) > 0
        
        restored = AgentCard.from_dict(data)
        assert restored.name == "Test Agent"
    
    def test_agent_card_to_json(self):
        """Test AgentCard.to_json() method."""
        card = AgentCard(
            name="Test Agent",
            description="A test agent",
            url="http://localhost:8000"
        )
        json_str = card.to_json()
        
        # Verify it's valid JSON
        data = json.loads(json_str)
        assert data["name"] == "Test Agent"


class TestGenerateAgentCard:
    """Test Agent Card generation from AgentIdentity."""
    
    def test_generate_from_identity(self):
        """Test generating Agent Card from AgentIdentity."""
        identity = AgentIdentity(
            agent_id="agent-123",
            name="Research Agent",
            agent_type=AgentType.CLAUDE
        )
        
        card = generate_agent_card(
            identity=identity,
            base_url="http://localhost:8000"
        )
        
        assert card.name == "Research Agent"
        assert "http://localhost:8000" in card.url
        assert len(card.skills) > 0
    
    def test_generate_with_custom_skills(self):
        """Test generating with custom skills."""
        identity = AgentIdentity(
            agent_id="agent-123",
            name="Custom Agent",
            agent_type=AgentType.CUSTOM
        )
        
        skills = [
            Skill(
                id="custom-skill",
                name="Custom Skill",
                description="A custom skill"
            )
        ]
        
        card = generate_agent_card(
            identity=identity,
            base_url="http://localhost:8000",
            skills=skills
        )
        
        assert len(card.skills) == 1
        assert card.skills[0].id == "custom-skill"


class TestJSONRPC:
    """Test JSON-RPC types."""
    
    def test_request_serialization(self):
        """Test JSONRPCRequest to_dict."""
        request = JSONRPCRequest(
            method="message/send",
            params={"message": {}},
            id="req-123"
        )
        data = request.to_dict()
        
        assert data["jsonrpc"] == "2.0"
        assert data["method"] == "message/send"
        assert data["id"] == "req-123"
    
    def test_request_from_dict(self):
        """Test JSONRPCRequest.from_dict()."""
        data = {
            "jsonrpc": "2.0",
            "method": "tasks/get",
            "params": {"id": "task-123"},
            "id": 1
        }
        request = JSONRPCRequest.from_dict(data)
        
        assert request.method == "tasks/get"
        assert request.params["id"] == "task-123"
    
    def test_response_serialization(self):
        """Test JSONRPCResponse to_dict."""
        response = JSONRPCResponse(
            id="req-123",
            result={"status": "ok"}
        )
        data = response.to_dict()
        
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "req-123"
        assert data["result"]["status"] == "ok"
    
    def test_error_response(self):
        """Test error response serialization."""
        error = JSONRPCError(
            code=A2AErrorCode.TASK_NOT_FOUND,
            message="Task not found"
        )
        response = JSONRPCResponse(id="req-123", error=error)
        data = response.to_dict()
        
        assert "error" in data
        assert data["error"]["code"] == -32001


class TestStreamResponse:
    """Test StreamResponse wrapper."""
    
    def test_task_response(self):
        """Test StreamResponse with task."""
        task = Task.create()
        response = StreamResponse(task=task)
        data = response.to_dict()
        
        assert "task" in data
    
    def test_message_response(self):
        """Test StreamResponse with message."""
        message = Message.agent("Hello")
        response = StreamResponse(message=message)
        data = response.to_dict()
        
        assert "message" in data


# ============================================================
# Integration Tests (require running server)
# ============================================================

@pytest.mark.asyncio
class TestA2AClientIntegration:
    """Integration tests for A2A client (mocked)."""
    
    async def test_discover_agent_success(self):
        """Test successful agent discovery."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "protocolVersion": "0.3.0",
            "name": "Test Agent",
            "description": "Test",
            "supportedInterfaces": [
                {"url": "http://localhost:8000/a2a", "protocolBinding": "JSONRPC"}
            ],
            "capabilities": {"streaming": True},
            "skills": []
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(A2AClient, 'http_client', new_callable=lambda: MagicMock()) as mock_client:
            client = A2AClient()
            mock_client.get = AsyncMock(return_value=mock_response)
            client._http_client = mock_client
            
            card = await client.discover_agent("http://localhost:8000")
            assert card.name == "Test Agent"


def run_tests():
    """Run all tests."""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
