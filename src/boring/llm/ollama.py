"""
Ollama Provider Implementation
"""

import json
from pathlib import Path

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
        log_dir: Path | None = None,
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
        except Exception:
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
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Writes complete code to a file. Use this for new files or rewrites.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Relative path to the file, e.g., src/main.py",
                            },
                            "content": {
                                "type": "string",
                                "description": "Complete code content to write.",
                            },
                        },
                        "required": ["file_path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_replace",
                    "description": "Perform a targeted search-and-replace on an existing file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Relative path to the file to modify",
                            },
                            "search": {
                                "type": "string",
                                "description": "Exact text to search for (must match exactly)",
                            },
                            "replace": {
                                "type": "string",
                                "description": "Text to replace the search text with",
                            },
                        },
                        "required": ["file_path", "search", "replace"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "report_status",
                    "description": "Report the current task status.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "description": "IN_PROGRESS or COMPLETE",
                            },
                            "tasks_completed": {
                                "type": "integer",
                                "description": "Number of tasks completed in this loop",
                            },
                            "files_modified": {
                                "type": "integer",
                                "description": "Number of files modified",
                            },
                            "exit_signal": {
                                "type": "boolean",
                                "description": "True only if all tasks are complete",
                            },
                        },
                        "required": [
                            "status",
                            "tasks_completed",
                            "files_modified",
                            "exit_signal",
                        ],
                    },
                },
            },
        ]

        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.7,
        }

        try:
            url = f"{self.base_url}/v1/chat/completions"
            if "/v1" in self.base_url:
                url = f"{self.base_url}/chat/completions"

            response = requests.post(url, json=payload, timeout=timeout_seconds)
            if response.status_code != 200:
                log_status(
                    self.log_dir,
                    "ERROR",
                    f"Ollama tool call error {response.status_code}: {response.text}",
                )
                raise RuntimeError(response.text)

            data = response.json()
            message = data["choices"][0]["message"]
            content = message.get("content") or ""

            function_calls = []
            for call in message.get("tool_calls", []) or []:
                fn = call.get("function", {}) or {}
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}
                function_calls.append({"name": fn.get("name", ""), "args": args})

            return LLMResponse(
                text=content,
                function_calls=function_calls,
                success=True,
                error=None,
                metadata={"provider": "ollama", "mode": "openai_compat"},
            )
        except Exception as e:
            log_status(self.log_dir, "ERROR", f"Ollama tool call request failed: {e}")
            text, success = self.generate(prompt, context, timeout_seconds)
            return LLMResponse(
                text=text,
                function_calls=[],
                success=success,
                error=None if success else text,
                metadata={"provider": "ollama", "mode": "fallback"},
            )
