"""
Example: Working with the new AgentMessage Format

This example demonstrates how agents can work with the new AgentMessage format
for flexible inter-agent communication.

The key principle:
- AIP handles routing, payment, and logging
- Agents handle understanding the user's intent

AgentMessage format:
{
    "intent": "raw user request (text or JSON)",
    "context": {
        "run_id": "...",
        "caller_id": "...",
        "conversation_id": "...",
        "payment_authorized": true
    },
    "hints": {  # Optional - from routing
        "detected_category": "...",
        "extracted_entities": {...},
        "confidence": 0.9
    },
    "structured_data": {...}  # Optional
}
"""

import asyncio
import json
from typing import AsyncIterator

# Google A2A types
from a2a.types import (
    AgentCard,
    AgentSkill,
    AgentCapabilities,
    Task,
    Message,
    Role,
)
from a2a.client.helpers import create_text_message_object

# Unibase SDK types
from unibase_agent_sdk.a2a import (
    A2AServer,
    StreamResponse,
    AgentMessage,  # The new message format
)


# =============================================================================
# Example 1: Simple handler using AgentMessage
# =============================================================================

def create_calculator_agent():
    """Create a calculator agent that parses intent from AgentMessage."""

    async def task_handler(task: Task, message: Message) -> AsyncIterator[StreamResponse]:
        # Parse the message using AgentMessage format
        # This handles both new and legacy formats automatically
        agent_message = AgentMessage.from_a2a_message(message)

        # Get the user's intent
        intent = agent_message.intent

        # Log context for debugging
        print(f"Processing request:")
        print(f"  Intent: {intent}")
        print(f"  Run ID: {agent_message.context.run_id}")
        print(f"  Caller: {agent_message.context.caller_id}")

        # Check if routing hints suggest this is a math query
        if agent_message.hints:
            print(f"  Detected category: {agent_message.hints.detected_category}")
            entities = agent_message.hints.extracted_entities
            if "expression" in entities:
                print(f"  Extracted expression: {entities['expression']}")

        # Agent handles understanding the intent
        # This could use regex, LLM, or structured parsing
        try:
            # Try to extract math expression from intent
            expression = _extract_expression(intent, agent_message.hints)
            result = eval(expression, {"__builtins__": {}}, {})
            response = f"Result: {expression} = {result}"
        except Exception as e:
            response = f"Could not evaluate expression: {e}"

        # Return response
        msg = create_text_message_object(Role.agent, response)
        yield StreamResponse(message=msg)

    def _extract_expression(intent: str, hints) -> str:
        """Extract math expression from intent."""
        # First, check if hints already extracted the expression
        if hints and hints.extracted_entities:
            if "expression" in hints.extracted_entities:
                return hints.extracted_entities["expression"]

        # Otherwise, try to parse from intent
        # Simple approach: look for patterns like "calculate X" or "what is X"
        import re
        patterns = [
            r"calculate\s+(.+)",
            r"what\s+is\s+(.+)",
            r"evaluate\s+(.+)",
            r"^([\d\s+\-*/().]+)$",
        ]
        for pattern in patterns:
            match = re.search(pattern, intent.lower())
            if match:
                return match.group(1).strip()

        # Fallback: try the whole intent as expression
        return intent.strip()

    # Create agent card
    agent_card = AgentCard(
        name="Calculator Agent",
        description="Evaluates math expressions. Understands intent from AgentMessage format.",
        url="http://localhost:8100",
        version="2.0.0",
        skills=[
            AgentSkill(
                id="calculator.compute",
                name="Calculate",
                description="Evaluate mathematical expressions",
                tags=["math", "calculator"],
            )
        ],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text/plain", "application/json"],
        default_output_modes=["text/plain"],
    )

    return A2AServer(
        agent_card=agent_card,
        task_handler=task_handler,
        host="0.0.0.0",
        port=8100,
    )


# =============================================================================
# Example 2: Agent using structured data
# =============================================================================

def create_weather_agent():
    """Create a weather agent that can use structured data if provided."""

    async def task_handler(task: Task, message: Message) -> AsyncIterator[StreamResponse]:
        agent_message = AgentMessage.from_a2a_message(message)

        # Check if structured data was provided (from advanced callers)
        if agent_message.structured_data:
            location = agent_message.structured_data.get("location")
            days = agent_message.structured_data.get("days", 1)
            print(f"Using structured data: location={location}, days={days}")
        else:
            # Parse from natural language intent
            location = _extract_location(agent_message.intent, agent_message.hints)
            days = 1

        # Generate weather response (mock)
        response = f"Weather forecast for {location}:\n"
        for i in range(days):
            response += f"  Day {i+1}: Sunny, 72°F\n"

        msg = create_text_message_object(Role.agent, response)
        yield StreamResponse(message=msg)

    def _extract_location(intent: str, hints) -> str:
        """Extract location from intent."""
        # Check hints first
        if hints and hints.extracted_entities:
            if "location" in hints.extracted_entities:
                return hints.extracted_entities["location"]

        # Simple extraction from intent
        import re
        patterns = [
            r"weather\s+(?:in|for|at)\s+(.+)",
            r"forecast\s+(?:for|in)\s+(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, intent.lower())
            if match:
                return match.group(1).strip().title()

        return "Unknown Location"

    agent_card = AgentCard(
        name="Weather Agent",
        description="Get weather forecasts. Accepts both natural language and structured data.",
        url="http://localhost:8101",
        version="2.0.0",
        skills=[
            AgentSkill(
                id="weather.forecast",
                name="Weather Forecast",
                description="Get weather forecast for a location",
                tags=["weather", "forecast"],
            )
        ],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text/plain", "application/json"],
        default_output_modes=["text/plain"],
    )

    return A2AServer(
        agent_card=agent_card,
        task_handler=task_handler,
        host="0.0.0.0",
        port=8101,
    )


# =============================================================================
# Example 3: Agent with context awareness
# =============================================================================

def create_context_aware_agent():
    """Create an agent that uses context for personalized responses."""

    # Simple in-memory conversation history
    conversations = {}

    async def task_handler(task: Task, message: Message) -> AsyncIterator[StreamResponse]:
        agent_message = AgentMessage.from_a2a_message(message)

        # Get conversation context
        conversation_id = agent_message.context.conversation_id
        caller_id = agent_message.context.caller_id

        # Track conversation history
        if conversation_id:
            if conversation_id not in conversations:
                conversations[conversation_id] = []
            conversations[conversation_id].append(agent_message.intent)
            history = conversations[conversation_id]
            turn_count = len(history)
        else:
            history = []
            turn_count = 1

        # Generate context-aware response
        response = f"Hello {caller_id}!\n"
        response += f"This is turn #{turn_count} of our conversation.\n"
        response += f"You said: {agent_message.intent}\n"

        if turn_count > 1:
            response += f"Previous messages: {history[:-1]}"

        msg = create_text_message_object(Role.agent, response)
        yield StreamResponse(message=msg)

    agent_card = AgentCard(
        name="Context-Aware Agent",
        description="An agent that maintains conversation context.",
        url="http://localhost:8102",
        version="2.0.0",
        skills=[
            AgentSkill(
                id="chat.respond",
                name="Chat",
                description="Have a conversation with context awareness",
                tags=["chat", "conversation"],
            )
        ],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
    )

    return A2AServer(
        agent_card=agent_card,
        task_handler=task_handler,
        host="0.0.0.0",
        port=8102,
    )


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import sys

    agents = {
        "calculator": ("Calculator Agent", create_calculator_agent, 8100),
        "weather": ("Weather Agent", create_weather_agent, 8101),
        "context": ("Context-Aware Agent", create_context_aware_agent, 8102),
    }

    if len(sys.argv) < 2:
        print("Usage: python agent_message_format.py <agent_name>")
        print("\nAvailable agents:")
        for name, (desc, _, port) in agents.items():
            print(f"  {name}: {desc} (port {port})")
        print("\nExample:")
        print("  python agent_message_format.py calculator")
        sys.exit(1)

    choice = sys.argv[1].lower()
    if choice in agents:
        desc, factory, port = agents[choice]
        server = factory()
        print(f"\n=== Starting {desc} ===")
        print(f"Agent Card: http://localhost:{port}/.well-known/agent.json")
        print(f"\nThis agent uses the new AgentMessage format for flexible communication.")
        print("It handles both natural language and structured requests.\n")
        asyncio.run(server.run())
    else:
        print(f"Unknown agent: {choice}")
        sys.exit(1)
