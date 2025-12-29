"""
Agent Wrappers for Unibase Agent SDK

Provides two approaches for integrating agents with Unibase:

1. Generic Wrapper (expose_as_a2a):
   Wrap ANY callable/agent as an A2A-compatible service.

   Example:
       from unibase_agent_sdk.wrappers import expose_as_a2a

       def my_handler(text: str) -> str:
           return f"Processed: {text}"

       server = expose_as_a2a("MyAgent", my_handler, port=8100)
       await server.run()

2. Framework-Specific Wrappers:
   Native wrappers for popular frameworks (CrewAI, AutoGen, etc.)

   Example:
       from unibase_agent_sdk.wrappers import CrewAIWrapper

       wrapper = CrewAIWrapper(my_crewai_agent, registry=registry)
       await wrapper.serve(port=8100)
"""

from unibase_agent_sdk.wrappers.generic import (
    expose_as_a2a,
    wrap_agent,
    AgentWrapper,
)

__all__ = [
    "expose_as_a2a",
    "wrap_agent",
    "AgentWrapper",
]
