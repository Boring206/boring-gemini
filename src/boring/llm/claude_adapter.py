"""
Claude Code CLI Adapter for Boring
"""

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

from ..config import settings
from ..logger import get_logger, log_status
from .provider import LLMProvider, LLMResponse

_logger = get_logger("claude_adapter")


class ClaudeCLIAdapter(LLMProvider):
    """
    Adapter that communicates with Anthropic's Claude Code CLI.

    Usage:
        adapter = ClaudeCLIAdapter()
        res = adapter.generate_with_tools("Fix this bug")
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        log_dir: Optional[Path] = None,
        timeout_seconds: int = 600,
    ):
        self._model_name = model_name or "claude-3-5-sonnet"
        self.log_dir = log_dir or settings.LOG_DIR
        self.timeout_seconds = timeout_seconds

        # Verify CLI availability
        self.cli_path = settings.CLAUDE_CLI_PATH or shutil.which("claude")
        if self.cli_path:
            log_status(self.log_dir, "INFO", f"Claude CLI Adapter initialized: {self.cli_path}")
        else:
            log_status(self.log_dir, "WARN", "Claude CLI (claude-code) not found in PATH.")

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def is_available(self) -> bool:
        return self.cli_path is not None

    def generate(
        self,
        prompt: str,
        context: str = "",
        system_instruction: str = "",
        timeout_seconds: int = 600,
    ) -> tuple[str, bool]:
        """Generate response using Claude CLI."""
        res = self.generate_with_tools(prompt, context, system_instruction, timeout_seconds)
        return res.text, res.success

    def generate_with_tools(
        self,
        prompt: str,
        context: str = "",
        system_instruction: str = "",
        timeout_seconds: int = 600,
    ) -> LLMResponse:
        """
        Invoke Claude CLI.
        Note: Claude Code is interactive by default. We use the 'print' mode
        or similar non-interactive flags if available, or simulate a session.
        """
        if not self.is_available:
            return LLMResponse(
                text="", function_calls=[], success=False, error="Claude CLI not found"
            )

        # Claude Code 'print' mode or direct prompt
        # Based on early docs/help, using 'claude "prompt"' often works for single shot.
        # We wrap it in a system instruction to ensure logical consistency.
        full_prompt = f"{system_instruction}\n\n{context}\n\n{prompt}"

        try:
            # Note: We use --non-interactive if supported, otherwise standard subprocess
            cmd = [self.cli_path, full_prompt]

            # Additional flags to ensure clean output for parsing
            # cmd.extend(["--no-color", "--json"]) # If supported

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout_seconds, encoding="utf-8"
            )

            if result.returncode != 0:
                return LLMResponse(
                    text="",
                    function_calls=[],
                    success=False,
                    error=result.stderr or "CLI execution failed",
                )

            text = result.stdout

            # Post-processing: Extract tool calls if Claude uses them in JSON/XML blocks
            function_calls = self._parse_tool_calls(text)

            return LLMResponse(
                text=text,
                function_calls=function_calls,
                success=True,
                metadata={"provider": "claude-code"},
            )

        except Exception as e:
            _logger.error(f"Claude CLI execution failed: {e}")
            return LLMResponse(text="", function_calls=[], success=False, error=str(e))

    def _parse_tool_calls(self, text: str) -> list[dict[str, Any]]:
        """Extract tool calls from Claude's text output."""
        # Claude often uses XML-like or JSON blocks for reasoning.
        # For now, we reuse the JSON pattern but add XML support if needed.
        calls = []
        try:
            # Look for JSON tool calls (standardized format)
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                if "tool_calls" in data:
                    for tc in data["tool_calls"]:
                        calls.append({"name": tc["name"], "args": tc["arguments"]})
        except:
            pass
        return calls
