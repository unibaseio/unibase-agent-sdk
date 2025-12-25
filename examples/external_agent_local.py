#!/usr/bin/env python3
"""
Example: Run an External Agent Locally with AIP Registration

This example demonstrates how to:
1. Register an agent with the AIP platform
2. Register as an external agent with the gateway (for task pulling)
3. Run the agent locally, pulling tasks from the gateway
4. Trigger the agent through the AIP platform

The agent:
1. Registers itself with AIP (so it appears in agent listings)
2. Registers with the gateway as external agent (for task queue)
3. Polls for tasks (long-polling)
4. Executes tasks and returns results
5. Sends heartbeats to stay registered

Usage:
    # Run with default settings (connects to remote AIP and Gateway)
    python packages/unibase-agent-sdk/examples/external_agent_local.py

    # Run with custom agent name
    python packages/unibase-agent-sdk/examples/external_agent_local.py \
        --name my-calculator --type calculator

    # Run with custom endpoints
    python packages/unibase-agent-sdk/examples/external_agent_local.py \
        --aip-endpoint http://13.215.218.179:5002 \
        --gateway http://13.212.253.141:8081 \
        --name my-agent

After the agent is running, trigger it using (specify the same agent name):
    python packages/unibase-agent-sdk/examples/trigger_agent_via_aip.py \
        --agent my-calculator \
        --objective "Calculate 25 * 4"
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

import httpx

# Add SDK paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "unibase-aip-sdk"))

from aip_sdk.external_agent_client import ExternalAgentClient


class AIPRegisteredExternalAgent(ExternalAgentClient):
    """
    Extended external agent that also registers with the AIP platform.

    This allows the agent to:
    1. Be discoverable via AIP agent listings
    2. Be routed to by the AIP orchestrator
    3. Receive tasks through the gateway task queue
    """

    def __init__(
        self,
        agent_name: str,
        gateway_url: str,
        aip_endpoint: str,
        user_id: str,
        *,
        poll_interval: float = 5.0,
        heartbeat_interval: float = 30.0,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        description: str = "External agent",
        price: float = 0.001,
        tasks: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(
            agent_name=agent_name,
            gateway_url=gateway_url,
            poll_interval=poll_interval,
            heartbeat_interval=heartbeat_interval,
            capabilities=capabilities,
            metadata=metadata,
        )
        self.aip_endpoint = aip_endpoint.rstrip('/')
        self.user_id = user_id
        self.description = description
        self.price = price
        self.tasks = tasks or []
        self.aip_agent_id: Optional[str] = None

    async def register_with_aip(self) -> Dict[str, Any]:
        """Register agent with the AIP platform."""
        print(f"[AIP] Registering agent '{self.agent_name}' with AIP platform...")

        # Build registration payload
        registration_data = {
            "handle": self.agent_name,
            "card": {
                "name": self.agent_name,
                "description": self.description,
                "version": "1.0.0",
            },
            "skills": [{"name": cap} for cap in self.capabilities],
            "endpoint_url": f"{self.gateway_url}/agents/{self.agent_name}/",
            "metadata": {
                "deployment": "external",
                "mode": "external",
                "gateway_url": self.gateway_url,
                **self.metadata,
            },
            "price": {
                "amount": self.price,
                "currency": "credits",
            },
            "tasks": self.tasks,
        }

        url = f"{self.aip_endpoint}/users/{self.user_id}/agents/register"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=registration_data)
            response.raise_for_status()
            result = response.json()

            self.aip_agent_id = result.get("agent_id")
            print(f"[AIP] Agent registered successfully!")
            print(f"      Agent ID: {self.aip_agent_id}")
            print(f"      Handle: {result.get('handle')}")
            return result

    async def run(self):
        """
        Main loop: register with AIP, then register with gateway and poll for tasks.
        """
        try:
            # Step 1: Register with AIP platform
            await self.register_with_aip()
            print()

            # Step 2: Register with gateway (from parent class)
            await self.register()

            self.running = True
            self.started_at = datetime.now()

            # Start heartbeat loop
            self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())

            print()
            print(f"Agent '{self.agent_name}' is now running!")
            print(f"  - Registered with AIP: {self.aip_endpoint}")
            print(f"  - Polling gateway: {self.gateway_url}")
            print()
            print("Press Ctrl+C to stop")
            print()

            # Main polling loop (from parent class logic)
            while self.running:
                try:
                    # Poll for task
                    task = await self.poll_task(timeout=30.0)

                    if task:
                        task_id = task["task_id"]
                        payload = task["payload"]

                        print(f"[Task] Received task {task_id}")
                        print(f"       Payload: {payload}")

                        self.current_task_id = task_id
                        start_time = datetime.now()

                        try:
                            # Execute task
                            result = await self.execute_task(payload)

                            # Calculate execution time
                            execution_time = (datetime.now() - start_time).total_seconds()

                            # Report success
                            await self.complete_task(
                                task_id,
                                result,
                                status="completed",
                                execution_time=execution_time
                            )

                            print(f"[Task] Completed in {execution_time:.2f}s")
                            print(f"       Result: {result}")
                            self.tasks_completed += 1

                        except Exception as e:
                            print(f"[Task] Failed: {e}")

                            # Calculate execution time
                            execution_time = (datetime.now() - start_time).total_seconds()

                            # Report failure
                            await self.complete_task(
                                task_id,
                                {"error": str(e)},
                                status="failed",
                                error=str(e),
                                execution_time=execution_time
                            )

                            self.tasks_failed += 1

                        finally:
                            self.current_task_id = None

                    else:
                        # No tasks, wait before next poll
                        await asyncio.sleep(self.poll_interval)

                except KeyboardInterrupt:
                    print("\nReceived interrupt signal")
                    break

                except Exception as e:
                    print(f"[Error] {e}")
                    await asyncio.sleep(self.poll_interval)

        finally:
            self.running = False

            # Stop heartbeat loop
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass

            print(f"\nAgent '{self.agent_name}' stopped.")
            print(f"  Completed: {self.tasks_completed}, Failed: {self.tasks_failed}")


class CalculatorAgent(AIPRegisteredExternalAgent):
    """
    Calculator agent that performs basic math operations.

    Expected payload format:
    {
        "operation": "add" | "subtract" | "multiply" | "divide",
        "a": number,
        "b": number
    }

    Or natural language in user_request field that will be parsed.
    """

    def _extract_user_request(self, payload: Dict[str, Any]) -> str | None:
        """Extract user_request from various payload formats including A2A JSON-RPC."""
        # Direct user_request field
        if "user_request" in payload:
            return payload["user_request"]

        # A2A JSON-RPC format: params.message.parts[0].text contains JSON with task.payload.user_request
        if payload.get("jsonrpc") == "2.0" and "params" in payload:
            try:
                message = payload["params"].get("message", {})
                parts = message.get("parts", [])
                if parts and parts[0].get("kind") == "text":
                    text = parts[0].get("text", "")
                    # Parse the JSON text
                    import json
                    inner = json.loads(text)
                    task_payload = inner.get("task", {}).get("payload", {})
                    if "user_request" in task_payload:
                        return task_payload["user_request"]
            except (json.JSONDecodeError, KeyError, IndexError):
                pass

        return None

    async def execute_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform calculation based on payload."""
        # Handle user_request from AIP routing (including A2A format)
        user_request = self._extract_user_request(payload)
        if user_request:
            return await self._handle_natural_language(user_request)

        operation = payload.get("operation", "add")
        a = float(payload.get("a", 0))
        b = float(payload.get("b", 0))

        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                return {
                    "status": "error",
                    "error": "Division by zero",
                    "agent_name": self.agent_name
                }
            result = a / b
        else:
            return {
                "status": "error",
                "error": f"Unknown operation: {operation}",
                "agent_name": self.agent_name
            }

        return {
            "status": "success",
            "operation": operation,
            "a": a,
            "b": b,
            "result": result,
            "agent_name": self.agent_name,
            "processed_at": datetime.now().isoformat()
        }

    async def _handle_natural_language(self, user_request: str) -> Dict[str, Any]:
        """Parse natural language math request."""
        import re

        # Try to extract numbers and operator
        # Pattern: number operator number
        pattern = r'(\d+(?:\.\d+)?)\s*([+\-*/x×])\s*(\d+(?:\.\d+)?)'
        match = re.search(pattern, user_request.lower())

        if match:
            a = float(match.group(1))
            op = match.group(2)
            b = float(match.group(3))

            op_map = {
                '+': 'add',
                '-': 'subtract',
                '*': 'multiply',
                '/': 'divide',
                'x': 'multiply',
                '×': 'multiply',
            }
            operation = op_map.get(op, 'add')

            return await self.execute_task({
                "operation": operation,
                "a": a,
                "b": b
            })

        return {
            "status": "error",
            "error": f"Could not parse math expression from: {user_request}",
            "agent_name": self.agent_name
        }


class EchoAgent(AIPRegisteredExternalAgent):
    """
    Simple echo agent that returns the payload with metadata.
    Great for testing that the agent-gateway communication works.
    """

    async def execute_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Echo back the payload with additional metadata."""
        # Simulate some processing time
        await asyncio.sleep(0.5)

        return {
            "status": "success",
            "echo": payload,
            "agent_name": self.agent_name,
            "processed_at": datetime.now().isoformat(),
            "message": f"Hello from {self.agent_name}! I received your message."
        }


class GreeterAgent(AIPRegisteredExternalAgent):
    """
    Greeter agent that generates personalized greetings.

    Expected payload format:
    {
        "name": "string",
        "language": "en" | "es" | "fr" | "zh" (optional, default: "en")
    }
    """

    GREETINGS = {
        "en": "Hello, {name}! Welcome to the Unibase AIP platform!",
        "es": "Hola, {name}! Bienvenido a la plataforma Unibase AIP!",
        "fr": "Bonjour, {name}! Bienvenue sur la plateforme Unibase AIP!",
        "zh": "{name}, 你好! 欢迎来到 Unibase AIP 平台!",
    }

    async def execute_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a greeting based on payload."""
        # Handle user_request from AIP routing
        if "user_request" in payload:
            # Extract name from request if possible
            name = "Guest"
            language = "en"
        else:
            name = payload.get("name", "Guest")
            language = payload.get("language", "en")

        greeting_template = self.GREETINGS.get(language, self.GREETINGS["en"])
        greeting = greeting_template.format(name=name)

        return {
            "status": "success",
            "greeting": greeting,
            "name": name,
            "language": language,
            "agent_name": self.agent_name,
            "processed_at": datetime.now().isoformat()
        }


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Run an external agent locally with AIP registration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run calculator agent (default)
  python external_agent_local.py

  # Run echo agent with custom name
  python external_agent_local.py --type echo --name my-echo

  # Run with custom endpoints
  python external_agent_local.py \\
      --aip-endpoint http://13.215.218.179:5002 \\
      --gateway http://13.212.253.141:8081 \\
      --type calculator

Available agent types:
  - calculator: Performs basic math (add, subtract, multiply, divide)
  - echo: Echoes back the payload (good for testing)
  - greeter: Generates greetings in different languages
        """
    )

    parser.add_argument(
        "--aip-endpoint",
        default=os.environ.get("AIP_ENDPOINT", "http://13.215.218.179:5002"),
        help="AIP platform URL (default: $AIP_ENDPOINT or http://13.215.218.179:5002)"
    )
    parser.add_argument(
        "--gateway",
        default=os.environ.get("GATEWAY_URL", "http://13.212.253.141:8081"),
        help="Gateway URL (default: $GATEWAY_URL or http://13.212.253.141:8081)"
    )
    parser.add_argument(
        "--user-id",
        default=os.environ.get("AIP_USER_ID", "user:0x5eA13664c5ce67753f208540d25B913788Aa3DaA"),
        help="User ID for agent registration (default: $AIP_USER_ID or user:0x5eA13664c5ce67753f208540d25B913788Aa3DaA)"
    )
    parser.add_argument(
        "--type",
        choices=["calculator", "echo", "greeter"],
        default="calculator",
        help="Agent type to run (default: calculator)"
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Agent name (default: agent type name)"
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=5.0,
        help="Poll interval in seconds (default: 5.0)"
    )
    parser.add_argument(
        "--heartbeat-interval",
        type=float,
        default=30.0,
        help="Heartbeat interval in seconds (default: 30.0)"
    )
    parser.add_argument(
        "--price",
        type=float,
        default=0.001,
        help="Price per task in credits (default: 0.001)"
    )

    args = parser.parse_args()
    agent_name = args.name or args.type

    # Print banner
    print("=" * 70)
    print("External Agent - Local Runner with AIP Registration")
    print("=" * 70)
    print(f"  Agent Type:          {args.type}")
    print(f"  Agent Name:          {agent_name}")
    print(f"  AIP Endpoint:        {args.aip_endpoint}")
    print(f"  Gateway URL:         {args.gateway}")
    print(f"  User ID:             {args.user_id}")
    print(f"  Price:               {args.price} credits")
    print(f"  Poll Interval:       {args.poll_interval}s")
    print(f"  Heartbeat Interval:  {args.heartbeat_interval}s")
    print("=" * 70)
    print()

    # Agent configurations
    agent_configs = {
        "calculator": {
            "class": CalculatorAgent,
            "capabilities": ["calculate", "math", "add", "subtract", "multiply", "divide"],
            "description": "Calculator agent that performs basic math operations",
            "tasks": [
                {
                    "name": "calculate",
                    "description": "Perform mathematical calculations (add, subtract, multiply, divide)",
                    "metadata": {"tags": ["math", "calculator"]}
                }
            ],
            "metadata": {
                "operations": ["add", "subtract", "multiply", "divide"],
                "version": "1.0.0",
            },
        },
        "echo": {
            "class": EchoAgent,
            "capabilities": ["echo", "test", "debug"],
            "description": "Echo agent for testing - returns payload with metadata",
            "tasks": [
                {
                    "name": "echo",
                    "description": "Echo back the input payload with metadata",
                    "metadata": {"tags": ["test", "debug"]}
                }
            ],
            "metadata": {
                "purpose": "testing",
                "version": "1.0.0",
            },
        },
        "greeter": {
            "class": GreeterAgent,
            "capabilities": ["greet", "welcome", "multilingual"],
            "description": "Greeter agent that generates multilingual greetings",
            "tasks": [
                {
                    "name": "greet",
                    "description": "Generate a greeting in multiple languages (en, es, fr, zh)",
                    "metadata": {"tags": ["greeting", "multilingual"]}
                }
            ],
            "metadata": {
                "languages": ["en", "es", "fr", "zh"],
                "version": "1.0.0",
            },
        },
    }

    config = agent_configs[args.type]
    AgentClass = config["class"]

    agent = AgentClass(
        agent_name=agent_name,
        gateway_url=args.gateway,
        aip_endpoint=args.aip_endpoint,
        user_id=args.user_id,
        poll_interval=args.poll_interval,
        heartbeat_interval=args.heartbeat_interval,
        capabilities=config["capabilities"],
        metadata=config["metadata"],
        description=config["description"],
        price=args.price,
        tasks=config["tasks"],
    )

    # Run agent
    try:
        await agent.run()
    except KeyboardInterrupt:
        print("\nAgent stopped by user")
    except Exception as e:
        print(f"\nAgent failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
