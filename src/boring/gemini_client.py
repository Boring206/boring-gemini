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
from .config import settings
from .llm.executor import ToolExecutor
from .llm.sdk import (
    DEFAULT_MODEL,
    GENAI_AVAILABLE,
    GeminiClient,
    create_gemini_client,
    genai,
)
from .llm.tools import (
    SYSTEM_INSTRUCTION_OPTIMIZED,
    get_boring_tools,
)


# Monkeypatch process_function_calls onto GeminiClient for backward compatibility
def _process_function_calls(self, function_calls, project_root=None):
    # Legacy method signature expected project_root as second argument
    root = project_root or settings.PROJECT_ROOT
    executor = ToolExecutor(root, self.log_dir)
    return executor.process_function_calls(function_calls)


GeminiClient.process_function_calls = _process_function_calls

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
    "genai",
]
