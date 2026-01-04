"""
LLM Module - Modular Client Architecture

This package contains the Gemini SDK integration split into:
- sdk.py: Core API client with retry logic
- tools.py: Function calling definitions
- executor.py: Tool execution logic
"""

from .sdk import GeminiClient, create_gemini_client
from .tools import get_boring_tools, SYSTEM_INSTRUCTION_OPTIMIZED
from .executor import ToolExecutor

__all__ = [
    "GeminiClient",
    "create_gemini_client",
    "get_boring_tools",
    "SYSTEM_INSTRUCTION_OPTIMIZED",
    "ToolExecutor",
]
