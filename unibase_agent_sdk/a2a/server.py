"""A2A Protocol Server."""

from typing import Optional, Callable, AsyncIterator, Dict, Any
from contextlib import asynccontextmanager
import json
import asyncio
import uuid

from ..core.exceptions import TaskExecutionError, InitializationError
from ..utils.logger import get_logger
from ..utils.config import get_default_aip_endpoint

logger = get_logger("a2a.server")

# Import directly from Google A2A SDK
from a2a.types import (
    AgentCard,
    Task,
    TaskState,
    TaskStatus,
    Message,
    TextPart,
    Role,
)
from a2a.utils.message import get_message_text
from a2a.client.helpers import create_text_message_object

# Import Unibase extensions
from .types import StreamResponse, A2AErrorCode


class A2AServer:
    """A2A-compliant server for exposing Unibase agents."""

    def __init__(
        self,
        agent_card: AgentCard,
        task_handler: Callable[[Task, Message], AsyncIterator[StreamResponse]],
        host: str = "0.0.0.0",
        port: int = 8000,
        registration_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize A2A server."""
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

    def _serialize_agent_card(self) -> Dict[str, Any]:
        """Serialize agent card to dict using Pydantic."""
        return self.agent_card.model_dump(by_alias=True, exclude_none=True)

    def _serialize_task(self, task: Task) -> Dict[str, Any]:
        """Serialize task to dict using Pydantic."""
        return task.model_dump(by_alias=True, exclude_none=True)

    def _parse_message(self, message_data: Dict[str, Any]) -> Message:
        """Parse message from dict using Pydantic."""
        return Message.model_validate(message_data)

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
            return JSONResponse(content=self._serialize_agent_card())

        # JSON-RPC endpoint - available at both / and /a2a for compatibility
        # Google A2A protocol expects JSONRPC at root URL
        @app.post("/")
        @app.post("/a2a")
        async def jsonrpc_endpoint(request: Request):
            try:
                body = await request.json()
                rpc_request = self._parse_jsonrpc_request(body)

                # Route to appropriate handler
                result = await self._handle_jsonrpc(rpc_request, body.get("id"))

                return JSONResponse(content=result)

            except json.JSONDecodeError:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": A2AErrorCode.PARSE_ERROR, "message": "Invalid JSON"}
                }
                return JSONResponse(content=error_response, status_code=400)
            except Exception as e:
                logger.exception(f"Error handling JSON-RPC request: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": A2AErrorCode.INTERNAL_ERROR, "message": str(e)}
                }
                return JSONResponse(content=error_response, status_code=500)

        # Streaming endpoint using SSE
        @app.post("/a2a/stream")
        async def stream_endpoint(request: Request):
            try:
                body = await request.json()
                rpc_request = self._parse_jsonrpc_request(body)

                if rpc_request["method"] != "message/stream":
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "error": {"code": A2AErrorCode.METHOD_NOT_FOUND, "message": "Streaming only supports message/stream"}
                    }
                    return JSONResponse(content=error_response, status_code=400)

                async def event_generator():
                    async for response in self._handle_message_stream(rpc_request, body.get("id")):
                        data = json.dumps(response)
                        yield f"data: {data}\n\n"

                return StreamingResponse(
                    event_generator(),
                    media_type="text/event-stream"
                )

            except Exception as e:
                logger.exception(f"Error in stream endpoint: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": A2AErrorCode.INTERNAL_ERROR, "message": str(e)}
                }
                return JSONResponse(content=error_response, status_code=500)

        # Health check
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "agent": self.agent_card.name}

        # Health check (alternative endpoint for gateway compatibility)
        @app.get("/healthz")
        async def healthz_check():
            return {"status": "healthy", "agent": self.agent_card.name}

        self._app = app
        return app

    def _parse_jsonrpc_request(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate JSON-RPC request."""
        if body.get("jsonrpc") != "2.0":
            raise ValueError("Invalid JSON-RPC version")
        if "method" not in body:
            raise ValueError("Missing method")
        return {
            "method": body["method"],
            "params": body.get("params", {}),
            "id": body.get("id"),
        }

    async def _handle_jsonrpc(self, request: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle JSON-RPC request and return response."""
        method_handlers = {
            "message/send": self._handle_message_send,
            "tasks/get": self._handle_tasks_get,
            "tasks/list": self._handle_tasks_list,
            "tasks/cancel": self._handle_tasks_cancel,
        }

        handler = method_handlers.get(request["method"])
        if not handler:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": A2AErrorCode.METHOD_NOT_FOUND, "message": f"Method not found: {request['method']}"}
            }

        try:
            result = await handler(request["params"])
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        except TaskExecutionError as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": A2AErrorCode.TASK_NOT_FOUND, "message": str(e)}
            }
        except Exception as e:
            logger.exception(f"Error handling {request['method']}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": A2AErrorCode.INTERNAL_ERROR, "message": str(e)}
            }

    async def _handle_message_send(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle message/send method."""
        # Parse message from params
        message_data = params.get("message", {})
        message = self._parse_message(message_data)

        # Get or create task
        task_id = params.get("id") or str(uuid.uuid4())
        context_id = params.get("contextId") or str(uuid.uuid4())

        if task_id in self._tasks:
            task = self._tasks[task_id]
            # Add message to history
            task = Task(
                id=task.id,
                context_id=task.context_id,
                status=task.status,
                history=list(task.history or []) + [message],
                artifacts=task.artifacts,
                metadata=task.metadata,
            )
        else:
            task = Task(
                id=task_id,
                context_id=context_id,
                status=TaskStatus(state=TaskState.submitted),
                history=[message],
            )

        self._tasks[task_id] = task

        # Update task status to working
        task = Task(
            id=task.id,
            context_id=task.context_id,
            status=TaskStatus(state=TaskState.working),
            history=task.history,
            artifacts=task.artifacts,
            metadata=task.metadata,
        )
        self._tasks[task_id] = task

        # Process the message (collect all stream responses)
        try:
            history = list(task.history or [])
            artifacts = list(task.artifacts or [])

            async for response in self.task_handler(task, message):
                if response.message:
                    history.append(response.message)
                if response.status_update:
                    task = Task(
                        id=task.id,
                        context_id=task.context_id,
                        status=response.status_update.status,
                        history=history,
                        artifacts=artifacts,
                        metadata=task.metadata,
                    )
                if response.artifact_update:
                    artifacts.append(response.artifact_update.artifact)

            # Mark as completed if not already in terminal state
            final_state = task.status.state
            if final_state not in [TaskState.completed, TaskState.failed, TaskState.canceled]:
                final_state = TaskState.completed

            task = Task(
                id=task.id,
                context_id=task.context_id,
                status=TaskStatus(state=final_state),
                history=history,
                artifacts=artifacts if artifacts else None,
                metadata=task.metadata,
            )

        except Exception as e:
            logger.exception(f"Error in task handler: {e}")
            error_message = create_text_message_object(Role.agent, f"Error: {str(e)}")
            task = Task(
                id=task.id,
                context_id=task.context_id,
                status=TaskStatus(state=TaskState.failed, message=error_message),
                history=list(task.history or []),
                artifacts=task.artifacts,
                metadata=task.metadata,
            )

        self._tasks[task_id] = task

        # Return the last agent message for compatibility with A2A middleware
        # The middleware expects result.kind === "message" to extract text
        # If we return a Task, it JSON.stringifies the whole object
        if history:
            last_agent_messages = [m for m in history if m.role == Role.agent]
            if last_agent_messages:
                response_data = last_agent_messages[-1].model_dump(by_alias=True, exclude_none=True)

                # Add AIP events to response metadata for AG-UI protocol
                aip_events = await self._get_aip_events()
                if aip_events:
                    if "metadata" not in response_data or response_data["metadata"] is None:
                        response_data["metadata"] = {}
                    response_data["metadata"]["aip_events"] = aip_events

                return response_data

        # Fallback: return task if no agent message found
        return self._serialize_task(task)

    async def _handle_message_stream(
        self,
        request: Dict[str, Any],
        request_id: Any
    ) -> AsyncIterator[Dict[str, Any]]:
        """Handle message/stream method with SSE responses."""
        params = request["params"]
        message_data = params.get("message", {})
        message = self._parse_message(message_data)

        # Get or create task
        task_id = params.get("id") or str(uuid.uuid4())
        context_id = params.get("contextId") or str(uuid.uuid4())

        if task_id in self._tasks:
            task = self._tasks[task_id]
            task = Task(
                id=task.id,
                context_id=task.context_id,
                status=task.status,
                history=list(task.history or []) + [message],
                artifacts=task.artifacts,
                metadata=task.metadata,
            )
        else:
            task = Task(
                id=task_id,
                context_id=context_id,
                status=TaskStatus(state=TaskState.submitted),
                history=[message],
            )

        self._tasks[task_id] = task

        # Update task status to working
        task = Task(
            id=task.id,
            context_id=task.context_id,
            status=TaskStatus(state=TaskState.working),
            history=task.history,
            artifacts=task.artifacts,
            metadata=task.metadata,
        )
        self._tasks[task_id] = task

        # Stream responses
        try:
            history = list(task.history or [])
            artifacts = list(task.artifacts or [])

            async for response in self.task_handler(task, message):
                event = response.get_event()
                if event:
                    yield {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": event.model_dump(by_alias=True, exclude_none=True)
                    }

                # Update task state
                if response.message:
                    history.append(response.message)
                if response.status_update:
                    task = Task(
                        id=task.id,
                        context_id=task.context_id,
                        status=response.status_update.status,
                        history=history,
                        artifacts=artifacts if artifacts else None,
                        metadata=task.metadata,
                    )
                if response.artifact_update:
                    artifacts.append(response.artifact_update.artifact)

            # Final response with completed task
            final_state = task.status.state
            if final_state not in [TaskState.completed, TaskState.failed, TaskState.canceled]:
                final_state = TaskState.completed

            task = Task(
                id=task.id,
                context_id=task.context_id,
                status=TaskStatus(state=final_state),
                history=history,
                artifacts=artifacts if artifacts else None,
                metadata=task.metadata,
            )
            self._tasks[task_id] = task

            yield {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": self._serialize_task(task)
            }

        except Exception as e:
            logger.exception(f"Error in stream handler: {e}")
            error_message = create_text_message_object(Role.agent, f"Error: {str(e)}")
            task = Task(
                id=task.id,
                context_id=task.context_id,
                status=TaskStatus(state=TaskState.failed, message=error_message),
                history=list(task.history or []),
                artifacts=task.artifacts,
                metadata=task.metadata,
            )
            self._tasks[task_id] = task

            yield {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": self._serialize_task(task)
            }

    async def _handle_tasks_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tasks/get method."""
        task_id = params.get("id")
        if not task_id or task_id not in self._tasks:
            raise TaskExecutionError(f"Task not found: {task_id}")
        return self._serialize_task(self._tasks[task_id])

    async def _handle_tasks_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tasks/list method."""
        tasks = list(self._tasks.values())

        # Apply filters if provided
        context_id = params.get("contextId")
        if context_id:
            tasks = [t for t in tasks if t.context_id == context_id]

        return {
            "tasks": [self._serialize_task(t) for t in tasks]
        }

    async def _handle_tasks_cancel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tasks/cancel method."""
        task_id = params.get("id")
        if not task_id or task_id not in self._tasks:
            raise TaskExecutionError(f"Task not found: {task_id}")

        task = self._tasks[task_id]

        # Can only cancel non-terminal tasks
        if task.status.state in [TaskState.completed, TaskState.failed, TaskState.canceled]:
            raise TaskExecutionError(f"Task {task_id} is already in terminal state")

        task = Task(
            id=task.id,
            context_id=task.context_id,
            status=TaskStatus(state=TaskState.canceled),
            history=task.history,
            artifacts=task.artifacts,
            metadata=task.metadata,
        )
        self._tasks[task_id] = task
        return self._serialize_task(task)

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

            # Import CostModel to reconstruct from dict
            from aip_sdk.types import CostModel
            cost_model_data = config.get("cost_model", {})
            cost_model = CostModel.from_dict(cost_model_data) if cost_model_data else CostModel()

            agent_config = AgentConfig(
                name=config["name"],
                handle=handle,
                description=config.get("description", ""),
                endpoint_url=f"http://{self.host}:{self.port}",
                skills=skills,
                cost_model=cost_model,
                currency=config.get("currency", "USD"),
            )

            # Register with platform
            result = await self._aip_client.register_agent(user_id, agent_config)
            self._agent_id = result.get("agent_id", f"erc8004:{handle}")

            logger.info(f"Agent registered successfully: {self._agent_id}")

        except Exception as e:
            logger.warning(f"AIP registration failed (agent will run without registration): {e}")
            # Don't fail startup - agent can still work without platform registration

    async def _get_aip_events(self) -> Optional[list]:
        """Get recent AIP events (payments, memory) for this agent.

        Returns events in a format suitable for the AG-UI protocol.
        These events are included in the A2A response metadata and
        can be displayed by the frontend.
        """
        if not self.registration_config or not self._aip_client:
            return None

        try:
            import httpx
            from datetime import datetime

            aip_endpoint = self.registration_config.get("aip_endpoint", get_default_aip_endpoint())
            agent_id = self._agent_id or f"erc8004:{self.registration_config.get('handle', '')}"

            # Query AIP for recent events for this agent
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{aip_endpoint}/agents/{agent_id}/events",
                    params={"limit": 10, "types": "payment_settled,memory_uploaded"}
                )

                if response.status_code == 200:
                    events = response.json()
                    if events:
                        # Transform events to AG-UI compatible format
                        result = []
                        for event in events:
                            event_type = event.get("type", "")
                            if event_type in ("payment_settled", "payment.settled"):
                                result.append({
                                    "type": "payment",
                                    "agent_id": event.get("destination") or agent_id,
                                    "amount": float(event.get("amount", 0)),
                                    "currency": event.get("currency", "USD"),
                                    "timestamp": event.get("ts", datetime.now().isoformat()),
                                    "transaction_url": event.get("tx_url"),
                                    "status": "settled"
                                })
                            elif "memory" in event_type:
                                result.append({
                                    "type": "memory",
                                    "scope": event.get("scope") or event.get("key", "unknown"),
                                    "operation": event.get("operation", "write"),
                                    "timestamp": event.get("ts", datetime.now().isoformat()),
                                    "membase_url": event.get("membase_url"),
                                    "data_size": event.get("size")
                                })
                        return result if result else None
        except Exception as e:
            logger.debug(f"Failed to get AIP events: {e}")

        return None

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
    """Create a simple task handler from a text-to-text function."""
    async def handler(task: Task, message: Message) -> AsyncIterator[StreamResponse]:
        # Extract text from message using Google A2A utility
        input_text = get_message_text(message)

        # Generate response
        response_text = response_func(input_text)

        # Yield response message using Google A2A helper
        response_msg = create_text_message_object(Role.agent, response_text)
        yield StreamResponse(message=response_msg)

    return handler


def create_async_handler(
    response_func: Callable[[str], Any]
) -> Callable[[Task, Message], AsyncIterator[StreamResponse]]:
    """Create a task handler from an async text-to-text function."""
    async def handler(task: Task, message: Message) -> AsyncIterator[StreamResponse]:
        input_text = get_message_text(message)
        response_text = await response_func(input_text)
        response_msg = create_text_message_object(Role.agent, response_text)
        yield StreamResponse(message=response_msg)

    return handler
