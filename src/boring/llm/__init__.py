"""
LLM Module - Modular Client Architecture
"""

from pathlib import Path
from typing import Optional

from .provider import LLMProvider, LLMResponse
from .gemini import GeminiProvider
from .claude_adapter import ClaudeCLIAdapter
from .ollama import OllamaProvider
from ..config import settings

def get_provider(provider_name: Optional[str] = None, model_name: Optional[str] = None) -> LLMProvider:
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
from .sdk import GeminiClient, create_gemini_client
from .tools import get_boring_tools, SYSTEM_INSTRUCTION_OPTIMIZED
from .executor import ToolExecutor

__all__ = [
    "get_provider",
    "GeminiClient",
    "create_gemini_client",
    "get_boring_tools",
    "SYSTEM_INSTRUCTION_OPTIMIZED",
    "ToolExecutor",
]
