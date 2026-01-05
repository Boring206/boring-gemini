"""
LLM Provider Abstraction
"""

from abc import abstractmethod

from ..interfaces import LLMClient, LLMResponse


class LLMProvider(LLMClient):
    """
    Extended LLM Client interface that allows for more flexible configuration
    and swapping of backends (Gemini, Ollama, LMStudio, etc.)
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the specific model being used"""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider/CLI is available and configured"""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        context: str = "",
        system_instruction: str = "",
        timeout_seconds: int = 600,
    ) -> tuple[str, bool]:
        """Generate text from prompt and context."""
        pass

    @abstractmethod
    def generate_with_tools(
        self,
        prompt: str,
        context: str = "",
        system_instruction: str = "",
        timeout_seconds: int = 600,
    ) -> LLMResponse:
        """Generate text and/or function calls."""
        pass

    def get_token_usage(self) -> dict[str, int]:
        """Return token usage statistics if available"""
        return {}
