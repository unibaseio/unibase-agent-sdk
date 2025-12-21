"""Calculator Agent - A2A compatible mathematical calculation agent.

This agent performs mathematical calculations and evaluations using the
Unibase Agent SDK and A2A protocol.
"""

import asyncio
import math
import re
from typing import AsyncIterator

from unibase_agent_sdk import AgentRegistry, AgentType
from unibase_agent_sdk.a2a import (
    A2AServer,
    AgentCard,
    Task,
    Message,
    TextPart,
    StreamResponse,
    Skill,
    Capability,
)


class CalculatorAgent:
    """Mathematical calculation agent."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    async def handle_task(self, task: Task, message: Message) -> AsyncIterator[StreamResponse]:
        """Handle calculation requests.

        Expected input: Mathematical expression to evaluate.
        """
        # Extract text from message
        input_text = ""
        for part in message.parts:
            if isinstance(part, TextPart):
                input_text += part.text

        # Extract expression
        expression = self._extract_expression(input_text)

        # Perform calculation
        try:
            result = self._evaluate_expression(expression)
            response_text = f"Calculation Result:\n\nExpression: {expression}\nResult: {result}"
        except Exception as e:
            response_text = f"Calculation Error:\n\nExpression: {expression}\nError: {str(e)}\n\nPlease ensure your expression uses valid mathematical syntax."

        # Yield response message
        yield StreamResponse(message=Message.agent(response_text))

    def _extract_expression(self, text: str) -> str:
        """Extract mathematical expression from input text."""
        # Look for patterns like "calculate X", "evaluate X", "compute X"
        patterns = [
            r"(?:calculate|compute|evaluate|solve)\s+(.+?)(?:\s*$|\s+and\s+|\s+then\s+)",
            r"(?:what is|what's)\s+(.+?)(?:\s*\?|\s*$)",
            r"expression[:\s]+(.+?)(?:\s*$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                expr = match.group(1).strip()
                # Clean up
                expr = expr.rstrip('?.,')
                return expr

        # If no pattern matches, treat entire text as expression
        # Remove common question words
        cleaned = re.sub(r'^(what is|calculate|compute|evaluate|solve)\s+', '', text, flags=re.IGNORECASE)
        cleaned = cleaned.rstrip('?.,').strip()

        return cleaned if cleaned else text

    def _evaluate_expression(self, expression: str) -> float:
        """Safely evaluate mathematical expression."""
        # Define allowed functions and constants
        allowed_names = {
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "asin": math.asin,
            "acos": math.acos,
            "atan": math.atan,
            "sinh": math.sinh,
            "cosh": math.cosh,
            "tanh": math.tanh,
            "pi": math.pi,
            "e": math.e,
            "log": math.log,
            "log10": math.log10,
            "log2": math.log2,
            "exp": math.exp,
            "abs": abs,
            "pow": pow,
            "round": round,
            "floor": math.floor,
            "ceil": math.ceil,
            "degrees": math.degrees,
            "radians": math.radians,
        }

        try:
            # Evaluate with restricted namespace for security
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return result
        except Exception as e:
            raise ValueError(f"Invalid expression: {str(e)}")


async def create_calculator_agent(registry: AgentRegistry) -> tuple[AgentCard, CalculatorAgent]:
    """Create and register calculator agent with A2A support."""

    # Register agent with registry
    identity = await registry.register_agent(
        name="Calculator Agent",
        agent_type=AgentType.CUSTOM,
        metadata={
            "description": "Perform mathematical calculations and evaluations",
            "capabilities": ["mathematics", "computation", "calculation"],
            "version": "1.0.0"
        }
    )

    # Create agent instance
    agent = CalculatorAgent(identity.agent_id)

    # Generate Agent Card for A2A
    agent_card = AgentCard(
        name="Calculator Agent",
        description="Perform mathematical calculations and evaluations including basic and scientific operations",
        url="http://localhost:8004",  # Will be overridden when running
        version="1.0.0",
        skills=[
            Skill(
                id="calculator.compute",
                name="Mathematical Computation",
                description="Evaluate mathematical expressions including basic arithmetic, algebra, and scientific functions",
                tags=["calculator", "math", "computation", "arithmetic", "scientific"],
                examples=[
                    "Calculate 2 + 2",
                    "What is sqrt(144)?",
                    "Evaluate sin(pi/2)",
                    "Compute log(100)",
                    "Calculate (5 + 3) * 2 - 7",
                    "What's the value of e^2?"
                ]
            )
        ],
        capabilities=Capability(
            streaming=True,
            push_notifications=False,
            state_transition_history=True
        )
    )

    return agent_card, agent


async def main():
    """Run calculator agent as standalone A2A server."""
    print("=" * 70)
    print("🔢 Calculator Agent - Unibase Agent SDK")
    print("=" * 70)

    # Create registry
    registry = AgentRegistry(
        aip_endpoint="https://aip.unibase.io",
        membase_endpoint="https://membase.unibase.io",
    )

    # Create agent
    agent_card, agent = await create_calculator_agent(registry)

    # Update URL for this server
    port = 8004
    agent_card.url = f"http://localhost:{port}"

    print(f"\n📝 Agent registered: {agent_card.name}")
    print(f"   Agent ID: {agent.agent_id}")
    print(f"   Skills: {[s.name for s in agent_card.skills]}")

    # Start A2A server
    print(f"\n🚀 Starting A2A Server on port {port}...")
    print(f"   Agent Card: {agent_card.url}/.well-known/agent.json")
    print(f"   A2A Endpoint: {agent_card.url}/a2a")
    print("\n   Press Ctrl+C to stop\n")

    server = A2AServer(
        agent_card=agent_card,
        task_handler=agent.handle_task,
        host="0.0.0.0",
        port=port
    )

    try:
        await server.run()
    except KeyboardInterrupt:
        print("\n\n👋 Calculator Agent stopped")

    await registry.close()


if __name__ == "__main__":
    asyncio.run(main())
