"""
Ollama Provider Implementation
"""

from pathlib import Path
from typing import Optional

import requests

from ..logger import log_status
from .provider import LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    """
    Provider for Ollama (local LLM runner).
    """

    def __init__(
        self,
        model_name: str,
        base_url: str = "http://localhost:11434",
        log_dir: Optional[Path] = None,
    ):
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")
        self.log_dir = log_dir or Path("logs")

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return resp.status_code == 200
        except:
            return False

    def generate(
        self, prompt: str, context: str = "", timeout_seconds: int = 300
    ) -> tuple[str, bool]:
        """Generate text using Ollama."""
        full_prompt = f"{context}\n\n{prompt}" if context else prompt

        try:
            # Using 'generate' endpoint for raw text
            # Or 'chat' endpoint if we want to structure it better
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_ctx": 4096},
            }

            response = requests.post(
                f"{self.base_url}/api/generate", json=payload, timeout=timeout_seconds
            )

            if response.status_code != 200:
                log_status(
                    self.log_dir, "ERROR", f"Ollama error {response.status_code}: {response.text}"
                )
                return f"Error: {response.text}", False

            data = response.json()
            return data.get("response", ""), True

        except Exception as e:
            log_status(self.log_dir, "ERROR", f"Ollama request failed: {e}")
            return str(e), False

    def generate_with_tools(
        self, prompt: str, context: str = "", timeout_seconds: int = 300
    ) -> LLMResponse:
        """
        Generate with tools.
        Note: Ollama has limited tool support for many models.
        We can attempt to use OpenAI-compatibility layer if needed,
        or just rely on the model following instructions if it's smart enough.

        For now, we'll assume no native tool binding support in this basic provider,
        or handle it via text parsing similar to CLI adapter.
        """
        # TODO: Improved tool support for Ollama via OpenAI compat endpoint
        text, success = self.generate(prompt, context, timeout_seconds)
        return LLMResponse(
            text=text,
            function_calls=[],
            success=success,
            error=None if success else text,
            metadata={"provider": "ollama"},
        )
