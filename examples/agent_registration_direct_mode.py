#!/usr/bin/env python3
"""
Example: Agent Registration in DIRECT Mode

This example demonstrates how to register an agent that communicates
directly with the AIP platform without a gateway.

Use this mode when:
- Your agent is publicly accessible
- You have a stable public IP or domain
- You don't need NAT traversal or firewall bypass

Environment Variables (optional):
- AIP_ENDPOINT: AIP platform URL (default: http://localhost:8001)
- MEMBASE_ENDPOINT: Membase URL (default: http://localhost:8002)
"""

import asyncio
import sys
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "unibase-agent-sdk"))

from unibase_agent_sdk import (
    AgentRegistry,
    RegistrationMode,
    AgentType,
)


async def main():
    """Register an agent in DIRECT mode."""

    print("=" * 80)
    print("Agent Registration - DIRECT Mode")
    print("=" * 80)
    print()

    # 1. Create registry in DIRECT mode (default)
    print("[1/4] Initializing Registry (DIRECT mode)")
    print("-" * 80)

    registry = AgentRegistry(
        aip_endpoint="http://localhost:8001",  # Or use env var AIP_ENDPOINT
        membase_endpoint="http://localhost:8002",  # Or use env var MEMBASE_ENDPOINT
        mode=RegistrationMode.DIRECT  # DIRECT mode - no gateway
    )

    print("  ✓ Registry initialized in DIRECT mode")
    print(f"    AIP Endpoint: {registry.aip_endpoint}")
    print(f"    Membase Endpoint: {registry.membase_endpoint}")
    print()

    # 2. Register agent identity
    print("[2/4] Registering Agent Identity")
    print("-" * 80)

    identity = await registry.register_agent(
        name="direct-weather-agent",
        agent_type=AgentType.CUSTOM,
        metadata={
            "description": "Weather information agent in direct mode",
            "capabilities": ["weather_forecast", "temperature_check"],
            "version": "1.0.0"
        }
    )

    print(f"  ✓ Agent registered successfully")
    print(f"    Agent ID: {identity.agent_id}")
    print(f"    Name: {identity.name}")
    print(f"    Type: {identity.agent_type.value}")
    print(f"    Mode: {identity.metadata.get('mode', 'direct')}")
    print()

    # 3. Display access information
    print("[3/4] Agent Access Information")
    print("-" * 80)
    print(f"  Agent will be accessible via AIP platform routing")
    print(f"  Other agents can communicate using:")
    print(f"    - Agent ID: {identity.agent_id}")
    print(f"    - Via registry.send_message_to_agent()")
    print()

    # 4. Show agent metadata
    print("[4/4] Agent Metadata")
    print("-" * 80)
    for key, value in identity.metadata.items():
        print(f"    {key}: {value}")
    print()

    # Summary
    print("=" * 80)
    print("Registration Complete!")
    print("=" * 80)
    print()
    print("ℹ️  In DIRECT mode:")
    print("  - Agent communicates directly with AIP platform")
    print("  - No gateway or proxy needed")
    print("  - Requires agent to be publicly accessible")
    print("  - Best for production deployments with stable infrastructure")
    print()

    # Cleanup
    await registry.close()


if __name__ == "__main__":
    asyncio.run(main())
