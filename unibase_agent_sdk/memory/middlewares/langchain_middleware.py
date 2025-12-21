"""
LangChain Memory Transparent Middleware

Usage:
    # Initialize
    lc_memory = LangChainMemoryMiddleware(agent_id="my-agent", memory_type="buffer")
    await lc_memory.initialize()
    
    # Use native LangChain Memory API directly!
    lc_memory.save_context(
        {"input": "Hello, I'm Alice"},
        {"output": "Hi Alice! How can I help you?"}
    )
    
    # Load memory variables
    memory_vars = lc_memory.load_memory_variables({})
    chat_history = memory_vars["chat_history"]
    
    # Access chat memory directly
    messages = lc_memory.chat_memory.messages
    
    # Clear memory
    lc_memory.clear()
"""
from typing import Any
from .base import TransparentMemoryMiddleware
from ...core.exceptions import MiddlewareNotAvailableError, ConfigurationError


# Try to import LangChain
try:
    from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False


class LangChainMemoryMiddleware(TransparentMemoryMiddleware):
    """
    LangChain Memory transparent adapter

    You can use it just like a native ConversationBufferMemory:
    - save_context(inputs, outputs)
    - load_memory_variables(inputs)
    - clear()
    - chat_memory.messages
    - chat_memory.add_user_message(message)
    - chat_memory.add_ai_message(message)
    
    All native LangChain Memory APIs remain available.
    """
    
    async def _initialize_middleware(self) -> Any:
        """Initialize the LangChain Memory instance"""
        if not HAS_LANGCHAIN:
            raise MiddlewareNotAvailableError("langchain", "pip install langchain")
        
        memory_type = self.config.get("memory_type", "buffer")
        
        if memory_type == "buffer":
            return ConversationBufferMemory(
                memory_key=self.config.get("memory_key", "chat_history"),
                return_messages=self.config.get("return_messages", True),
                **self.config.get("extra_params", {})
            )
        elif memory_type == "summary":
            # Summary memory requires an LLM
            llm = self.config.get("llm")
            if not llm:
                raise ValueError("ConversationSummaryMemory requires 'llm' in config")
            return ConversationSummaryMemory(
                llm=llm,
                memory_key=self.config.get("memory_key", "chat_history"),
                **self.config.get("extra_params", {})
            )
        else:
            # Default to buffer
            return ConversationBufferMemory(
                memory_key=self.config.get("memory_key", "chat_history"),
                return_messages=True
            )
    
