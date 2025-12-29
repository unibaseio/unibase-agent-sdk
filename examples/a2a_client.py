#!/usr/bin/env python3
"""
A2A Protocol Client Example

Demonstrates how to discover and communicate with A2A-compatible agents.

Usage:
    python a2a_client.py --agent-url http://localhost:8103
"""

import asyncio
import argparse

from unibase_agent_sdk import A2AClient, Message


async def discover_agent(client: A2AClient, agent_url: str):
    """Discover an agent and display its capabilities."""
    print(f"\n{'='*60}")
    print(f"DISCOVERING AGENT: {agent_url}")
    print(f"{'='*60}")

    try:
        card = await client.discover_agent(agent_url)
        print(f"\nAgent Card:")
        print(f"  Name: {card.name}")
        print(f"  Description: {card.description}")
        print(f"  Version: {card.version}")
        print(f"  URL: {card.url}")

        if card.skills:
            print(f"\nSkills ({len(card.skills)}):")
            for skill in card.skills:
                print(f"  - {skill.name}: {skill.description}")
                if skill.examples:
                    print(f"    Examples: {', '.join(skill.examples[:3])}")

        return card
    except Exception as e:
        print(f"Failed to discover agent: {e}")
        return None


async def send_task(client: A2AClient, agent_url: str, message_text: str):
    """Send a task to an agent and get the response."""
    print(f"\n{'='*60}")
    print(f"SENDING TASK")
    print(f"{'='*60}")
    print(f"Message: {message_text}")

    try:
        message = Message.user(message_text)
        task = await client.send_task(agent_url, message)

        print(f"\nTask ID: {task.id}")
        print(f"Status: {task.status.state.value}")

        if task.history:
            print(f"\nResponse:")
            for msg in task.history:
                role = msg.role.value if hasattr(msg.role, 'value') else msg.role
                for part in msg.parts:
                    if hasattr(part, 'text'):
                        print(f"  [{role}]: {part.text}")

        return task
    except Exception as e:
        print(f"Failed to send task: {e}")
        return None


async def stream_task(client: A2AClient, agent_url: str, message_text: str):
    """Stream a task response from an agent."""
    print(f"\n{'='*60}")
    print(f"STREAMING TASK")
    print(f"{'='*60}")
    print(f"Message: {message_text}")
    print(f"\nStreaming response:")

    try:
        message = Message.user(message_text)
        async for response in client.stream_task(agent_url, message):
            if response.message:
                for part in response.message.parts:
                    if hasattr(part, 'text'):
                        print(f"  > {part.text}")
            if response.task:
                print(f"\nTask completed: {response.task.status.state.value}")
    except Exception as e:
        print(f"Failed to stream task: {e}")


async def main():
    parser = argparse.ArgumentParser(description="A2A Protocol Client Example")
    parser.add_argument(
        "--agent-url",
        default="http://localhost:8103",
        help="URL of the A2A agent to communicate with",
    )
    parser.add_argument(
        "--message",
        default="2 + 2",
        help="Message to send to the agent",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Use streaming mode",
    )
    args = parser.parse_args()

    print("A2A Protocol Client Example")
    print("-" * 40)

    async with A2AClient() as client:
        # Discover the agent
        card = await discover_agent(client, args.agent_url)

        if card:
            # Send a task
            if args.stream:
                await stream_task(client, args.agent_url, args.message)
            else:
                await send_task(client, args.agent_url, args.message)

    print(f"\n{'='*60}")
    print("DONE")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
