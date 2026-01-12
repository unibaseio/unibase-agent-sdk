#!/usr/bin/env python3
"""
Streaming Agent with Registration Example

Demonstrates how to create an A2A agent that streams responses AND registers itself 
with the AIP platform at startup.

This example builds on `streaming_agent.py` by adding:
1. Registration configuration (user_id, aip_endpoint)
2. Auto-registration on startup
3. Optional pricing configuration

Run:
    python streaming_agent_with_registration.py --user-id "user:0x123...789"

Test:
    # First, the agent will register itself with the AIP platform.
    # Then you can interact with it via the Gateway or directly.
    
    curl -X POST http://localhost:8100/a2a \\
        -H "Content-Type: application/json" \\
        -d '{"jsonrpc":"2.0","method":"message/send","params":{"message":{"role":"user","parts":[{"type":"text","text":"Tell me a story"}],"messageId":"test-msg-1"}},"id":1}'

    # To test STREAMING (SSE):
    curl -N -X POST http://localhost:8100/a2a/stream \\
        -H "Content-Type: application/json" \\
        -d '{"jsonrpc":"2.0","method":"message/stream","params":{"message":{"role":"user","parts":[{"type":"text","text":"Tell me a story"}],"messageId":"test-msg-1"}},"id":1}'
"""

import asyncio
import os
import argparse
import dotenv
dotenv.load_dotenv()
from typing import AsyncIterator

from unibase_agent_sdk import expose_as_a2a, StreamResponse
from a2a.types import AgentSkill, Message, TextPart, Role
from aip_sdk.types import CostModel


# =============================================================================
# Handlers (Reused from streaming_agent.py for simplicity)
# =============================================================================
async def openai_streaming_handler(input_text: str) -> AsyncIterator[str]:
    """Streaming OpenAI handler."""
    try:
        from openai import AsyncOpenAI
    except ImportError:
        yield "Error: pip install openai"
        return

    print("OpenAI Streaming Handler", input_text)
    client = AsyncOpenAI()
    stream = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": input_text}],
        max_tokens=1024,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

async def simple_streaming_handler(input_text: str) -> AsyncIterator[str]:
    """Stream response word by word."""
    words = f"You said: {input_text}. Let me think about that...".split()

    for word in words:
        yield word + " "
        await asyncio.sleep(0.1)

    yield "\\n\\nDone!"

# =============================================================================
# Main
# =============================================================================

HANDLERS = {
    "simple": (simple_streaming_handler, "Simple word-by-word streaming"),
    "llm": (openai_streaming_handler, "LLM-style token streaming"),
}


def main():
    parser = argparse.ArgumentParser(description="Streaming agent with registration")
    parser.add_argument(
        "--mode",
        choices=list(HANDLERS.keys()),
        default="llm",
        help="Streaming mode (default: llm)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("AGENT_PORT", "8100")),
        help="Port to run on (default: 8100)",
    )
    
    # Registration arguments
    parser.add_argument(
        "--user-id",
        required=True,
        help="AIP User ID (e.g., user:0x123...)",
    )
    parser.add_argument(
        "--aip-endpoint",
        default=os.environ.get("AIP_ENDPOINT", "http://localhost:8001"),
        help="AIP Platform Endpoint",
    )
    parser.add_argument(
        "--cost-per-call",
        type=float,
        default=0.01,
        help="Cost per call in USD (default: 0.01)",
    )
    
    args = parser.parse_args()

    handler, description = HANDLERS[args.mode]

    # Define skills
    skills = [
        AgentSkill(
            id="streaming.registered.demo",
            name="Registered Streaming Demo",
            description=description,
            tags=["streaming", "demo", "registered"],
        ),
    ]

    # Create server with registration config
    # The `expose_as_a2a` wrapper handles the actual registration logic
    server = expose_as_a2a(
        name="Registered Streaming Agent",
        handler=handler,
        port=args.port,
        description=f"A registered streaming agent: {description}",
        skills=skills,
        streaming=True,
        
        # Registration parameters
        user_id=args.user_id,
        aip_endpoint=args.aip_endpoint,
        auto_register=True,
        cost_model=None,
    )

    print(f"Registered Streaming Agent ({args.mode} mode)")
    print(f"Port: {args.port}")
    print(f"Agent Card: http://localhost:{args.port}/.well-known/agent.json")
    print(f"AIP Endpoint: {args.aip_endpoint}")
    print(f"User ID: {args.user_id}")
    print("\nPress Ctrl+C to stop\n")

    server.run_sync()


if __name__ == "__main__":
    main()
