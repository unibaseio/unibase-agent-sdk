"""Research Agent - A2A compatible research and information gathering agent.

This agent performs research on topics and provides structured findings using
the Unibase Agent SDK and A2A protocol.
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


class ResearchAgent:
    """Research agent for investigating topics and gathering information."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    async def handle_task(self, task: Task, message: Message) -> AsyncIterator[StreamResponse]:
        """Handle research requests.

        Expected input: Research request describing topic and optional depth/focus areas.
        """
        # Extract text from message
        input_text = ""
        for part in message.parts:
            if isinstance(part, TextPart):
                input_text += part.text

        # Parse research parameters
        topic = self._extract_topic(input_text)
        depth = self._extract_depth(input_text)

        # Generate research findings
        findings = self._conduct_research(topic, depth)

        # Format response
        response_text = self._format_findings(findings)

        # Yield response message
        yield StreamResponse(message=Message.agent(response_text))

    def _extract_topic(self, text: str) -> str:
        """Extract research topic from input text."""
        # Look for patterns like "research on X", "investigate X", "about X"
        patterns = [
            r"(?:research|investigate|study)(?:\s+on)?\s+(.+?)(?:\s+with|\s+in|\s*$)",
            r"(?:about|regarding)\s+(.+?)(?:\s+with|\s+in|\s*$)",
            r"topic[:\s]+(.+?)(?:\s+with|\s+in|\s*$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                topic = match.group(1).strip()
                # Remove common trailing words
                topic = re.sub(r'\s+(with|in|depth|detail|comprehensive|basic)\s*$', '', topic, flags=re.IGNORECASE)
                return topic

        # Fallback: use first few words or entire text if short
        words = text.split()
        if len(words) <= 5:
            return text
        return " ".join(words[:5])

    def _extract_depth(self, text: str) -> str:
        """Extract research depth from input text."""
        text_lower = text.lower()
        if "comprehensive" in text_lower or "detailed" in text_lower or "in-depth" in text_lower:
            return "comprehensive"
        elif "basic" in text_lower or "simple" in text_lower or "brief" in text_lower:
            return "basic"
        return "detailed"

    def _conduct_research(self, topic: str, depth: str) -> dict:
        """Generate mock research findings."""
        num_points = {"basic": 3, "detailed": 5, "comprehensive": 7}.get(depth, 5)
        num_sources = {"basic": 2, "detailed": 3, "comprehensive": 5}.get(depth, 3)

        return {
            "topic": topic,
            "depth": depth,
            "summary": f"Research summary on {topic}. This topic covers key aspects "
                      f"including fundamental concepts, recent developments, and practical applications.",
            "key_points": [
                f"Key finding #{i+1}: Important aspect of {topic} that demonstrates "
                f"{'fundamental concepts' if i == 0 else 'practical applications' if i == 1 else 'recent developments'}"
                for i in range(num_points)
            ],
            "sources": [
                {
                    "title": f"Source {i+1}: {topic} - {'Overview' if i == 0 else 'Detailed Analysis' if i == 1 else 'Recent Developments'}",
                    "url": f"https://example.com/{topic.replace(' ', '-').lower()}-{i+1}",
                    "relevance": "high" if i < 2 else "medium"
                }
                for i in range(num_sources)
            ],
            "recommendations": [
                f"Consider exploring {topic} in more depth to understand advanced concepts",
                f"Review latest developments in {topic} to stay current",
                f"Connect with experts in the {topic} field for practical insights"
            ]
        }

    def _format_findings(self, findings: dict) -> str:
        """Format research findings as readable text."""
        lines = [
            f"Research Report: {findings['topic']}",
            f"Depth: {findings['depth'].title()}",
            "",
            "Summary:",
            findings['summary'],
            "",
            "Key Findings:",
        ]

        for i, point in enumerate(findings['key_points'], 1):
            lines.append(f"  {i}. {point}")

        lines.extend([
            "",
            "Sources:",
        ])

        for source in findings['sources']:
            lines.append(f"  • {source['title']}")
            lines.append(f"    {source['url']} ({source['relevance']} relevance)")

        lines.extend([
            "",
            "Recommendations:",
        ])

        for i, rec in enumerate(findings['recommendations'], 1):
            lines.append(f"  {i}. {rec}")

        return "\n".join(lines)


async def create_research_agent(registry: AgentRegistry) -> tuple[AgentCard, ResearchAgent]:
    """Create and register research agent with A2A support."""

    # Register agent with registry
    identity = await registry.register_agent(
        name="Research Agent",
        agent_type=AgentType.CUSTOM,
        metadata={
            "description": "Research topics and gather structured information",
            "capabilities": ["research", "analysis", "information-gathering"],
            "version": "1.0.0"
        }
    )

    # Create agent instance
    agent = ResearchAgent(identity.agent_id)

    # Generate Agent Card for A2A
    agent_card = AgentCard(
        name="Research Agent",
        description="Research topics and gather structured information with sources and recommendations",
        url="http://localhost:8002",  # Will be overridden when running
        version="1.0.0",
        skills=[
            Skill(
                id="research.investigate",
                name="Research & Investigation",
                description="Research topics and gather structured information with varying depth levels",
                tags=["research", "analysis", "information", "investigation"],
                examples=[
                    "Research artificial intelligence with comprehensive depth",
                    "Investigate quantum computing",
                    "Study climate change in detail",
                    "Basic research on blockchain technology"
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
    """Run research agent as standalone A2A server."""
    print("=" * 70)
    print("🔍 Research Agent - Unibase Agent SDK")
    print("=" * 70)

    # Create registry
    registry = AgentRegistry(
        aip_endpoint="https://aip.unibase.io",
        membase_endpoint="https://membase.unibase.io",
    )

    # Create agent
    agent_card, agent = await create_research_agent(registry)

    # Update URL for this server
    port = 8002
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
        print("\n\n👋 Research Agent stopped")

    await registry.close()


if __name__ == "__main__":
    asyncio.run(main())
