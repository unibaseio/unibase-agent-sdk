"""A2A Protocol Client.

Client for communicating with external A2A-compliant agents.
Supports agent discovery via Agent Cards and task execution
via JSON-RPC 2.0 over HTTP.

Features:
- Agent discovery via /.well-known/agent.json
- Synchronous task execution
- Streaming task execution (SSE)
- Task management (get, list, cancel)
"""

from typing import Optional, Dict, Any, AsyncIterator, List, Union
import json
import uuid

import httpx

from .types import (
    AgentCard,
    Task,
    Message,
    StreamResponse,
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
)


class A2AClientError(Exception):
    """Base exception for A2A client errors."""
    pass


class AgentDiscoveryError(A2AClientError):
    """Error discovering an agent via Agent Card."""
    pass


class TaskExecutionError(A2AClientError):
    """Error executing a task."""
    
    def __init__(self, message: str, error: Optional[JSONRPCError] = None):
        super().__init__(message)
        self.error = error


class A2AClient:
    """Client for communicating with A2A-compliant agents.
    
    This client enables discovery and communication with any agent
    that implements the A2A protocol specification.
    
    Example:
        >>> from unibase_agent_sdk.a2a import A2AClient, Message
        >>> 
        >>> async with A2AClient() as client:
        ...     # Discover agent capabilities
        ...     card = await client.discover_agent("https://agent.example.com")
        ...     print(f"Agent: {card.name}")
        ...     print(f"Skills: {[s.name for s in card.skills]}")
        ...     
        ...     # Send a task
        ...     message = Message.user("What can you do?")
        ...     task = await client.send_task(card.url, message)
        ...     print(f"Response: {task.history[-1].parts[0].text}")
    """
    
    def __init__(
        self,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ):
        """Initialize A2A client.
        
        Args:
            timeout: Request timeout in seconds
            headers: Additional headers to include in requests
        """
        self.timeout = timeout
        self._headers = headers or {}
        self._http_client: Optional[httpx.AsyncClient] = None
        
        # Cache for discovered agents
        self._agent_cache: Dict[str, AgentCard] = {}
    
    async def __aenter__(self) -> "A2AClient":
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.aclose()
    
    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get HTTP client, creating if needed."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self._http_client
    
    async def close(self):
        """Close the client and release resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    async def discover_agent(
        self,
        base_url: str,
        force_refresh: bool = False
    ) -> AgentCard:
        """Discover an agent via its Agent Card.
        
        Fetches the agent's capabilities from /.well-known/agent.json
        
        Args:
            base_url: Base URL of the agent
            force_refresh: If True, bypass cache and fetch fresh data
        
        Returns:
            AgentCard describing the agent's capabilities
            
        Raises:
            AgentDiscoveryError: If agent card cannot be fetched
        """
        base_url = base_url.rstrip("/")
        
        # Check cache
        if not force_refresh and base_url in self._agent_cache:
            return self._agent_cache[base_url]
        
        try:
            response = await self.http_client.get(
                f"{base_url}/.well-known/agent.json",
                headers=self._headers
            )
            response.raise_for_status()
            
            card = AgentCard.from_dict(response.json())
            self._agent_cache[base_url] = card
            return card
            
        except httpx.HTTPError as e:
            raise AgentDiscoveryError(
                f"Failed to discover agent at {base_url}: {e}"
            )
        except (json.JSONDecodeError, KeyError) as e:
            raise AgentDiscoveryError(
                f"Invalid agent card at {base_url}: {e}"
            )
    
    async def send_task(
        self,
        agent_url: str,
        message: Message,
        task_id: Optional[str] = None,
        context_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """Send a task to a remote agent.
        
        Executes a task synchronously, waiting for completion.
        
        Args:
            agent_url: A2A endpoint URL (typically base_url/a2a)
            message: Message to send
            task_id: Optional task ID for continuing a task
            context_id: Optional context ID for grouping tasks
            metadata: Optional metadata to include with the task
        
        Returns:
            Task with results
            
        Raises:
            TaskExecutionError: If task execution fails
        """
        agent_url = agent_url.rstrip("/")
        if not agent_url.endswith("/a2a"):
            agent_url = f"{agent_url}/a2a"
        
        # Build request
        params: Dict[str, Any] = {
            "message": message.to_dict()
        }
        if task_id:
            params["id"] = task_id
        if context_id:
            params["contextId"] = context_id
        if metadata:
            params["metadata"] = metadata
        
        request = JSONRPCRequest(
            method="message/send",
            params=params,
            id=str(uuid.uuid4())
        )
        
        try:
            response = await self.http_client.post(
                agent_url,
                json=request.to_dict(),
                headers={**self._headers, "Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            if "error" in data and data["error"]:
                error = JSONRPCError(
                    code=data["error"]["code"],
                    message=data["error"]["message"],
                    data=data["error"].get("data")
                )
                raise TaskExecutionError(
                    f"Task execution failed: {error.message}",
                    error=error
                )
            
            return Task.from_dict(data["result"])
            
        except httpx.HTTPError as e:
            raise TaskExecutionError(f"HTTP error: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            raise TaskExecutionError(f"Invalid response: {e}")
    
    async def stream_task(
        self,
        agent_url: str,
        message: Message,
        task_id: Optional[str] = None,
        context_id: Optional[str] = None,
    ) -> AsyncIterator[StreamResponse]:
        """Stream task responses from a remote agent.
        
        Executes a task with streaming responses via SSE.
        
        Args:
            agent_url: A2A endpoint URL
            message: Message to send
            task_id: Optional task ID for continuing a task
            context_id: Optional context ID for grouping tasks
        
        Yields:
            StreamResponse objects as they arrive
            
        Raises:
            TaskExecutionError: If streaming fails
        """
        agent_url = agent_url.rstrip("/")
        if not agent_url.endswith("/a2a/stream"):
            if agent_url.endswith("/a2a"):
                agent_url = f"{agent_url}/stream"
            else:
                agent_url = f"{agent_url}/a2a/stream"
        
        params: Dict[str, Any] = {
            "message": message.to_dict()
        }
        if task_id:
            params["id"] = task_id
        if context_id:
            params["contextId"] = context_id
        
        request = JSONRPCRequest(
            method="message/stream",
            params=params,
            id=str(uuid.uuid4())
        )
        
        try:
            async with self.http_client.stream(
                "POST",
                agent_url,
                json=request.to_dict(),
                headers={**self._headers, "Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        
                        if "error" in data and data["error"]:
                            error = JSONRPCError(
                                code=data["error"]["code"],
                                message=data["error"]["message"]
                            )
                            raise TaskExecutionError(
                                f"Stream error: {error.message}",
                                error=error
                            )
                        
                        result = data.get("result", {})
                        yield self._parse_stream_response(result)
                        
        except httpx.HTTPError as e:
            raise TaskExecutionError(f"Streaming error: {e}")
    
    def _parse_stream_response(self, data: Dict[str, Any]) -> StreamResponse:
        """Parse a stream response from raw data."""
        response = StreamResponse()
        
        if "task" in data:
            response.task = Task.from_dict(data["task"])
        elif "message" in data:
            response.message = Message.from_dict(data["message"])
        elif "statusUpdate" in data:
            from .types import TaskStatusUpdateEvent, TaskStatus
            update = data["statusUpdate"]
            response.status_update = TaskStatusUpdateEvent(
                task_id=update["taskId"],
                context_id=update.get("contextId"),
                status=TaskStatus.from_dict(update["status"]),
                final=update.get("final", False)
            )
        elif "artifactUpdate" in data:
            from .types import TaskArtifactUpdateEvent, Artifact
            update = data["artifactUpdate"]
            response.artifact_update = TaskArtifactUpdateEvent(
                task_id=update["taskId"],
                context_id=update.get("contextId"),
                artifact=Artifact.from_dict(update["artifact"])
            )
        
        return response
    
    async def get_task(
        self,
        agent_url: str,
        task_id: str
    ) -> Task:
        """Get a task by ID from a remote agent.
        
        Args:
            agent_url: A2A endpoint URL
            task_id: ID of the task to retrieve
        
        Returns:
            Task with current status
            
        Raises:
            TaskExecutionError: If task retrieval fails
        """
        agent_url = agent_url.rstrip("/")
        if not agent_url.endswith("/a2a"):
            agent_url = f"{agent_url}/a2a"
        
        request = JSONRPCRequest(
            method="tasks/get",
            params={"id": task_id},
            id=str(uuid.uuid4())
        )
        
        try:
            response = await self.http_client.post(
                agent_url,
                json=request.to_dict(),
                headers={**self._headers, "Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            if "error" in data and data["error"]:
                raise TaskExecutionError(
                    f"Get task failed: {data['error']['message']}"
                )
            
            return Task.from_dict(data["result"])
            
        except httpx.HTTPError as e:
            raise TaskExecutionError(f"HTTP error: {e}")
    
    async def list_tasks(
        self,
        agent_url: str,
        context_id: Optional[str] = None
    ) -> List[Task]:
        """List tasks from a remote agent.
        
        Args:
            agent_url: A2A endpoint URL
            context_id: Optional context ID to filter by
        
        Returns:
            List of tasks
            
        Raises:
            TaskExecutionError: If listing fails
        """
        agent_url = agent_url.rstrip("/")
        if not agent_url.endswith("/a2a"):
            agent_url = f"{agent_url}/a2a"
        
        params: Dict[str, Any] = {}
        if context_id:
            params["contextId"] = context_id
        
        request = JSONRPCRequest(
            method="tasks/list",
            params=params,
            id=str(uuid.uuid4())
        )
        
        try:
            response = await self.http_client.post(
                agent_url,
                json=request.to_dict(),
                headers={**self._headers, "Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            if "error" in data and data["error"]:
                raise TaskExecutionError(
                    f"List tasks failed: {data['error']['message']}"
                )
            
            return [Task.from_dict(t) for t in data["result"].get("tasks", [])]
            
        except httpx.HTTPError as e:
            raise TaskExecutionError(f"HTTP error: {e}")
    
    async def cancel_task(
        self,
        agent_url: str,
        task_id: str
    ) -> Task:
        """Cancel a task on a remote agent.
        
        Args:
            agent_url: A2A endpoint URL
            task_id: ID of the task to cancel
        
        Returns:
            Task with canceled status
            
        Raises:
            TaskExecutionError: If cancellation fails
        """
        agent_url = agent_url.rstrip("/")
        if not agent_url.endswith("/a2a"):
            agent_url = f"{agent_url}/a2a"
        
        request = JSONRPCRequest(
            method="tasks/cancel",
            params={"id": task_id},
            id=str(uuid.uuid4())
        )
        
        try:
            response = await self.http_client.post(
                agent_url,
                json=request.to_dict(),
                headers={**self._headers, "Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            if "error" in data and data["error"]:
                raise TaskExecutionError(
                    f"Cancel task failed: {data['error']['message']}"
                )
            
            return Task.from_dict(data["result"])
            
        except httpx.HTTPError as e:
            raise TaskExecutionError(f"HTTP error: {e}")
