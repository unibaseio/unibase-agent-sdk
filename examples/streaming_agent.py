#!/usr/bin/env python3
"""
Streaming Agent Example

Demonstrates how to create an A2A agent that streams responses.
Streaming provides better UX for long-running operations.

This example shows:
1. Async generator pattern for streaming
2. Using StreamResponse for typed responses
3. Progress updates during processing

Run:
    python streaming_agent.py

Test:
    # Non-streaming request
    curl -X POST http://localhost:8100/a2a \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"message/send","params":{"message":{"role":"user","parts":[{"type":"text","text":"Tell me a story"}]}},"id":1}'
"""

import asyncio
import os
from typing import AsyncIterator

from unibase_agent_sdk import expose_as_a2a, StreamResponse
from a2a.types import AgentSkill, Message, TextPart, Role


# =============================================================================
# Example 1: Simple Streaming (yield strings)
# =============================================================================

async def simple_streaming_handler(input_text: str) -> AsyncIterator[str]:
    """Stream response word by word.

    The simplest streaming pattern - just yield strings.
    Each yield becomes a chunk sent to the client.
    """
    words = f"You said: {input_text}. Let me think about that...".split()

    for word in words:
        yield word + " "
        await asyncio.sleep(0.1)  # Simulate processing time

    yield "\n\nDone!"


# =============================================================================
# Example 2: Streaming with Progress Updates
# =============================================================================

async def progress_streaming_handler(input_text: str) -> AsyncIterator[str]:
    """Stream with progress updates.

    Useful for long-running operations where you want to
    show progress to the user.
    """
    steps = [
        ("Analyzing input...", 0.5),
        ("Processing request...", 1.0),
        ("Generating response...", 0.5),
    ]

    for step_msg, delay in steps:
        yield f"[Progress] {step_msg}\n"
        await asyncio.sleep(delay)

    # Final response
    yield f"\n[Result] Processed: {input_text}"


# =============================================================================
# Example 3: Streaming with StreamResponse (typed)
# =============================================================================

async def typed_streaming_handler(input_text: str) -> AsyncIterator[StreamResponse]:
    """Stream using StreamResponse for typed responses.

    StreamResponse allows you to send structured messages
    with proper A2A Message types.
    """
    # Send initial acknowledgment
    yield StreamResponse(
        message=Message(
            role=Role.agent,
            parts=[TextPart(text=f"Processing: {input_text}\n")]
        )
    )

    await asyncio.sleep(0.5)

    # Stream the response in chunks
    response_parts = [
        "Here's my analysis:\n",
        "1. First point\n",
        "2. Second point\n",
        "3. Third point\n",
    ]

    for part in response_parts:
        yield StreamResponse(
            message=Message(
                role=Role.agent,
                parts=[TextPart(text=part)]
            )
        )
        await asyncio.sleep(0.3)

    # Final message
    yield StreamResponse(
        message=Message(
            role=Role.agent,
            parts=[TextPart(text="\nAnalysis complete!")]
        )
    )


# =============================================================================
# Example 4: Simulated LLM Streaming
# =============================================================================

async def llm_style_streaming(input_text: str) -> AsyncIterator[str]:
    """Simulate LLM-style token streaming.

    This mimics how real LLMs stream responses token by token.
    """
    # Simulate a response that streams character by character
    response = f"""Based on your input "{input_text}", here's my response:

This is a simulated streaming response that demonstrates how an LLM
would stream tokens. Each character is sent with a small delay to
simulate the generation process.

Key points:
- Streaming improves perceived latency
- Users see results immediately
- Better experience for long responses

Thank you for using the streaming agent!"""

    # Stream character by character (like real LLM)
    for char in response:
        yield char
        await asyncio.sleep(0.02)  # ~50 chars/second


# =============================================================================
# Main
# =============================================================================

HANDLERS = {
    "simple": (simple_streaming_handler, "Simple word-by-word streaming"),
    "progress": (progress_streaming_handler, "Streaming with progress updates"),
    "typed": (typed_streaming_handler, "Typed StreamResponse streaming"),
    "llm": (llm_style_streaming, "LLM-style token streaming"),
}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Streaming agent example")
    parser.add_argument(
        "--mode",
        choices=list(HANDLERS.keys()),
        default="simple",
        help="Streaming mode (default: simple)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("AGENT_PORT", "8100")),
        help="Port to run on (default: 8100)",
    )
    args = parser.parse_args()

    handler, description = HANDLERS[args.mode]

    skills = [
        AgentSkill(
            id="streaming.demo",
            name="Streaming Demo",
            description=description,
            tags=["streaming", "demo"],
        ),
    ]

    server = expose_as_a2a(
        name="Streaming Agent",
        handler=handler,
        port=args.port,
        description=f"Streaming agent demo: {description}",
        skills=skills,
        streaming=True,
    )

    print(f"Streaming Agent ({args.mode} mode)")
    print(f"Port: {args.port}")
    print(f"Agent Card: http://localhost:{args.port}/.well-known/agent.json")
    print("\nPress Ctrl+C to stop\n")

    server.run_sync()


if __name__ == "__main__":
    main()
