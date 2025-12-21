#!/usr/bin/env python3
"""Launch all AIP agents simultaneously.

This script starts all example agents as A2A servers on different ports:
- Weather Agent: http://localhost:8001
- Research Agent: http://localhost:8002
- Travel Agent: http://localhost:8003
- Calculator Agent: http://localhost:8004

Each agent runs in its own process and can be accessed independently via
the A2A protocol.

Usage:
    python examples/aip_agents/launch_all_agents.py

    # Or make it executable and run:
    chmod +x examples/aip_agents/launch_all_agents.py
    ./examples/aip_agents/launch_all_agents.py
"""

import asyncio
import signal
import sys
from typing import List

from unibase_agent_sdk import AgentRegistry, AgentType
from unibase_agent_sdk.a2a import A2AServer

# Import agent factories
from weather_agent import create_weather_agent
from research_agent import create_research_agent
from travel_agent import create_travel_agent
from calculator_agent import create_calculator_agent


class AgentLauncher:
    """Manages launching and coordinating multiple A2A agents."""

    def __init__(self):
        self.servers: List[A2AServer] = []
        self.registry: AgentRegistry = None
        self.tasks: List[asyncio.Task] = []

    async def setup_registry(self):
        """Create and configure the agent registry."""
        self.registry = AgentRegistry(
            aip_endpoint="https://aip.unibase.io",
            membase_endpoint="https://membase.unibase.io",
        )
        print("✅ Agent Registry initialized")

    async def create_all_agents(self):
        """Create all agent instances and their A2A servers."""
        agents_config = [
            ("Weather Agent", create_weather_agent, 8001, "🌤️"),
            ("Research Agent", create_research_agent, 8002, "🔍"),
            ("Travel Agent", create_travel_agent, 8003, "✈️"),
            ("Calculator Agent", create_calculator_agent, 8004, "🔢"),
        ]

        for name, factory, port, emoji in agents_config:
            agent_card, agent = await factory(self.registry)
            agent_card.url = f"http://localhost:{port}"

            # Update supported interfaces with correct URL
            agent_card.supported_interfaces[0].url = f"http://localhost:{port}/a2a"

            server = A2AServer(
                agent_card=agent_card,
                task_handler=agent.handle_task,
                host="0.0.0.0",
                port=port
            )

            self.servers.append(server)
            print(f"{emoji} {name} configured on port {port}")

    async def start_server(self, server: A2AServer):
        """Start a single A2A server."""
        try:
            await server.run()
        except Exception as e:
            print(f"Error running server on port {server.port}: {e}")

    async def run_all(self):
        """Start all agents concurrently."""
        print("\n" + "=" * 70)
        print("🚀 Starting All AIP Agents")
        print("=" * 70)

        # Setup registry
        await self.setup_registry()
        print()

        # Create all agents
        await self.create_all_agents()
        print()

        # Display endpoints
        print("📡 Agent Endpoints:")
        print("-" * 70)
        for server in self.servers:
            card = server.agent_card
            print(f"  {card.name}")
            print(f"    • Agent Card: http://localhost:{server.port}/.well-known/agent.json")
            print(f"    • A2A Endpoint: http://localhost:{server.port}/a2a")
            print(f"    • Skills: {', '.join([s.name for s in card.skills])}")
            print()

        print("=" * 70)
        print("All agents are starting... Press Ctrl+C to stop all agents")
        print("=" * 70)
        print()

        # Start all servers concurrently
        server_tasks = [
            asyncio.create_task(self.start_server(server))
            for server in self.servers
        ]

        self.tasks = server_tasks

        # Wait for all tasks
        try:
            await asyncio.gather(*server_tasks)
        except asyncio.CancelledError:
            print("\n\n🛑 Shutting down all agents...")

    async def shutdown(self):
        """Gracefully shutdown all agents."""
        # Cancel all running tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to finish
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

        # Close registry
        if self.registry:
            await self.registry.close()

        print("✅ All agents stopped successfully")


async def main():
    """Main entry point."""
    launcher = AgentLauncher()

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()

    def signal_handler():
        print("\n\n⚠️  Received shutdown signal...")
        asyncio.create_task(shutdown_handler())

    async def shutdown_handler():
        await launcher.shutdown()
        loop.stop()

    # Register signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await launcher.run_all()
    except KeyboardInterrupt:
        pass
    finally:
        await launcher.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
