#!/usr/bin/env python3
"""
LLM SDK Integrations - Expose Any LLM Agent as A2A Service

This example shows how to integrate popular LLM SDKs with Unibase:
- Anthropic (Claude)
- OpenAI
- Google (Gemini)

All examples follow the same pattern:
1. Create your agent/handler using the native SDK
2. Wrap it with expose_as_a2a()
3. Run the server

Requirements:
    uv pip install anthropic openai google-generativeai

Environment Variables:
    ANTHROPIC_API_KEY - For Claude examples
    OPENAI_API_KEY - For OpenAI examples
    GOOGLE_API_KEY - For Gemini examples
    AGENT_PORT - Port to run on (default: 8100)
"""

import asyncio
import os
from typing import AsyncIterator

from unibase_agent_sdk import expose_as_a2a
from a2a.types import AgentSkill


# =============================================================================
# Example 1: Anthropic (Claude)
# =============================================================================

async def claude_handler(input_text: str) -> str:
    """Simple Claude handler."""
    try:
        import anthropic
    except ImportError:
        return "Error: uv pip install anthropic"

    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": input_text}]
    )
    return response.content[0].text


async def claude_streaming_handler(input_text: str) -> AsyncIterator[str]:
    """Streaming Claude handler."""
    try:
        import anthropic
    except ImportError:
        yield "Error: uv pip install anthropic"
        return

    client = anthropic.AsyncAnthropic()
    async with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": input_text}]
    ) as stream:
        async for text in stream.text_stream:
            yield text


# =============================================================================
# Example 2: OpenAI (GPT-4)
# =============================================================================

async def openai_handler(input_text: str) -> str:
    """Simple OpenAI handler."""
    try:
        from openai import AsyncOpenAI
    except ImportError:
        return "Error: uv pip install openai"

    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": input_text}],
        max_tokens=1024,
    )
    return response.choices[0].message.content


async def openai_streaming_handler(input_text: str) -> AsyncIterator[str]:
    """Streaming OpenAI handler."""
    try:
        from openai import AsyncOpenAI
    except ImportError:
        yield "Error: uv pip install openai"
        return

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


# =============================================================================
# Example 3: Google (Gemini)
# =============================================================================

async def gemini_handler(input_text: str) -> str:
    """Simple Gemini handler."""
    try:
        import google.generativeai as genai
    except ImportError:
        return "Error: uv pip install google-generativeai"

    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = await model.generate_content_async(input_text)
    return response.text


# =============================================================================
# Main: Run Selected Provider
# =============================================================================

PROVIDERS = {
    "claude": {
        "handler": claude_handler,
        "streaming_handler": claude_streaming_handler,
        "name": "Claude Agent",
        "description": "AI assistant powered by Claude",
        "env_key": "ANTHROPIC_API_KEY",
    },
    "openai": {
        "handler": openai_handler,
        "streaming_handler": openai_streaming_handler,
        "name": "OpenAI Agent",
        "description": "AI assistant powered by GPT-4",
        "env_key": "OPENAI_API_KEY",
    },
    "gemini": {
        "handler": gemini_handler,
        "streaming_handler": None,  # Gemini streaming is different
        "name": "Gemini Agent",
        "description": "AI assistant powered by Gemini",
        "env_key": "GOOGLE_API_KEY",
    },
}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run LLM agent as A2A service")
    parser.add_argument(
        "--provider",
        choices=list(PROVIDERS.keys()),
        default="claude",
        help="LLM provider to use (default: claude)",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Enable streaming mode",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("AGENT_PORT", "8100")),
        help="Port to run on (default: 8100)",
    )
    args = parser.parse_args()

    provider = PROVIDERS[args.provider]

    # Check API key
    if not os.environ.get(provider["env_key"]):
        print(f"Warning: {provider['env_key']} not set")

    # Select handler
    if args.stream and provider["streaming_handler"]:
        handler = provider["streaming_handler"]
        streaming = True
        print(f"Using {args.provider} with streaming")
    else:
        handler = provider["handler"]
        streaming = False
        print(f"Using {args.provider}")

    # Define skills
    skills = [
        AgentSkill(
            id=f"{args.provider}.assistant",
            name="AI Assistant",
            description=provider["description"],
            tags=[args.provider, "ai", "assistant"],
        ),
    ]

    # Create and run server
    server = expose_as_a2a(
        name=provider["name"],
        handler=handler,
        port=args.port,
        description=provider["description"],
        skills=skills,
        streaming=streaming,
    )

    print(f"\nStarting {provider['name']} on port {args.port}")
    print(f"Agent Card: http://localhost:{args.port}/.well-known/agent.json")
    print("\nPress Ctrl+C to stop\n")

    server.run_sync()


if __name__ == "__main__":
    main()
