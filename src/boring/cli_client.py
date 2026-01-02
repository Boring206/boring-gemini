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

import subprocess
import shutil
import json
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

from .logger import log_status
from .logger import log_status
from .interfaces import LLMClient, LLMResponse


@dataclass
class CLIResponse:
    """Response from Gemini CLI."""
    text: str
    success: bool
    error: Optional[str] = None


class GeminiCLIAdapter(LLMClient):
    """
    Adapter that implements LLMClient interface using Gemini CLI.
    
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
        cwd: Optional[Path] = None
    ):
        self._model_name = model_name
        self.log_dir = log_dir or Path("logs")
        self.timeout_seconds = timeout_seconds
        self.cwd = cwd
        
        # Verify CLI is installed
        self.cli_path = shutil.which("gemini")
        if not self.cli_path:
            raise FileNotFoundError(
                "Gemini CLI not found. Install with:\n"
                "  npm install -g @google/gemini-cli\n"
                "Then authenticate with:\n"
                "  gemini login"
            )
        
        log_status(self.log_dir, "INFO", f"Gemini CLI Adapter initialized: {self.cli_path} (cwd: {self.cwd})")

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
        timeout_seconds: int = 900,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response that includes text (tools not yet supported in CLI adapter).
        Ignores tool definitions for now and returns plain text wrapped in LLMResponse.
        """
        # Fallback to standard generate since CLI doesn't support complex tool calls easily yet
        text, success = self.generate(prompt, context)
        
        return LLMResponse(
            text=text,
            function_calls=[],
            success=success,
            error=None if success else "Generation failed",
            metadata={"source": "gemini-cli-adapter"}
        )
    
    def generate(self, prompt: str, context: str = "", **kwargs) -> Tuple[str, bool]:
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
        self,
        prompt: str,
        context: str = "",
        max_retries: int = 3,
        **kwargs
    ) -> Tuple[str, bool]:
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
    
    def _execute_cli(self, prompt: str) -> CLIResponse:
        """Execute Gemini CLI with prompt."""
        cmd = [
            self.cli_path,
            "-p", prompt,
            "-m", self.model_name,
            "--output-format", "text"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,  # CRITICAL: Prevent inheriting MCP's stdin
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                encoding="utf-8",
                cwd=self.cwd  # Execute in project context
            )
            
            # Check for authentication errors
            stderr = result.stderr.lower() if result.stderr else ""
            if "login" in stderr or "unauthenticated" in stderr or "not authenticated" in stderr:
                raise PermissionError(
                    "Gemini CLI is not authenticated.\n"
                    "Please run: gemini login\n"
                    "Then try again."
                )
            
            if result.returncode != 0:
                return CLIResponse(
                    text=result.stderr or "CLI returned error",
                    success=False,
                    error=result.stderr
                )
            
            return CLIResponse(
                text=result.stdout,
                success=True
            )
            
        except subprocess.TimeoutExpired:
            return CLIResponse(
                text="CLI execution timed out",
                success=False,
                error="Timeout"
            )
        except FileNotFoundError:
            raise FileNotFoundError(
                "Gemini CLI not found. Install with:\n"
                "  npm install -g @google/gemini-cli"
            )
    
    def _execute_cli_json(self, prompt: str) -> CLIResponse:
        """Execute Gemini CLI with JSON output format."""
        cmd = [
            self.cli_path,
            "-p", prompt,
            "-m", self.model_name,
            "--output-format", "json"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,  # CRITICAL: Prevent inheriting MCP's stdin
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                encoding="utf-8"
            )
            
            if result.returncode != 0:
                return CLIResponse(
                    text=result.stderr or "CLI error",
                    success=False,
                    error=result.stderr
                )
            
            try:
                data = json.loads(result.stdout)
                return CLIResponse(
                    text=data.get("text", result.stdout),
                    success=True
                )
            except json.JSONDecodeError:
                return CLIResponse(
                    text=result.stdout,
                    success=True
                )
                
        except subprocess.TimeoutExpired:
            return CLIResponse(
                text="CLI execution timed out",
                success=False,
                error="Timeout"
            )


def create_cli_adapter(
    model_name: str = "gemini-2.0-flash-exp",
    log_dir: Optional[Path] = None
) -> Optional[GeminiCLIAdapter]:
    """
    Factory function to create a CLI adapter.
    
    Returns None if CLI is not available.
    """
    try:
        return GeminiCLIAdapter(model_name=model_name, log_dir=log_dir)
    except FileNotFoundError as e:
        log_status(log_dir or Path("logs"), "ERROR", str(e))
        return None


def check_cli_available() -> bool:
    """Check if Gemini CLI is installed."""
    return shutil.which("gemini") is not None


def check_cli_authenticated() -> Tuple[bool, str]:
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
            timeout=5  # Short timeout to avoid hangs
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
