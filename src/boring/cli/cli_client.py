"""
Gemini CLI Adapter for Boring V4.0

Provides a privacy-focused backend that uses the local Gemini CLI
instead of direct API calls. This allows usage without an API key
by leveraging the CLI's OAuth token.

Features:
- No API key required (uses `gemini login` OAuth)
- Same interface as GeminiClient (Adapter Pattern)
- Automatic authentication error detection
"""

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from boring.core.logger import log_status
from boring.llm.provider import LLMProvider, LLMResponse


@dataclass
class CLIResponse:
    """Response from Gemini CLI."""

    text: str
    success: bool
    error: Optional[str] = None


class GeminiCLIAdapter(LLMProvider):
    """
    Adapter that implements LLMProvider interface using Gemini CLI.

    Usage:
        adapter = GeminiCLIAdapter()
        text, success = adapter.generate("Explain this code")

    Prerequisites:
        1. Install: npm install -g @google/gemini-cli
        2. Login: gemini login
    """

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash-exp",
        log_dir: Optional[Path] = None,
        timeout_seconds: int = 300,
        cwd: Optional[Path] = None,
    ):
        self._model_name = model_name
        self.log_dir = log_dir or Path("logs")
        self.timeout_seconds = timeout_seconds
        self.cwd = cwd

        # Verify CLI is available (shutil.which returns None if not found)
        self.cli_path = shutil.which("gemini")
        if self.cli_path:
            log_status(
                self.log_dir,
                "INFO",
                f"Gemini CLI Adapter initialized: {self.cli_path} (cwd: {self.cwd})",
            )
        else:
            log_status(
                self.log_dir,
                "WARN",
                "Gemini CLI not found. CLI-based features will be unavailable.",
            )

    @property
    def provider_name(self) -> str:
        return "gemini_cli"

    @property
    def base_url(self) -> Optional[str]:
        return None  # CLI doesn't use a base URL in the same way

    @property
    def model_name(self) -> str:
        """Return the model name being used."""
        return self._model_name

    @property
    def is_available(self) -> bool:
        """Check if the client is properly configured and available."""
        return self.cli_path is not None

    def generate_with_tools(
        self,
        prompt: str,
        context: str = "",
        tools: Optional[list] = None,
        timeout_seconds: int = 900,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate a response that includes text and potential tool calls.
        Since CLI doesn't natively support tool binding, we use Prompt Engineering + JSON Parsing.
        """
        # 1. Construct System Prompt for Tools
        tool_definitions = (
            json.dumps(
                [t for t in tools if hasattr(t, "to_json") or isinstance(t, dict)],
                default=str,
                indent=2,
            )
            if tools
            else "[]"
        )

        system_instruction = f"""
SYSTEM INSTRUCTION: You are an AI assistant with access to the following tools:
{tool_definitions}

To use a tool, you MUST output a JSON block strictly in this format:
```json
{{
  "tool_calls": [
    {{
      "name": "tool_name",
      "arguments": {{ "arg1": "value1" }}
    }}
  ]
}}
```
If no tool is needed, just respond with normal text.
"""
        full_context = f"{context}\n\n{system_instruction}"

        # 2. Call CLI
        text, success = self.generate(prompt, full_context)

        if not success:
            return LLMResponse(
                text=text, function_calls=[], success=False, error="CLI generation failed"
            )

        # 3. Parse Output for Tool Calls
        function_calls = []
        clean_text = text

        try:
            # Look for JSON block
            import re

            json_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)

                if "tool_calls" in data:
                    for tc in data["tool_calls"]:
                        function_calls.append({"name": tc["name"], "args": tc["arguments"]})
                    # Remove the tool call JSON from the visible text to keep UI clean
                    clean_text = text.replace(json_match.group(0), "").strip()

        except Exception as e:
            log_status(self.log_dir, "WARN", f"Failed to parse CLI tool output: {e}")

        return LLMResponse(
            text=clean_text,
            function_calls=function_calls,
            success=True,
            metadata={"source": "gemini-cli-adapter"},
        )

    def generate(self, prompt: str, context: str = "", **kwargs) -> tuple[str, bool]:
        """
        Generate response using Gemini CLI.

        Args:
            prompt: The main prompt text
            context: Additional context to prepend

        Returns:
            Tuple of (response_text, success)
        """
        full_prompt = f"{context}\n\n{prompt}" if context else prompt

        try:
            response = self._execute_cli(full_prompt)
            return response.text, response.success
        except PermissionError as e:
            # Authentication error
            log_status(self.log_dir, "ERROR", str(e))
            return str(e), False
        except Exception as e:
            log_status(self.log_dir, "ERROR", f"CLI error: {e}")
            return str(e), False

    def generate_with_retry(
        self, prompt: str, context: str = "", max_retries: int = 3, **kwargs
    ) -> tuple[str, bool]:
        """Generate with automatic retry on transient errors."""
        for attempt in range(max_retries):
            text, success = self.generate(prompt, context, **kwargs)

            if success:
                return text, True

            # Check for auth errors (no retry)
            if "login" in text.lower() or "unauthenticated" in text.lower():
                return text, False

            # Retry on transient errors
            if attempt < max_retries - 1:
                log_status(self.log_dir, "WARN", f"Retry {attempt + 1}/{max_retries}")

        return text, False

    def chat(self, prompt: str, interactive: bool = False, **kwargs) -> str:
        """
        Chat interface (alias for generate in CLI adapter).

        Args:
            prompt: The message to send.
            interactive: Ignored in CLI adapter (always non-interactive via subprocess).

        Returns:
            The response string.
        """
        text, success = self.generate(prompt, **kwargs)
        if not success:
            raise RuntimeError(f"Gemini CLI generation failed: {text}")
        return text

    def _execute_cli(self, prompt: str) -> CLIResponse:
        """Execute Gemini CLI with prompt."""
        cmd = [self.cli_path]

        # Only add model flag if not using default
        if self.model_name != "default":
            cmd.extend(["-m", self.model_name])

        # CRITICAL: Use non-interactive flags to prevent hangs in MCP/headless mode
        # -p - : Read prompt from stdin
        # --yolo: Auto-approve all tools (required for non-interactive loop)
        cmd.extend(["--output-format", "text", "--yolo", "-p", "-"])

        try:
            result = subprocess.run(
                cmd,
                input=prompt,  # Pass prompt via stdin
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                encoding="utf-8",
                cwd=self.cwd,
                stdin=None,  # subprocess.run with input=... handles stdin
            )

            # Check for authentication errors
            stderr = result.stderr.lower() if result.stderr else ""
            if "login" in stderr or "unauthenticated" in stderr or "not authenticated" in stderr:
                raise PermissionError(
                    "Gemini CLI is not authenticated.\nPlease run: gemini login\nThen try again."
                )

            if result.returncode != 0:
                return CLIResponse(
                    text=result.stderr or "CLI returned error", success=False, error=result.stderr
                )

            return CLIResponse(text=result.stdout, success=True)

        except subprocess.TimeoutExpired:
            return CLIResponse(text="CLI execution timed out", success=False, error="Timeout")
        except FileNotFoundError:
            raise FileNotFoundError(
                "Gemini CLI not found. Install with:\n  npm install -g @google/gemini-cli"
            )

    def _execute_cli_json(self, prompt: str) -> CLIResponse:
        """Execute Gemini CLI with JSON output format."""
        cmd = [self.cli_path]

        if self.model_name != "default":
            cmd.extend(["-m", self.model_name])

        # CRITICAL: Use non-interactive flags
        cmd.extend(["--output-format", "json", "--yolo", "-p", "-"])

        try:
            result = subprocess.run(
                cmd,
                input=prompt,  # Pass prompt via stdin
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                encoding="utf-8",
                cwd=self.cwd,
            )

            if result.returncode != 0:
                return CLIResponse(
                    text=result.stderr or "CLI error", success=False, error=result.stderr
                )

            try:
                data = json.loads(result.stdout)
                return CLIResponse(text=data.get("text", result.stdout), success=True)
            except json.JSONDecodeError:
                return CLIResponse(text=result.stdout, success=True)

        except subprocess.TimeoutExpired:
            return CLIResponse(text="CLI execution timed out", success=False, error="Timeout")


def create_cli_adapter(
    model_name: str = "gemini-2.0-flash-exp", log_dir: Optional[Path] = None
) -> Optional[GeminiCLIAdapter]:
    """
    Factory function to create a CLI adapter.

    Returns None if CLI is not available.
    """
    try:
        adapter = GeminiCLIAdapter(model_name=model_name, log_dir=log_dir)
        if not adapter.is_available:
            return None
        return adapter
    except Exception as e:
        log_status(log_dir or Path("logs"), "ERROR", str(e))
        return None


def check_cli_available() -> bool:
    """Check if Gemini CLI is installed."""
    return shutil.which("gemini") is not None


def check_cli_authenticated() -> tuple[bool, str]:
    """
    Check if Gemini CLI is authenticated.

    Returns:
        Tuple of (is_authenticated, message)
    """
    if not check_cli_available():
        return False, "Gemini CLI not installed"

    try:
        # Run a simple test command
        result = subprocess.run(
            ["gemini", "-p", "hi", "--output-format", "text"],
            stdin=subprocess.DEVNULL,  # CRITICAL: Prevent inheriting MCP's stdin
            capture_output=True,
            text=True,
            timeout=5,  # Short timeout to avoid hangs
        )

        stderr = result.stderr.lower() if result.stderr else ""
        if "login" in stderr or "unauthenticated" in stderr:
            return False, "Not authenticated. Run: gemini login"

        if result.returncode == 0:
            return True, "Authenticated"

        return False, result.stderr or "Unknown error"

    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)
