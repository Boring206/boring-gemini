"""
LLM Provider Factory for Judge
"""

from ..cli_client import create_cli_adapter
from ..config import settings
from ..llm.ollama import OllamaProvider
from ..llm.openai_compat import OpenAICompatProvider
from ..llm.provider import LLMProvider


def create_judge_provider() -> LLMProvider:
    """Factory to create the appropriate LLM provider based on config."""
    provider_type = settings.LLM_PROVIDER.lower()

    if provider_type == "ollama":
        return OllamaProvider(
            model_name=settings.LLM_MODEL or "llama3",
            base_url=settings.LLM_BASE_URL or "http://localhost:11434",
            log_dir=settings.LOG_DIR,
        )
    elif provider_type == "openai_compat" or provider_type == "lmstudio":
        return OpenAICompatProvider(
            model_name=settings.LLM_MODEL or "local-model",
            base_url=settings.LLM_BASE_URL or "http://localhost:1234/v1",
            log_dir=settings.LOG_DIR,
        )
    else:
        # Default to Gemini (CLI Adapter for now, as Judge typically runs via CLI)
        return create_cli_adapter(model_name=settings.DEFAULT_MODEL, log_dir=settings.LOG_DIR)
