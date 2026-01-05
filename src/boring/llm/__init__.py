"""
LLM Module - Modular Client Architecture
"""

from typing import Optional

from ..config import settings
from .claude_adapter import ClaudeCLIAdapter
from .gemini import GeminiProvider
from .ollama import OllamaProvider
from .provider import LLMProvider, LLMResponse


def get_provider(
    provider_name: Optional[str] = None, model_name: Optional[str] = None
) -> LLMProvider:
    """
    Factory function to get the appropriate LLM provider.

    Discovery Priority:
    1. Specified provider_name
    2. settings.LLM_PROVIDER
    3. Auto-discovery
    """
    provider_name = provider_name or settings.LLM_PROVIDER

    if provider_name == "claude-code":
        return ClaudeCLIAdapter(model_name=model_name)

    if provider_name == "ollama":
        return OllamaProvider(model_name=model_name or "llama3")

    # Default to Gemini (handles both SDK and CLI internally)
    return GeminiProvider(model_name=model_name)


# For backward compatibility
from .executor import ToolExecutor
from .sdk import GeminiClient, create_gemini_client
from .tools import SYSTEM_INSTRUCTION_OPTIMIZED, get_boring_tools

__all__ = [
    "get_provider",
    "GeminiClient",
    "create_gemini_client",
    "get_boring_tools",
    "SYSTEM_INSTRUCTION_OPTIMIZED",
    "ToolExecutor",
    "LLMResponse",
]
