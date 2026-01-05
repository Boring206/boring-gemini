"""
Gemini Provider Implementation (SDK & CLI fallback)
"""

from pathlib import Path
from typing import Optional

from ..config import settings
from ..logger import get_logger
from .provider import LLMProvider, LLMResponse
from .tools import SYSTEM_INSTRUCTION_OPTIMIZED, get_boring_tools

_logger = get_logger("gemini_provider")

try:
    from google import genai
    from google.genai import types

    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    genai = None
    types = None


class GeminiProvider(LLMProvider):
    """
    Standardized provider for Google Gemini.
    Supports SDK (API Key) and CLI (gcloud/google-auth) backends.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        log_dir: Optional[Path] = None,
    ):
        self._model_name = model_name or settings.DEFAULT_MODEL
        self.log_dir = log_dir or settings.LOG_DIR
        self.api_key = api_key or settings.GOOGLE_API_KEY

        self.backend = "sdk"
        self.cli_adapter = None
        self.client = None

        # Determine backend
        if not self.api_key:
            from ..cli_client import GeminiCLIAdapter, check_cli_available

            if check_cli_available():
                _logger.info("No API key. Using Gemini CLI backend.")
                self.backend = "cli"
                self.cli_adapter = GeminiCLIAdapter(
                    model_name=self._model_name, log_dir=self.log_dir
                )
            else:
                _logger.warning(
                    "No API key and Gemini CLI not found. SDK will fail if no key provided later."
                )

        if self.backend == "sdk" and SDK_AVAILABLE and self.api_key:
            self.client = genai.Client(api_key=self.api_key)

        self.tools = get_boring_tools()
        self.use_function_calling = settings.USE_FUNCTION_CALLING and len(self.tools) > 0

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def is_available(self) -> bool:
        if self.backend == "sdk":
            return SDK_AVAILABLE and bool(self.api_key)
        return self.cli_adapter is not None

    def generate(
        self,
        prompt: str,
        context: str = "",
        system_instruction: str = "",
        timeout_seconds: int = 600,
    ) -> tuple[str, bool]:
        if self.backend == "cli":
            return self.cli_adapter.generate(prompt, context)

        if not self.client:
            return "Error: Gemini SDK not initialized (missing API key)", False

        try:
            full_prompt = f"# Context\n{context}\n\n# Task\n{prompt}" if context else prompt
            contents = [types.Content(role="user", parts=[types.Part(text=full_prompt)])]

            response = self.client.models.generate_content(
                model=self._model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction or SYSTEM_INSTRUCTION_OPTIMIZED,
                    temperature=0.7,
                    max_output_tokens=8192,
                ),
            )
            return response.text or "", True
        except Exception as e:
            _logger.error(f"Gemini SDK error: {e}")
            return str(e), False

    def generate_with_tools(
        self,
        prompt: str,
        context: str = "",
        system_instruction: str = "",
        timeout_seconds: int = 600,
    ) -> LLMResponse:
        if self.backend == "cli":
            res = self.cli_adapter.generate_with_tools(prompt, context)
            return LLMResponse(
                text=res.text,
                function_calls=res.function_calls,
                success=res.success,
                error=None if res.success else res.text,
                metadata={"backend": "cli"},
            )

        if not self.client:
            return LLMResponse(
                text="", function_calls=[], success=False, error="SDK not initialized"
            )

        try:
            full_prompt = f"# Context\n{context}\n\n# Task\n{prompt}" if context else prompt
            contents = [types.Content(role="user", parts=[types.Part(text=full_prompt)])]

            response = self.client.models.generate_content(
                model=self._model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction or SYSTEM_INSTRUCTION_OPTIMIZED,
                    temperature=0.7,
                    max_output_tokens=8192,
                    tools=self.tools if self.use_function_calling else None,
                ),
            )

            function_calls = []
            text_parts = []
            if response.candidates:
                for cand in response.candidates:
                    if cand.content:
                        for part in cand.content.parts:
                            if part.function_call:
                                function_calls.append(
                                    {
                                        "name": part.function_call.name,
                                        "args": dict(part.function_call.args),
                                    }
                                )
                            elif part.text:
                                text_parts.append(part.text)

            return LLMResponse(
                text="\n".join(text_parts),
                function_calls=function_calls,
                success=True,
                metadata={"backend": "sdk"},
            )
        except Exception as e:
            return LLMResponse(text="", function_calls=[], success=False, error=str(e))
