"""A2A Protocol Server.

FastAPI-based server implementing the A2A protocol specification,
enabling agents to be discovered and communicated with via standard
A2A mechanisms (JSON-RPC 2.0 over HTTP).

Features:
- Agent Card endpoint at /.well-known/agent.json
- JSON-RPC 2.0 endpoint at /a2a
- Streaming support via Server-Sent Events (SSE)
- Task lifecycle management
"""

from typing import Optional, Callable, AsyncIterator, Dict, Any, Union
from contextlib import asynccontextmanager
import json
import asyncio
import uuid

from ..core.exceptions import TaskExecutionError, InitializationError
from ..utils.logger import get_logger

logger = get_logger("a2a.server")

from .types import (
    AgentCard,
    Task,
    TaskState,
    TaskStatus,
    Message,
    StreamResponse,
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    A2AErrorCode,
)


class A2AServer:
    """A2A-compliant server for exposing Unibase agents.

    This server implements the A2A protocol specification, allowing
    any Unibase agent to be discovered and communicated with by
    standard A2A clients.

    Example:
        >>> from unibase_agent_sdk.a2a import A2AServer, AgentCard, Message
        >>>
        >>> async def handle_task(task: Task, message: Message):
        ...     # Process the message and yield responses
        ...     yield StreamResponse(message=Message.agent("Hello!"))
        >>>
        >>> card = AgentCard(
        ...     name="My Agent",
        ...     description="A helpful AI agent",
        ...     url="http://localhost:8000"
        ... )
        >>>
        >>> server = A2AServer(agent_card=card, task_handler=handle_task)
        >>> await server.run()
    """

    def __init__(
        self,
        agent_card: AgentCard,
        task_handler: Callable[[Task, Message], AsyncIterator[StreamResponse]],
        host: str = "0.0.0.0",
        port: int = 8000,
        registration_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize A2A server.

        Args:
            agent_card: Agent Card describing this agent
            task_handler: Async generator function that processes tasks
            host: Host to bind the server to
            port: Port to listen on
            registration_config: Optional config for AIP platform registration.
                                 If provided, agent will be registered on startup.
                                 Keys: user_id, aip_endpoint, handle, name, description, skills
        """
        self.agent_card = agent_card
        self.task_handler = task_handler
        self.host = host
        self.port = port
        self.registration_config = registration_config

        # Task storage (in-memory for now)
        self._tasks: Dict[str, Task] = {}

        # Registration state
        self._agent_id: Optional[str] = None
        self._aip_client = None

        # Create FastAPI app
        self._app = None
    
    def create_app(self):
        """Create and configure the FastAPI application."""
        try:
            from fastapi import FastAPI, Request, Response
            from fastapi.responses import JSONResponse, StreamingResponse
            from fastapi.middleware.cors import CORSMiddleware
        except ImportError:
            raise InitializationError(
                "FastAPI is required for A2A server. "
                "Install it with: pip install fastapi uvicorn"
            )
        
        @asynccontextmanager
        async def lifespan(app):
            logger.info(f"A2A Server starting at http://{self.host}:{self.port}")
            logger.info(f"Agent Card: http://{self.host}:{self.port}/.well-known/agent.json")

            # Register with AIP platform if configured
            if self.registration_config:
                await self._register_with_aip()

            yield

            # Cleanup on shutdown
            if self._aip_client:
                await self._aip_client.close()
            logger.info("A2A Server shutting down")
        
        app = FastAPI(
            title=self.agent_card.name,
            description=self.agent_card.description,
            version=self.agent_card.version,
            lifespan=lifespan
        )
        
        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Agent Card endpoint
        @app.get("/.well-known/agent.json")
        async def get_agent_card():
            return JSONResponse(content=self.agent_card.to_dict())
        
        # JSON-RPC endpoint
        @app.post("/a2a")
        async def jsonrpc_endpoint(request: Request):
            try:
                body = await request.json()
                rpc_request = JSONRPCRequest.from_dict(body)
                
                # Route to appropriate handler
                result = await self._handle_jsonrpc(rpc_request)
                
                return JSONResponse(content=result.to_dict())
                
            except json.JSONDecodeError:
                error = JSONRPCError(
                    code=A2AErrorCode.PARSE_ERROR,
                    message="Invalid JSON"
                )
                return JSONResponse(
                    content=JSONRPCResponse(id=None, error=error).to_dict(),
                    status_code=400
                )
            except Exception as e:
                error = JSONRPCError(
                    code=A2AErrorCode.INTERNAL_ERROR,
                    message=str(e)
                )
                return JSONResponse(
                    content=JSONRPCResponse(id=None, error=error).to_dict(),
                    status_code=500
                )
        
        # Streaming endpoint using SSE
        @app.post("/a2a/stream")
        async def stream_endpoint(request: Request):
            try:
                body = await request.json()
                rpc_request = JSONRPCRequest.from_dict(body)
                
                if rpc_request.method != "message/stream":
                    error = JSONRPCError(
                        code=A2AErrorCode.METHOD_NOT_FOUND,
                        message="Streaming only supports message/stream"
                    )
                    return JSONResponse(
                        content=JSONRPCResponse(id=rpc_request.id, error=error).to_dict(),
                        status_code=400
                    )
                
                async def event_generator():
                    async for response in self._handle_message_stream(rpc_request):
                        data = json.dumps(response.to_dict())
                        yield f"data: {data}\n\n"
                
                return StreamingResponse(
                    event_generator(),
                    media_type="text/event-stream"
                )
                
            except Exception as e:
                error = JSONRPCError(
                    code=A2AErrorCode.INTERNAL_ERROR,
                    message=str(e)
                )
                return JSONResponse(
                    content=JSONRPCResponse(id=None, error=error).to_dict(),
                    status_code=500
                )
        
        # Health check
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "agent": self.agent_card.name}
        
        self._app = app
        return app
    
    async def _handle_jsonrpc(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Handle JSON-RPC request and return response."""
        method_handlers = {
            "message/send": self._handle_message_send,
            "tasks/get": self._handle_tasks_get,
            "tasks/list": self._handle_tasks_list,
            "tasks/cancel": self._handle_tasks_cancel,
        }
        
        handler = method_handlers.get(request.method)
        if not handler:
            return JSONRPCResponse(
                id=request.id,
                error=JSONRPCError(
                    code=A2AErrorCode.METHOD_NOT_FOUND,
                    message=f"Method not found: {request.method}"
                )
            )
        
        try:
            result = await handler(request.params)
            return JSONRPCResponse(id=request.id, result=result)
        except Exception as e:
            return JSONRPCResponse(
                id=request.id,
                error=JSONRPCError(
                    code=A2AErrorCode.INTERNAL_ERROR,
                    message=str(e)
                )
            )
    
    async def _handle_message_send(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle message/send method."""
        # Parse message
        message_data = params.get("message", {})
        message = Message.from_dict(message_data)
        
        # Get or create task
        task_id = params.get("id")
        if task_id and task_id in self._tasks:
            task = self._tasks[task_id]
            task.history.append(message)
        else:
            task = Task.create(message)
            task_id = task.id
            self._tasks[task_id] = task
        
        # Update task status to working
        task.status = TaskStatus(state=TaskState.WORKING)
        
        # Process the message (collect all stream responses)
        try:
            async for response in self.task_handler(task, message):
                if response.message:
                    task.history.append(response.message)
                if response.status_update:
                    task.status = response.status_update.status
                if response.artifact_update:
                    task.artifacts.append(response.artifact_update.artifact)
            
            # Mark as completed if not already in terminal state
            if task.status.state not in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED]:
                task.status = TaskStatus(state=TaskState.COMPLETED)
                
        except Exception as e:
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message=Message.agent(f"Error: {str(e)}")
            )
        
        return task.to_dict()
    
    async def _handle_message_stream(
        self, 
        request: JSONRPCRequest
    ) -> AsyncIterator[JSONRPCResponse]:
        """Handle message/stream method with SSE responses."""
        params = request.params
        message_data = params.get("message", {})
        message = Message.from_dict(message_data)
        
        # Get or create task
        task_id = params.get("id")
        if task_id and task_id in self._tasks:
            task = self._tasks[task_id]
            task.history.append(message)
        else:
            task = Task.create(message)
            task_id = task.id
            self._tasks[task_id] = task
        
        # Update task status
        task.status = TaskStatus(state=TaskState.WORKING)
        
        # Stream responses
        try:
            async for response in self.task_handler(task, message):
                yield JSONRPCResponse(id=request.id, result=response.to_dict())
                
                # Update task state
                if response.message:
                    task.history.append(response.message)
                if response.status_update:
                    task.status = response.status_update.status
                if response.artifact_update:
                    task.artifacts.append(response.artifact_update.artifact)
            
            # Final response with completed task
            if task.status.state not in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED]:
                task.status = TaskStatus(state=TaskState.COMPLETED)
            
            yield JSONRPCResponse(
                id=request.id,
                result=StreamResponse(task=task).to_dict()
            )
            
        except Exception as e:
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message=Message.agent(f"Error: {str(e)}")
            )
            yield JSONRPCResponse(
                id=request.id,
                result=StreamResponse(task=task).to_dict()
            )
    
    async def _handle_tasks_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tasks/get method."""
        task_id = params.get("id")
        if not task_id or task_id not in self._tasks:
            raise TaskExecutionError(f"Task not found: {task_id}")
        return self._tasks[task_id].to_dict()
    
    async def _handle_tasks_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tasks/list method."""
        tasks = list(self._tasks.values())
        
        # Apply filters if provided
        context_id = params.get("contextId")
        if context_id:
            tasks = [t for t in tasks if t.context_id == context_id]
        
        return {
            "tasks": [t.to_dict() for t in tasks]
        }
    
    async def _handle_tasks_cancel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tasks/cancel method."""
        task_id = params.get("id")
        if not task_id or task_id not in self._tasks:
            raise TaskExecutionError(f"Task not found: {task_id}")

        task = self._tasks[task_id]

        # Can only cancel non-terminal tasks
        if task.status.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED]:
            raise TaskExecutionError(f"Task {task_id} is already in terminal state")
        
        task.status = TaskStatus(state=TaskState.CANCELED)
        return task.to_dict()

    async def _register_with_aip(self):
        """Register agent with AIP platform."""
        if not self.registration_config:
            return

        try:
            from aip_sdk import AsyncAIPClient, AgentConfig, SkillConfig
        except ImportError:
            logger.warning(
                "aip_sdk not available, skipping AIP registration. "
                "Install with: pip install unibase-aip-sdk"
            )
            return

        config = self.registration_config
        user_id = config["user_id"]
        aip_endpoint = config["aip_endpoint"]
        handle = config["handle"]

        logger.info(f"Registering agent with AIP platform at {aip_endpoint}")
        logger.info(f"  User ID: {user_id}")
        logger.info(f"  Handle: erc8004:{handle}")

        try:
            # Create AIP client
            self._aip_client = AsyncAIPClient(base_url=aip_endpoint)

            # Build agent config
            skills = [
                SkillConfig(
                    skill_id=s["id"],
                    name=s["name"],
                    description=s.get("description", ""),
                )
                for s in config.get("skills", [])
            ]

            agent_config = AgentConfig(
                name=config["name"],
                handle=handle,
                description=config.get("description", ""),
                endpoint_url=f"http://{self.host}:{self.port}",
                skills=skills,
            )

            # Register with platform
            result = await self._aip_client.register_agent(user_id, agent_config)
            self._agent_id = result.get("agent_id", f"erc8004:{handle}")

            logger.info(f"Agent registered successfully: {self._agent_id}")

        except Exception as e:
            logger.warning(f"AIP registration failed (agent will run without registration): {e}")
            # Don't fail startup - agent can still work without platform registration

    @property
    def agent_id(self) -> Optional[str]:
        """Get the registered agent ID (if registered with AIP)."""
        return self._agent_id

    async def run(self):
        """Start the A2A server."""
        try:
            import uvicorn
        except ImportError:
            raise InitializationError(
                "uvicorn is required to run the A2A server. "
                "Install it with: pip install uvicorn"
            )
        
        app = self.create_app()
        config = uvicorn.Config(
            app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    def run_sync(self):
        """Start the A2A server synchronously."""
        asyncio.run(self.run())


def create_simple_handler(
    response_func: Callable[[str], str]
) -> Callable[[Task, Message], AsyncIterator[StreamResponse]]:
    """Create a simple task handler from a text-to-text function.
    
    This helper makes it easy to create A2A agents from simple
    functions that take a text input and return a text response.
    
    Args:
        response_func: Function that takes input text and returns response text
    
    Returns:
        Task handler suitable for A2AServer
        
    Example:
        >>> def echo(text):
        ...     return f"You said: {text}"
        >>> 
        >>> handler = create_simple_handler(echo)
        >>> server = A2AServer(agent_card=card, task_handler=handler)
    """
    async def handler(task: Task, message: Message) -> AsyncIterator[StreamResponse]:
        # Extract text from message
        input_text = ""
        for part in message.parts:
            if hasattr(part, "text"):
                input_text += part.text
        
        # Generate response
        response_text = response_func(input_text)
        
        # Yield response message
        yield StreamResponse(message=Message.agent(response_text))
    
    return handler


def create_async_handler(
    response_func: Callable[[str], Any]
) -> Callable[[Task, Message], AsyncIterator[StreamResponse]]:
    """Create a task handler from an async text-to-text function.
    
    Similar to create_simple_handler but for async functions.
    """
    async def handler(task: Task, message: Message) -> AsyncIterator[StreamResponse]:
        input_text = ""
        for part in message.parts:
            if hasattr(part, "text"):
                input_text += part.text
        
        response_text = await response_func(input_text)
        yield StreamResponse(message=Message.agent(response_text))
    
    return handler
