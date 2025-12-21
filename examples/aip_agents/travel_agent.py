"""Travel Agent - A2A compatible travel planning agent.

This agent helps plan travel itineraries including flights, hotels, and activities
using the Unibase Agent SDK and A2A protocol.
"""

import asyncio
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


class TravelAgent:
    """Travel planning agent for itinerary creation and recommendations."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    async def handle_task(self, task: Task, message: Message) -> AsyncIterator[StreamResponse]:
        """Handle travel planning requests.

        Expected input: Travel planning request with destination, dates, budget, and interests.
        """
        # Extract text from message
        input_text = ""
        for part in message.parts:
            if isinstance(part, TextPart):
                input_text += part.text

        # Parse travel parameters
        destination = self._extract_destination(input_text)
        dates = self._extract_dates(input_text)
        budget = self._extract_budget(input_text)
        interests = self._extract_interests(input_text)

        # Generate travel plan
        plan = self._create_travel_plan(destination, dates, budget, interests)

        # Format response
        response_text = self._format_plan(plan)

        # Yield response message
        yield StreamResponse(message=Message.agent(response_text))

    def _extract_destination(self, text: str) -> str:
        """Extract destination from input text."""
        patterns = [
            r"(?:to|in|visit|going to)\s+([A-Z][a-zA-Z\s]+?)(?:\s+for|\s+in|\s+on|\s+with|\s*,|\s*$)",
            r"destination[:\s]+([A-Z][a-zA-Z\s]+?)(?:\s+for|\s+in|\s+on|\s*,|\s*$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return "Paris"  # Default

    def _extract_dates(self, text: str) -> str:
        """Extract travel dates from input text."""
        # Look for month/year patterns
        month_pattern = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})"
        match = re.search(month_pattern, text, re.IGNORECASE)
        if match:
            return f"{match.group(1)} {match.group(2)}"

        # Look for "X days" pattern
        days_pattern = r"(\d+)\s*days?"
        match = re.search(days_pattern, text, re.IGNORECASE)
        if match:
            return f"{match.group(1)} days"

        return "June 2025"  # Default

    def _extract_budget(self, text: str) -> str:
        """Extract budget from input text."""
        pattern = r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)"
        match = re.search(pattern, text)
        if match:
            return f"${match.group(1)}"

        # Check for budget descriptors
        if "budget" in text.lower():
            if "high" in text.lower() or "luxury" in text.lower():
                return "$5000"
            elif "low" in text.lower() or "cheap" in text.lower():
                return "$1000"

        return "$3000"  # Default

    def _extract_interests(self, text: str) -> list:
        """Extract travel interests from input text."""
        interest_keywords = {
            "food": ["food", "dining", "cuisine", "restaurant"],
            "culture": ["culture", "museum", "history", "art"],
            "outdoors": ["outdoor", "hiking", "nature", "adventure"],
            "nightlife": ["nightlife", "bar", "club", "entertainment"],
            "relaxation": ["relax", "spa", "beach", "leisure"],
            "family": ["family", "kids", "children"]
        }

        text_lower = text.lower()
        interests = []

        for interest, keywords in interest_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                interests.append(interest.title())

        return interests if interests else ["Culture", "Food"]

    def _create_travel_plan(self, destination: str, dates: str, budget: str, interests: list) -> dict:
        """Generate mock travel plan."""
        return {
            "destination": destination,
            "dates": dates,
            "budget": budget,
            "interests": interests,
            "recommendations": {
                "flights": [
                    {
                        "carrier": "Sample Airlines",
                        "price": "$850",
                        "duration": "8h 30m",
                        "notes": "Direct flight available"
                    },
                    {
                        "carrier": "Budget Air",
                        "price": "$650",
                        "duration": "12h 15m",
                        "notes": "One stopover"
                    }
                ],
                "hotels": [
                    {
                        "name": f"Grand Hotel {destination}",
                        "location": "City Center",
                        "nightly_rate": "$200",
                        "rating": "4.5/5",
                        "notes": "Centrally located with great reviews"
                    },
                    {
                        "name": f"{destination} Budget Inn",
                        "location": "Near Transit",
                        "nightly_rate": "$80",
                        "rating": "4.0/5",
                        "notes": "Good value, close to public transportation"
                    }
                ],
                "activities": self._generate_activities(destination, interests)
            },
            "summary": f"Complete travel plan for {destination} created successfully"
        }

    def _generate_activities(self, destination: str, interests: list) -> list:
        """Generate activity recommendations based on interests."""
        activities = []

        interest_activities = {
            "Culture": [
                f"Visit the main museums and cultural sites in {destination}",
                f"Take a guided historical walking tour",
                "Attend a local theater or music performance"
            ],
            "Food": [
                f"Try regional cuisine at local restaurants in {destination}",
                "Take a food tour or cooking class",
                "Visit local markets and food halls"
            ],
            "Outdoors": [
                f"Explore parks and outdoor spaces in {destination}",
                "Take a day trip to nearby natural attractions",
                "Rent bikes for city exploration"
            ],
            "Nightlife": [
                "Experience the local nightlife scene",
                "Visit popular bars and entertainment districts",
                "Attend evening cultural events"
            ],
            "Relaxation": [
                "Enjoy spa and wellness facilities",
                "Relax at scenic viewpoints",
                "Visit cafes and peaceful gardens"
            ],
            "Family": [
                "Visit family-friendly attractions and parks",
                "Explore interactive museums",
                "Enjoy kid-friendly restaurants and activities"
            ]
        }

        for interest in interests:
            if interest in interest_activities:
                activities.extend(interest_activities[interest][:2])

        # Add general activities if none specified
        if not activities:
            activities = [
                f"Explore the main attractions of {destination}",
                f"Walking tours around {destination}",
                "Visit local cafes and restaurants"
            ]

        return activities[:6]  # Limit to 6 activities

    def _format_plan(self, plan: dict) -> str:
        """Format travel plan as readable text."""
        lines = [
            f"✈️  Travel Plan: {plan['destination']}",
            "=" * 60,
            f"Dates: {plan['dates']}",
            f"Budget: {plan['budget']}",
            f"Interests: {', '.join(plan['interests'])}",
            "",
            "🛫 Flight Options:",
        ]

        for flight in plan['recommendations']['flights']:
            lines.append(f"  • {flight['carrier']} - {flight['price']}")
            lines.append(f"    Duration: {flight['duration']} - {flight['notes']}")

        lines.extend([
            "",
            "🏨 Hotel Recommendations:",
        ])

        for hotel in plan['recommendations']['hotels']:
            lines.append(f"  • {hotel['name']} ({hotel['rating']})")
            lines.append(f"    {hotel['location']} - {hotel['nightly_rate']}/night")
            lines.append(f"    {hotel['notes']}")

        lines.extend([
            "",
            "🎯 Recommended Activities:",
        ])

        for i, activity in enumerate(plan['recommendations']['activities'], 1):
            lines.append(f"  {i}. {activity}")

        lines.extend([
            "",
            f"Summary: {plan['summary']}"
        ])

        return "\n".join(lines)


async def create_travel_agent(registry: AgentRegistry) -> tuple[AgentCard, TravelAgent]:
    """Create and register travel agent with A2A support."""

    # Register agent with registry
    identity = await registry.register_agent(
        name="Travel Planner Agent",
        agent_type=AgentType.CUSTOM,
        metadata={
            "description": "Plan travel itineraries including flights, hotels, and activities",
            "capabilities": ["planning", "research", "recommendations"],
            "version": "1.0.0"
        }
    )

    # Create agent instance
    agent = TravelAgent(identity.agent_id)

    # Generate Agent Card for A2A
    agent_card = AgentCard(
        name="Travel Planner Agent",
        description="Help plan travel itineraries including flights, hotels, and activities based on preferences",
        url="http://localhost:8003",  # Will be overridden when running
        version="1.0.0",
        skills=[
            Skill(
                id="travel.planning",
                name="Travel Planning",
                description="Create comprehensive travel itineraries with flights, accommodations, and activities",
                tags=["travel", "planning", "itinerary", "vacation", "tourism"],
                examples=[
                    "Plan a trip to Paris in June with $3000 budget",
                    "Travel to Tokyo for 7 days with culture and food interests",
                    "Budget trip to Barcelona with nightlife focus",
                    "Family vacation to Orlando for 5 days"
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
    """Run travel agent as standalone A2A server."""
    print("=" * 70)
    print("✈️  Travel Planner Agent - Unibase Agent SDK")
    print("=" * 70)

    # Create registry
    registry = AgentRegistry(
        aip_endpoint="https://aip.unibase.io",
        membase_endpoint="https://membase.unibase.io",
    )

    # Create agent
    agent_card, agent = await create_travel_agent(registry)

    # Update URL for this server
    port = 8003
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
        print("\n\n👋 Travel Planner Agent stopped")

    await registry.close()


if __name__ == "__main__":
    asyncio.run(main())
