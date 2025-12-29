#!/usr/bin/env python3
"""
Example: Agent Registration in GATEWAY Mode

This example demonstrates how to register an agent that communicates
through a gateway/proxy. The gateway handles routing and can support
agents behind firewalls or NAT.

Use this mode when:
- Your agent is behind a firewall or NAT
- You want centralized routing through a single gateway
- You're running multiple agents on different ports
- You need load balancing or failover capabilities

Prerequisites:
1. Start the gateway:
   python -m gateway.main --port 8080

2. Start your agent backend on a local port (e.g., 8103)

Environment Variables (optional):
- AIP_ENDPOINT: AIP platform URL (default: http://localhost:8001)
- GATEWAY_URL: Gateway URL (default: http://localhost:8080)
- AGENT_BACKEND_URL: Agent's backend URL (e.g., http://localhost:8103)
"""

import asyncio
import sys
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "unibase-agent-sdk"))

from unibase_agent_sdk import (
    AgentRegistry,
    RegistrationMode,
    AgentType,
)


async def main():
    """Register an agent in GATEWAY mode."""

    print("=" * 80)
    print("Agent Registration - GATEWAY Mode")
    print("=" * 80)
    print()

    # 1. Create registry in GATEWAY mode
    print("[1/5] Initializing Registry (GATEWAY mode)")
    print("-" * 80)

    registry = AgentRegistry(
        aip_endpoint="http://localhost:8001",  # Or use env var AIP_ENDPOINT
        mode=RegistrationMode.GATEWAY,  # GATEWAY mode
        gateway_url="http://localhost:8080",  # Or use env var GATEWAY_URL
        agent_backend_url="http://localhost:8103"  # Or use env var AGENT_BACKEND_URL
    )

    print("  ✓ Registry initialized in GATEWAY mode")
    print(f"    AIP Endpoint: {registry.aip_endpoint}")
    print(f"    Gateway URL: {registry.gateway_url}")
    print(f"    Agent Backend URL: {registry.agent_backend_url}")
    print()

    # 2. Register agent identity (with gateway)
    print("[2/5] Registering Agent with Gateway")
    print("-" * 80)

    identity = await registry.register_agent(
        name="gateway-weather-agent",
        agent_type=AgentType.CUSTOM,
        metadata={
            "description": "Weather information agent behind gateway",
            "capabilities": ["weather_forecast", "temperature_check"],
            "version": "1.0.0"
        }
    )

    print(f"  ✓ Agent registered successfully")
    print(f"    Agent ID: {identity.agent_id}")
    print(f"    Name: {identity.name}")
    print(f"    Type: {identity.agent_type.value}")
    print(f"    Mode: {identity.metadata.get('mode', 'gateway')}")
    print()

    # 3. Display gateway routing information
    print("[3/5] Gateway Routing Information")
    print("-" * 80)
    endpoint_url = identity.metadata.get('endpoint_url')
    if endpoint_url:
        print(f"  ✓ Agent is accessible via gateway:")
        print(f"    Gateway URL: {endpoint_url}")
        print(f"  ")
        print(f"  Request flow:")
        print(f"    Client → {endpoint_url}")
        print(f"           ↓ (Gateway routes to)")
        print(f"           → {registry.agent_backend_url}")
    print()

    # 4. Display access information
    print("[4/5] Agent Access Information")
    print("-" * 80)
    print(f"  External clients should use:")
    print(f"    Endpoint: {endpoint_url}")
    print(f"  ")
    print(f"  Other agents can communicate using:")
    print(f"    - Agent ID: {identity.agent_id}")
    print(f"    - Via registry.send_message_to_agent()")
    print()

    # 5. Show agent metadata
    print("[5/5] Agent Metadata")
    print("-" * 80)
    for key, value in identity.metadata.items():
        if value is not None:
            print(f"    {key}: {value}")
    print()

    # Summary
    print("=" * 80)
    print("Registration Complete!")
    print("=" * 80)
    print()
    print("ℹ️  In GATEWAY mode:")
    print("  - Agent runs on local backend (localhost:8103)")
    print("  - Gateway proxies requests from public endpoint")
    print("  - Agent can be behind firewall/NAT")
    print("  - Multiple agents can share single gateway port")
    print("  - Gateway provides routing, monitoring, and health checks")
    print()
    print("💡 Tips:")
    print(f"  - Test your agent: curl -X POST {endpoint_url}/task")
    print(f"  - View gateway status: curl {registry.gateway_url}/gateway/agents")
    print(f"  - Agent metrics: curl {endpoint_url}/metrics")
    print()

    # Cleanup
    await registry.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n⚠️  Make sure:")
        print("   1. Gateway is running: python -m gateway.main --port 8080")
        print("   2. Agent backend is running on the configured port")
        sys.exit(1)
