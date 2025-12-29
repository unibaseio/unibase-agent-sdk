"""
Example: Wrap ANY Agent as A2A Service

This example demonstrates how to use the generic wrappers to expose
any existing agent/function as an A2A-compatible service.

No framework-specific code required!
"""

import asyncio


# =============================================================================
# Example 1: Simple Function
# =============================================================================

def example_simple_function():
    """Wrap a simple function as an A2A agent."""
    from unibase_agent_sdk import expose_as_a2a

    def echo(text: str) -> str:
        return f"Echo: {text}"

    server = expose_as_a2a(
        name="EchoAgent",
        handler=echo,
        port=8100,
        description="Simple echo agent that repeats your message",
    )

    print("Starting EchoAgent on http://localhost:8100")
    print("Agent Card: http://localhost:8100/.well-known/agent.json")
    server.run_sync()


# =============================================================================
# Example 2: Async Function (e.g., LLM call)
# =============================================================================

async def example_async_function():
    """Wrap an async function as an A2A agent."""
    from unibase_agent_sdk import expose_as_a2a

    async def process(text: str) -> str:
        # Simulate async LLM call
        await asyncio.sleep(0.1)
        return f"Processed: {text.upper()}"

    server = expose_as_a2a(
        name="ProcessorAgent",
        handler=process,
        port=8101,
        description="Async processor agent",
    )

    print("Starting ProcessorAgent on http://localhost:8101")
    await server.run()


# =============================================================================
# Example 3: Wrap Existing Class-Based Agent
# =============================================================================

def example_class_agent():
    """Wrap a class-based agent using AgentWrapper."""
    from unibase_agent_sdk import wrap_agent

    class MyAgent:
        def __init__(self, prefix: str = "Result"):
            self.prefix = prefix

        def process(self, text: str) -> str:
            """Process input and return result."""
            return f"{self.prefix}: {text}"

        def summarize(self, text: str) -> str:
            """Summarize the input text."""
            return f"Summary: {text[:50]}..."

    # Create agent instance
    agent = MyAgent(prefix="Processed")

    # Wrap with specific method
    wrapper = wrap_agent(
        agent=agent,
        name="MyAgent",
        method="process",  # Use the 'process' method as handler
    )

    print("Starting MyAgent on http://localhost:8102")
    wrapper.serve_sync(port=8102)


# =============================================================================
# Example 4: Wrap LangChain Agent (pseudo-code)
# =============================================================================

def example_langchain_agent():
    """
    Example of wrapping a LangChain agent.

    This is pseudo-code - requires langchain installed.
    """
    from unibase_agent_sdk import expose_as_a2a

    # Pseudo-code: Create LangChain agent
    # from langchain.agents import AgentExecutor, create_react_agent
    # agent = AgentExecutor(...)

    # Wrap with a lambda that extracts the output
    # server = expose_as_a2a(
    #     name="LangChainAgent",
    #     handler=lambda text: agent.invoke({"input": text})["output"],
    #     port=8103,
    # )
    # await server.run()

    print("LangChain example - requires langchain installed")


# =============================================================================
# Example 5: Multi-Skill Agent
# =============================================================================

def example_multi_skill():
    """Create an agent with multiple skills."""
    from unibase_agent_sdk import AgentWrapper, Skill

    class MultiSkillAgent:
        def calculate(self, expression: str) -> str:
            """Evaluate a math expression."""
            try:
                result = eval(expression)
                return f"Result: {result}"
            except Exception as e:
                return f"Error: {e}"

        def translate(self, text: str) -> str:
            """Translate text (mock)."""
            return f"Translated: {text} -> [translation]"

    agent = MultiSkillAgent()

    wrapper = AgentWrapper(
        agent=agent,
        name="MultiSkillAgent",
        skill_methods={
            "calculator": "calculate",
            "translator": "translate",
        },
        description="Agent with multiple skills",
    )

    print("Starting MultiSkillAgent on http://localhost:8104")
    wrapper.serve_sync(port=8104)


# =============================================================================
# Example 6: Custom Skills Definition
# =============================================================================

def example_custom_skills():
    """Create an agent with custom skill definitions."""
    from unibase_agent_sdk import expose_as_a2a, Skill

    def weather(location: str) -> str:
        return f"Weather in {location}: Sunny, 72F"

    # Define skills explicitly
    skills = [
        Skill(
            id="weather.forecast",
            name="Weather Forecast",
            description="Get weather forecast for a location",
            tags=["weather", "forecast"],
            examples=["What's the weather in NYC?", "Weather forecast for London"],
        )
    ]

    server = expose_as_a2a(
        name="WeatherAgent",
        handler=weather,
        port=8105,
        skills=skills,
        description="Get weather forecasts for any location",
    )

    print("Starting WeatherAgent on http://localhost:8105")
    server.run_sync()


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import sys

    examples = {
        "1": ("Simple Function", example_simple_function),
        "2": ("Async Function", lambda: asyncio.run(example_async_function())),
        "3": ("Class Agent", example_class_agent),
        "4": ("LangChain (pseudo)", example_langchain_agent),
        "5": ("Multi-Skill", example_multi_skill),
        "6": ("Custom Skills", example_custom_skills),
    }

    if len(sys.argv) < 2:
        print("Usage: python wrap_any_agent.py <example_number>")
        print("\nAvailable examples:")
        for num, (name, _) in examples.items():
            print(f"  {num}: {name}")
        sys.exit(1)

    choice = sys.argv[1]
    if choice in examples:
        name, func = examples[choice]
        print(f"\n=== Running Example: {name} ===\n")
        func()
    else:
        print(f"Unknown example: {choice}")
        sys.exit(1)
