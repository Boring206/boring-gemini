"""
Gemini SDK Client for Boring (V10 Modular Architecture)

Core client implementation with:
- Stateless client architecture (google-genai)
- Retry logic with exponential backoff
- Support for both sync and async generation

This module is imported by boring.gemini_client for backwards compatibility.
"""

import os
import time
from pathlib import Path
from typing import Any, Optional

# New unified SDK imports
try:
    from google import genai
    from google.genai import types

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    types = None

from ..config import settings
from ..logger import get_logger, log_status
from .tools import SYSTEM_INSTRUCTION_OPTIMIZED, get_boring_tools

# Structured logger for this module
_logger = get_logger("gemini_client")

# Default model (from settings)
DEFAULT_MODEL = settings.DEFAULT_MODEL


class GeminiClient:
    """
    Lightweight wrapper around the Google Gen AI SDK.

    V10 Changes:
    - Modular architecture (tools and executor separate)
    - Stateless client pattern
    - Updated for google-genai SDK

    Handles:
    - API key configuration
    - Content generation
    - Rate limit handling
    - Error recovery
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
        log_dir: Path = Path("logs"),
    ):
        """
        Initialize the Gemini client.

        Args:
            api_key: Google API key. If None, reads from GOOGLE_API_KEY env var.
            model_name: Gemini model to use.
            log_dir: Directory for logging.
        """
        self.log_dir = log_dir
        self.model_name = model_name

        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-genai package not installed. Install with: pip install google-genai"
            )

        # Get API key (Prioritize arg -> settings -> env)
        self.api_key = api_key or settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY", "")

        self.backend = "sdk"
        self.cli_adapter = None

        if not self.api_key:
            # Fallback to CLI if possible
            from ..cli_client import GeminiCLIAdapter, check_cli_available

            if check_cli_available():
                _logger.info("No API key found. Falling back to Gemini CLI backend.")
                self.backend = "cli"
                self.cli_adapter = GeminiCLIAdapter(
                    model_name=self.model_name, log_dir=self.log_dir
                )
            else:
                raise ValueError(
                    "GOOGLE_API_KEY not set and Gemini CLI not found. "
                    "Please set GOOGLE_API_KEY or install @google/gemini-cli."
                )

        # Initialize SDK client if using SDK backend
        if self.backend == "sdk":
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

        # Get tools for function calling
        self.tools = get_boring_tools()
        self.use_function_calling = len(self.tools) > 0

        log_status(self.log_dir, "INFO", f"Gemini SDK V10 initialized with model: {model_name}")
        if self.use_function_calling:
            log_status(self.log_dir, "INFO", "Function Calling enabled")

    def generate(
        self,
        prompt: str,
        context: str = "",
        system_instruction: str = "",
        timeout_seconds: int = settings.TIMEOUT_MINUTES * 60,
    ) -> tuple[str, bool]:
        """
        Generate content using Gemini.

        Args:
            prompt: The main prompt/instructions
            context: Additional context to prepend
            system_instruction: System-level instructions
            timeout_seconds: Request timeout

        Returns:
            Tuple of (response_text, success_flag)
        """
        # Build the full prompt
        full_prompt_parts = []

        if context:
            full_prompt_parts.append(f"# Context\n{context}")

        full_prompt_parts.append(f"# Task\n{prompt}")

        full_prompt = "\n\n---\n\n".join(full_prompt_parts)

        # Build contents with proper Part objects
        contents = [types.Content(role="user", parts=[types.Part(text=full_prompt)])]

        try:
            if self.backend == "cli":
                return self.cli_adapter.generate(prompt, context)

            # Generate content using stateless client
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction or SYSTEM_INSTRUCTION_OPTIMIZED,
                        temperature=0.7,
                        max_output_tokens=8192,
                    ),
                )
            except Exception as e:
                # Handle Model Not Found (404) with fallback
                if "404" in str(e) or "not found" in str(e).lower():
                    fallback_model = "gemini-1.5-flash"
                    if self.model_name != fallback_model:
                        _logger.warning(
                            f"Model {self.model_name} not found. Falling back to {fallback_model}"
                        )
                        response = self.client.models.generate_content(
                            model=fallback_model,
                            contents=contents,
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction
                                or SYSTEM_INSTRUCTION_OPTIMIZED,
                                temperature=0.7,
                                max_output_tokens=8192,
                            ),
                        )
                    else:
                        raise e
                else:
                    raise e

            # Extract text from response (Pydantic model)
            if response and response.text:
                return response.text, True
            else:
                log_status(self.log_dir, "WARN", "Empty response from Gemini")
                return "", False

        except Exception as e:
            error_str = str(e).lower()
            if "429" in str(e) or "resource_exhausted" in error_str:
                log_status(self.log_dir, "ERROR", f"Rate limit exceeded: {e}")
                return f"RATE_LIMIT_ERROR: {e}", False
            elif "deadline" in error_str or "timeout" in error_str:
                log_status(self.log_dir, "ERROR", f"Request timeout: {e}")
                return f"TIMEOUT_ERROR: {e}", False
            else:
                log_status(self.log_dir, "ERROR", f"Unexpected error: {e}")
                return f"UNEXPECTED_ERROR: {e}", False

    def generate_with_retry(
        self,
        prompt: str,
        context: str = "",
        system_instruction: str = "",
        max_retries: int = 3,
        base_delay: float = 2.0,
    ) -> tuple[str, bool]:
        """
        Generate content with exponential backoff retry.
        """
        for attempt in range(max_retries):
            response, success = self.generate(prompt, context, system_instruction)

            if success:
                return response, True

            # Check if it's a rate limit error or server overloaded
            if (
                "RATE_LIMIT_ERROR" in response
                or "503" in response
                or "overloaded" in str(response).lower()
            ):
                delay = base_delay * (2**attempt)
                log_status(
                    self.log_dir,
                    "WARN",
                    f"Rate limited/Overloaded, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})",
                )
                time.sleep(delay)
                continue

            # For other errors, don't retry
            break

        return response, False

    def generate_with_tools(
        self, prompt: str, context: str = "", timeout_seconds: int = settings.TIMEOUT_MINUTES * 60
    ) -> tuple[str, list[dict[str, Any]], bool]:
        """
        Generate content using Gemini with Function Calling.

        Returns:
            Tuple of (text_response, function_calls, success_flag)
            - text_response: Any text content from the response
            - function_calls: List of dicts with 'name' and 'args' keys
            - success_flag: Whether generation succeeded
        """
        full_prompt_parts = []
        if context:
            full_prompt_parts.append(f"# Context\n{context}")
        full_prompt_parts.append(f"# Task\n{prompt}")
        full_prompt = "\n\n---\n\n".join(full_prompt_parts)

        # Build contents
        contents = [types.Content(role="user", parts=[types.Part(text=full_prompt)])]

        try:
            if self.backend == "cli":
                res = self.cli_adapter.generate_with_tools(prompt, context)
                return res.text, res.function_calls, res.success

            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION_OPTIMIZED,
                        temperature=0.7,
                        max_output_tokens=8192,
                        tools=self.tools if self.use_function_calling else None,
                    ),
                )
            except Exception as e:
                # Handle Model Not Found (404) with fallback
                if "404" in str(e) or "not found" in str(e).lower():
                    fallback_model = "gemini-1.5-flash"
                    if self.model_name != fallback_model:
                        _logger.warning(
                            f"Model {self.model_name} not found in tools call. Falling back to {fallback_model}"
                        )
                        response = self.client.models.generate_content(
                            model=fallback_model,
                            contents=contents,
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_INSTRUCTION_OPTIMIZED,
                                temperature=0.7,
                                max_output_tokens=8192,
                                tools=self.tools if self.use_function_calling else None,
                            ),
                        )
                    else:
                        raise e
                else:
                    raise e

            # Extract function calls and text
            function_calls = []
            text_parts = []

            if response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, "content") and candidate.content:
                        for part in candidate.content.parts:
                            # Check for function call
                            if hasattr(part, "function_call") and part.function_call:
                                fc = part.function_call
                                # Use model_dump() for Pydantic models
                                args = dict(fc.args) if hasattr(fc.args, "__iter__") else {}
                                function_calls.append({"name": fc.name, "args": args})
                            # Check for text
                            elif hasattr(part, "text") and part.text:
                                text_parts.append(part.text)

            text_response = "\n".join(text_parts)

            if function_calls:
                log_status(
                    self.log_dir,
                    "INFO",
                    f"Received {len(function_calls)} function call(s): {[fc['name'] for fc in function_calls]}",
                )

            return text_response, function_calls, True

        except Exception as e:
            error_str = str(e).lower()
            if "429" in str(e) or "resource_exhausted" in error_str:
                log_status(self.log_dir, "ERROR", f"Rate limit exceeded: {e}")
                return f"RATE_LIMIT_ERROR: {e}", [], False
            elif "deadline" in error_str or "timeout" in error_str:
                log_status(self.log_dir, "ERROR", f"Request timeout: {e}")
                return f"TIMEOUT_ERROR: {e}", [], False
            else:
                log_status(self.log_dir, "ERROR", f"Unexpected error in generate_with_tools: {e}")
                return f"UNEXPECTED_ERROR: {e}", [], False


def create_gemini_client(
    log_dir: Path = Path("logs"), model_name: str = DEFAULT_MODEL
) -> Optional[GeminiClient]:
    """
    Factory function to create a GeminiClient.

    Returns None if initialization fails (missing API key, etc.)
    """
    try:
        return GeminiClient(log_dir=log_dir, model_name=model_name)
    except (ImportError, ValueError) as e:
        log_status(log_dir, "ERROR", f"Failed to initialize Gemini client: {e}")
        return None
