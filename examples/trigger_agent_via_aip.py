#!/usr/bin/env python3
"""
Example: Trigger External Agent via AIP Platform

This example demonstrates how to trigger an agent through the AIP platform
using the /runs/stream endpoint. The AIP orchestrator will route your request
to the appropriate agent based on capabilities.

Workflow:
1. Your local agent registers with AIP and gateway (external_agent_local.py)
2. This script sends a request to AIP /runs/stream
3. AIP orchestrator routes the task to your agent via the gateway
4. Your agent pulls the task, executes it, and returns the result
5. This script receives streaming events and the final result

Usage:
    # First, start your local agent in one terminal with a specific name:
    python packages/unibase-agent-sdk/examples/external_agent_local.py \
        --name my-calculator --type calculator

    # Then, in another terminal, trigger it via AIP by specifying the agent:
    python packages/unibase-agent-sdk/examples/trigger_agent_via_aip.py \
        --agent my-calculator \
        --objective "Calculate 25 * 4"

    # Or list registered agents:
    python packages/unibase-agent-sdk/examples/trigger_agent_via_aip.py --list-agents

    # Or see all streaming events:
    python packages/unibase-agent-sdk/examples/trigger_agent_via_aip.py \
        --agent my-calculator \
        --objective "Calculate 100 / 5" --verbose
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, AsyncGenerator, Optional

import httpx

# Add SDK paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "unibase-aip-sdk"))


async def run_via_aip_stream(
    aip_endpoint: str,
    objective: str,
    user_id: Optional[str] = None,
    agent: Optional[str] = None,
    domain_hint: Optional[str] = None,
    timeout: float = 120.0,
    verbose: bool = False,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Send a request to AIP /runs/stream and yield events.

    Args:
        aip_endpoint: AIP platform URL
        objective: The task/objective to execute
        user_id: Optional user ID for payment
        agent: Optional target agent name/handle for direct routing
        domain_hint: Optional hint for agent routing
        timeout: Request timeout
        verbose: Print all events

    Yields:
        Event dictionaries from the stream
    """
    url = f"{aip_endpoint}/runs/stream"

    payload = {"objective": objective}
    if user_id:
        payload["user_id"] = user_id
    if agent:
        payload["agent"] = agent
    if domain_hint:
        payload["domain_hint"] = domain_hint

    print(f"[AIP] Sending request to: {url}")
    print(f"[AIP] Objective: {objective}")
    if agent:
        print(f"[AIP] Target agent: {agent}")
    if domain_hint:
        print(f"[AIP] Domain hint: {domain_hint}")
    print()

    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", url, json=payload) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                raise Exception(f"AIP request failed ({response.status_code}): {error_text.decode()}")

            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue

                raw = line[6:].strip()
                if not raw:
                    continue

                try:
                    event = json.loads(raw)
                    yield event
                except json.JSONDecodeError:
                    if verbose:
                        print(f"[Warning] Failed to parse event: {raw}")


async def run_task_via_aip(
    aip_endpoint: str,
    objective: str,
    user_id: Optional[str] = None,
    agent: Optional[str] = None,
    domain_hint: Optional[str] = None,
    timeout: float = 120.0,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Send a request to AIP and wait for the final result.

    Args:
        aip_endpoint: AIP platform URL
        objective: The task/objective to execute
        user_id: Optional user ID for payment
        agent: Optional target agent name/handle for direct routing
        domain_hint: Optional hint for agent routing
        timeout: Request timeout
        verbose: Print all events

    Returns:
        Final result dictionary
    """
    events = []
    result = None
    error = None

    async for event in run_via_aip_stream(
        aip_endpoint=aip_endpoint,
        objective=objective,
        user_id=user_id,
        agent=agent,
        domain_hint=domain_hint,
        timeout=timeout,
        verbose=verbose,
    ):
        events.append(event)
        event_type = event.get("type", "unknown")

        if verbose:
            summary = event.get("summary_text", "")
            print(f"  [{event_type}] {summary}")

        # Handle different event types
        if event_type == "agent_invoked":
            agent = event.get("agent", "unknown")
            print(f"[Event] Agent invoked: {agent}")

        elif event_type == "agent_completed":
            agent = event.get("agent", "unknown")
            summary = event.get("summary", "")
            print(f"[Event] Agent completed: {agent}")
            if summary:
                print(f"        Summary: {summary}")

        elif event_type == "run_completed":
            result = {
                "status": "completed",
                "run_id": event.get("run_id"),
                "summary": event.get("summary"),
                "output": event.get("output"),
            }

        elif event_type == "run_error":
            error = event.get("error", "Unknown error")
            result = {
                "status": "failed",
                "run_id": event.get("run_id"),
                "error": error,
            }

        elif event_type == "payment_settled":
            if verbose:
                amount = event.get("amount", 0)
                destination = event.get("destination", "unknown")
                print(f"[Payment] {amount} credits to {destination}")

    if result is None:
        result = {
            "status": "unknown",
            "events": events,
        }

    return result


async def list_agents(aip_endpoint: str, user_id: str) -> Dict[str, Any]:
    """List agents registered with AIP for a user."""
    url = f"{aip_endpoint}/users/{user_id}/agents"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


async def list_all_prices(aip_endpoint: str) -> Dict[str, Any]:
    """List all agent prices."""
    url = f"{aip_endpoint}/pricing/agents"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


async def health_check(aip_endpoint: str) -> bool:
    """Check if AIP platform is healthy."""
    url = f"{aip_endpoint}/healthz"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            return response.status_code == 200
    except Exception:
        return False


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Trigger an agent via AIP platform /runs/stream endpoint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Trigger a specific agent by name
  python trigger_agent_via_aip.py --agent my-calculator --objective "Calculate 25 * 4"

  # Trigger with verbose output (see all events)
  python trigger_agent_via_aip.py --agent my-calculator --objective "What is 100 / 5?" -v

  # List registered agents
  python trigger_agent_via_aip.py --list-agents

  # Check AIP health
  python trigger_agent_via_aip.py --health

  # Use custom AIP endpoint
  python trigger_agent_via_aip.py \\
      --aip-endpoint http://13.215.218.179:5002 \\
      --agent my-calculator \\
      --objective "Calculate 7 + 8"
        """
    )

    parser.add_argument(
        "--aip-endpoint",
        default=os.environ.get("AIP_ENDPOINT", "http://13.215.218.179:5002"),
        help="AIP platform URL (default: $AIP_ENDPOINT or http://13.215.218.179:5002)"
    )
    parser.add_argument(
        "--user-id",
        default=os.environ.get("AIP_USER_ID", "user:0x5eA13664c5ce67753f208540d25B913788Aa3DaA"),
        help="User ID for payment (default: $AIP_USER_ID or user:0x5eA13664c5ce67753f208540d25B913788Aa3DaA)"
    )
    parser.add_argument(
        "--agent",
        help="Target agent name (will be included in objective for routing)"
    )
    parser.add_argument(
        "--objective",
        help="The task/objective to send to AIP"
    )
    parser.add_argument(
        "--domain-hint",
        help="Optional domain hint for agent routing"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Request timeout in seconds (default: 120)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show all streaming events"
    )
    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="List agents registered for the user"
    )
    parser.add_argument(
        "--list-prices",
        action="store_true",
        help="List all agent prices"
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Check AIP platform health"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Trigger Agent via AIP Platform")
    print("=" * 70)
    print(f"  AIP Endpoint: {args.aip_endpoint}")
    print(f"  User ID:      {args.user_id}")
    print("=" * 70)
    print()

    # Health check
    if args.health:
        print("Checking AIP platform health...")
        healthy = await health_check(args.aip_endpoint)
        if healthy:
            print("AIP platform is healthy!")
        else:
            print("AIP platform is NOT healthy or unreachable")
            return 1
        return 0

    # List agents
    if args.list_agents:
        print(f"Fetching agents for user '{args.user_id}'...")
        try:
            result = await list_agents(args.aip_endpoint, args.user_id)
            agents = result.get("agents", [])
            total = result.get("total", len(agents))

            print(f"\nRegistered Agents ({total}):")
            print("-" * 60)

            if not agents:
                print("  No agents found for this user")
            else:
                for agent in agents:
                    agent_id = agent.get("agent_id", "unknown")
                    handle = agent.get("handle", "unknown")
                    endpoint = agent.get("endpoint_url", "none")
                    has_wallet = agent.get("has_wallet", False)
                    print(f"  - {handle}")
                    print(f"    ID: {agent_id}")
                    print(f"    Endpoint: {endpoint}")
                    print(f"    Has Wallet: {has_wallet}")
                    print()

        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0

    # List prices
    if args.list_prices:
        print("Fetching agent prices...")
        try:
            result = await list_all_prices(args.aip_endpoint)
            prices = result.get("prices", [])
            total = result.get("total", len(prices))

            print(f"\nAgent Prices ({total}):")
            print("-" * 60)

            if not prices:
                print("  No prices registered")
            else:
                for price in prices:
                    identifier = price.get("identifier", "unknown")
                    amount = price.get("amount", 0)
                    currency = price.get("currency", "credits")
                    print(f"  - {identifier}: {amount} {currency}")

        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0

    # Run task
    if not args.objective:
        print("Error: --objective is required to run a task")
        print("       Use --help for usage information")
        return 1

    try:
        result = await run_task_via_aip(
            aip_endpoint=args.aip_endpoint,
            objective=args.objective,
            user_id=args.user_id,
            agent=args.agent,
            domain_hint=args.domain_hint,
            timeout=args.timeout,
            verbose=args.verbose,
        )

        print()
        print("=" * 70)
        print("Result:")
        print("=" * 70)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get("status") == "completed":
            print("\nSuccess!")
            return 0
        else:
            print("\nTask did not complete successfully")
            return 1

    except Exception as e:
        print(f"\nError: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Is the AIP platform running?")
        print("     Run: python trigger_agent_via_aip.py --health")
        print("  2. Is your agent running and registered?")
        print("     Run: python trigger_agent_via_aip.py --list-agents")
        print("  3. Check the AIP and Gateway logs for errors")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
