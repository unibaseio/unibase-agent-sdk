#!/usr/bin/env python3
"""Test client for AIP agents.

This script demonstrates how to interact with the AIP agents using
the A2A protocol client.

Usage:
    # Test all agents
    python examples/aip_agents/test_agent_client.py

    # Test specific agent
    python examples/aip_agents/test_agent_client.py --agent weather
"""

import asyncio
import argparse
from typing import Dict

from unibase_agent_sdk.a2a import A2AClient, Message


# Agent configurations
AGENTS = {
    "weather": {
        "name": "Weather Agent",
        "url": "http://localhost:8001",
        "test_query": "Weather for San Francisco for 5 days"
    },
    "research": {
        "name": "Research Agent",
        "url": "http://localhost:8002",
        "test_query": "Research artificial intelligence with detailed depth"
    },
    "travel": {
        "name": "Travel Agent",
        "url": "http://localhost:8003",
        "test_query": "Plan a trip to Paris in June with $3000 budget and culture interests"
    },
    "calculator": {
        "name": "Calculator Agent",
        "url": "http://localhost:8004",
        "test_query": "Calculate sqrt(144) + sin(pi/2) * 10"
    }
}


async def test_agent(agent_config: Dict[str, str]):
    """Test a single agent."""
    print(f"\n{'='*70}")
    print(f"Testing: {agent_config['name']}")
    print(f"URL: {agent_config['url']}")
    print(f"{'='*70}\n")

    async with A2AClient() as client:
        try:
            # 1. Discover agent
            print("📋 Discovering agent...")
            card = await client.discover_agent(agent_config['url'])
            print(f"   ✅ Found: {card.name}")
            print(f"   Description: {card.description}")
            print(f"   Version: {card.version}")
            print(f"   Skills:")
            for skill in card.skills:
                print(f"      • {skill.name}: {skill.description}")

            # 2. Send test query
            print(f"\n📤 Sending query: '{agent_config['test_query']}'")
            message = Message.user(agent_config['test_query'])
            task = await client.send_task(agent_config['url'], message)

            print(f"\n   Task ID: {task.id}")
            print(f"   Status: {task.status.state.value}")

            # 3. Display response
            print("\n💬 Response:")
            print("-" * 70)
            if task.history:
                for msg in task.history:
                    if msg.role.value == "agent":
                        for part in msg.parts:
                            if hasattr(part, "text"):
                                print(part.text)
            print("-" * 70)

            print(f"\n✅ {agent_config['name']} test completed successfully!")

        except Exception as e:
            print(f"\n❌ Error testing {agent_config['name']}: {e}")
            print(f"   Make sure the agent is running at {agent_config['url']}")
            return False

    return True


async def test_all_agents():
    """Test all available agents."""
    print("\n" + "="*70)
    print("🧪 Testing All AIP Agents")
    print("="*70)

    results = {}
    for agent_key, agent_config in AGENTS.items():
        success = await test_agent(agent_config)
        results[agent_key] = success
        await asyncio.sleep(1)  # Small delay between tests

    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    for agent_key, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {AGENTS[agent_key]['name']}: {status}")

    total = len(results)
    passed = sum(1 for s in results.values() if s)
    print(f"\nTotal: {passed}/{total} agents passed")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test AIP agents")
    parser.add_argument(
        "--agent",
        choices=list(AGENTS.keys()),
        help="Test specific agent (default: test all)"
    )
    args = parser.parse_args()

    if args.agent:
        # Test specific agent
        await test_agent(AGENTS[args.agent])
    else:
        # Test all agents
        await test_all_agents()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Testing interrupted")
