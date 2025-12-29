"""Weather Agent - A2A compatible weather forecasting agent.

This agent provides weather forecasts for locations using the Unibase Agent SDK
and A2A protocol.

Environment Variables:
    - AIP_ENDPOINT: AIP platform URL (auto-detected from config)
    - MEMBASE_ENDPOINT: Membase URL (auto-detected from config)
    - AGENT_PORT: Port to run the agent on (default: 8001)
    - AIP_ENVIRONMENT: Deployment environment (local, staging, production)
"""

import asyncio
import os
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


class WeatherAgent:
    """Weather forecasting agent compatible with AIP."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    async def handle_task(self, task: Task, message: Message) -> AsyncIterator[StreamResponse]:
        """Handle weather forecast requests.

        Expected input format: "Weather for <location> for <days> days"
        """
        # Extract text from message
        input_text = ""
        for part in message.parts:
            if isinstance(part, TextPart):
                input_text += part.text

        # Parse location and days
        location = "San Francisco"  # Default
        days = 3  # Default

        # Try to extract location
        location_match = re.search(r"(?:weather (?:for|in) )([^,]+?)(?:\s+for|\s+\d+|$)", input_text, re.IGNORECASE)
        if location_match:
            location = location_match.group(1).strip()

        # Try to extract days
        days_match = re.search(r"(\d+)\s*days?", input_text, re.IGNORECASE)
        if days_match:
            days = min(int(days_match.group(1)), 7)  # Cap at 7 days

        # Generate mock weather forecast
        forecast = self._generate_forecast(location, days)

        # Format response
        response_text = self._format_forecast(forecast)

        # Yield response message
        yield StreamResponse(message=Message.agent(response_text))

    def _generate_forecast(self, location: str, days: int) -> dict:
        """Generate mock weather forecast data."""
        return {
            "location": location,
            "current": {
                "temperature": "72°F",
                "condition": "Partly Cloudy",
                "humidity": "65%",
                "wind": "10 mph"
            },
            "forecast": [
                {
                    "day": f"Day {i+1}",
                    "high": f"{70 + i*2}°F",
                    "low": f"{55 + i}°F",
                    "condition": "Sunny" if i % 2 == 0 else "Partly Cloudy"
                }
                for i in range(min(days, 7))
            ]
        }

    def _format_forecast(self, forecast: dict) -> str:
        """Format forecast data as readable text."""
        lines = [
            f"Weather Forecast for {forecast['location']}",
            "",
            "Current Conditions:",
            f"  Temperature: {forecast['current']['temperature']}",
            f"  Condition: {forecast['current']['condition']}",
            f"  Humidity: {forecast['current']['humidity']}",
            f"  Wind: {forecast['current']['wind']}",
            "",
            "Forecast:",
        ]

        for day_data in forecast['forecast']:
            lines.append(
                f"  {day_data['day']}: {day_data['condition']}, "
                f"High: {day_data['high']}, Low: {day_data['low']}"
            )

        return "\n".join(lines)


async def create_weather_agent(registry: AgentRegistry) -> tuple[AgentCard, WeatherAgent]:
    """Create and register weather agent with A2A support."""

    # Register agent with registry
    identity = await registry.register_agent(
        name="Weather Agent",
        agent_type=AgentType.CUSTOM,
        metadata={
            "description": "Provides weather forecasts and current conditions for locations",
            "capabilities": ["weather", "forecasting"],
            "version": "1.0.0"
        }
    )

    # Create agent instance
    agent = WeatherAgent(identity.agent_id)

    # Generate Agent Card for A2A
    agent_card = AgentCard(
        name="Weather Agent",
        description="Provides weather forecasts and current conditions for locations",
        url="http://localhost:8001",  # Will be overridden when running
        version="1.0.0",
        skills=[
            Skill(
                id="weather.forecast",
                name="Weather Forecast",
                description="Provide weather forecasts and current conditions for locations",
                tags=["weather", "forecast", "climate"],
                examples=[
                    "Weather for San Francisco for 5 days",
                    "What's the weather in Tokyo?",
                    "Weather forecast for London"
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
    """Run weather agent as standalone A2A server."""
    print("=" * 70)
    print("🌤️  Weather Agent - Unibase Agent SDK")
    print("=" * 70)

    # Create registry - URLs auto-detected from environment or config
    registry = AgentRegistry()

    # Create agent
    agent_card, agent = await create_weather_agent(registry)

    # Update URL for this server
    port = int(os.environ.get("AGENT_PORT", "8001"))
    host = os.environ.get("AGENT_HOST", "localhost")
    agent_card.url = f"http://{host}:{port}"

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
        print("\n\n👋 Weather Agent stopped")

    await registry.close()


if __name__ == "__main__":
    asyncio.run(main())
