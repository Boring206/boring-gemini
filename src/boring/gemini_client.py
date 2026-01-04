"""
Gemini SDK Client for Boring (V10.1 - Modular)

This module now re-exports from the modular boring.llm package
for backwards compatibility with existing code.

The actual implementation is in:
- boring.llm.sdk: GeminiClient core
- boring.llm.tools: Function calling definitions
- boring.llm.executor: Tool execution logic
"""

# Re-export everything from new modular structure
from .llm.sdk import (
    GeminiClient,
    create_gemini_client,
    DEFAULT_MODEL,
    GENAI_AVAILABLE,
)
from .llm.tools import (
    get_boring_tools,
    SYSTEM_INSTRUCTION_OPTIMIZED,
)
from .llm.executor import ToolExecutor

# Backwards compatibility: process_function_calls as method
# For code that does: client.process_function_calls(...)
# They should now use: ToolExecutor(project_root).process_function_calls(...)

__all__ = [
    "GeminiClient",
    "create_gemini_client",
    "get_boring_tools",
    "SYSTEM_INSTRUCTION_OPTIMIZED",
    "ToolExecutor",
    "DEFAULT_MODEL",
    "GENAI_AVAILABLE",
]
