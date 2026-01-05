"""
OpenAI Compatible Provider (LM Studio, vLLM, etc.)
"""

from pathlib import Path
from typing import Optional

import requests

from ..logger import log_status
from .provider import LLMProvider, LLMResponse


class OpenAICompatProvider(LLMProvider):
    """
    Provider for OpenAI-compatible APIs (LM Studio, vLLM, etc.)
    """

    def __init__(
        self,
        model_name: str,
        base_url: str = "http://localhost:1234/v1",
        api_key: str = "lm-studio",
        log_dir: Optional[Path] = None,
    ):
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.log_dir = log_dir or Path("logs")

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider_name(self) -> str:
        return "openai_compat"

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def is_available(self) -> bool:
        """Check if server is reachable."""
        try:
            # Most OpenAI compat servers have a /v1/models endpoint
            url = f"{self.base_url}/models"
            if "/v1" not in self.base_url:
                url = f"{self.base_url}/v1/models"

            resp = requests.get(url, timeout=2)
            return resp.status_code == 200
        except:
            return False

    def generate(
        self, prompt: str, context: str = "", timeout_seconds: int = 300
    ) -> tuple[str, bool]:
        """Generate text."""
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        try:
            url = f"{self.base_url}/chat/completions"
            if "/v1" not in self.base_url:
                url = f"{self.base_url}/v1/chat/completions"

            response = requests.post(url, headers=headers, json=payload, timeout=timeout_seconds)

            if response.status_code != 200:
                log_status(
                    self.log_dir, "ERROR", f"API error {response.status_code}: {response.text}"
                )
                return f"Error: {response.text}", False

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content, True

        except Exception as e:
            log_status(self.log_dir, "ERROR", f"Request failed: {e}")
            return str(e), False

    def generate_with_tools(
        self, prompt: str, context: str = "", timeout_seconds: int = 300
    ) -> LLMResponse:
        """
        Generate with tools using OpenAI format.
        """
        # Improved tool support implementation would go here
        # For now, fallback to text only as most local models struggle with function calling structure
        text, success = self.generate(prompt, context, timeout_seconds)
        return LLMResponse(
            text=text,
            function_calls=[],
            success=success,
            error=None if success else text,
            metadata={"provider": "openai_compat"},
        )
