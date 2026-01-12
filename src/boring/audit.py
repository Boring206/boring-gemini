# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Audit logging for MCP tool invocations.

Provides structured JSONL logging for all tool calls, enabling:
- Debugging and troubleshooting
- Usage analytics
- Security auditing
"""

import json
import time
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional


class AuditLogger:
    """
    Structured JSON Lines logger for MCP tool invocations.

    Each log entry contains:
    - timestamp: ISO 8601 UTC timestamp
    - tool: Name of the tool invoked
    - args: Arguments passed to the tool (sanitized)
    - result_status: SUCCESS, ERROR, RATE_LIMITED, etc.
    - duration_ms: Execution time in milliseconds
    - project_root: Active project path
    """

    _instance: Optional["AuditLogger"] = None

    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit.jsonl"
        self._enabled = True

    @classmethod
    def get_instance(cls, log_dir: Optional[Path] = None) -> "AuditLogger":
        """Get or create singleton instance."""
        if cls._instance is None:
            if log_dir is None:
                log_dir = Path.cwd() / "logs"
            cls._instance = cls(log_dir)
        return cls._instance

    def enable(self):
        """Enable audit logging."""
        self._enabled = True

    def disable(self):
        """Disable audit logging (for tests)."""
        self._enabled = False

    def log(
        self,
        tool_name: str,
        args: dict[str, Any],
        result: dict[str, Any],
        duration_ms: int,
        project_root: Optional[str] = None,
    ):
        """
        Log a tool invocation.

        Args:
            tool_name: Name of the MCP tool
            args: Arguments passed (will be sanitized)
            result: Tool return value
            duration_ms: Execution time in milliseconds
            project_root: Active project directory
        """
        if not self._enabled:
            return

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": tool_name,
            "args": self._sanitize_args(args),
            "result_status": result.get("status", "UNKNOWN")
            if isinstance(result, dict)
            else "UNKNOWN",
            "result": result,
            "duration_ms": duration_ms,
            "project_root": project_root,
        }

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass  # Silent fail - audit should never break the tool

    def _sanitize_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Remove sensitive data from args before logging."""
        sanitized = {}
        sensitive_keys = {"token", "password", "secret", "key", "api_key"}

        for k, v in args.items():
            if k.lower() in sensitive_keys:
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, str) and len(v) > 500:
                sanitized[k] = v[:200] + f"... [truncated {len(v)} chars]"
            else:
                sanitized[k] = v

        return sanitized

    def get_recent_logs(self, limit: int = 100) -> list:
        """Read recent log entries."""
        if not self.log_file.exists():
            return []

        def _safe_parse(line):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                return None

        with open(self.log_file, encoding="utf-8") as f:
            entries = [
                parsed for line in f if line.strip() if (parsed := _safe_parse(line)) is not None
            ]

        return entries[-limit:]


def audited(func: Callable) -> Callable:
    """
    Decorator to automatically log tool invocations.

    Usage:
        @mcp.tool()
        @audited
        def my_tool(arg1: str) -> dict:
            ...
    """
    import inspect

    sig = inspect.signature(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        # Lazy import to avoid circular dependency
        from .error_translator import ErrorTranslator

        translator = ErrorTranslator()

        # Capture all arguments including defaults
        try:
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            all_args = dict(bound_args.arguments)
            # Remove 'self' or 'cls' if present
            if "self" in all_args:
                all_args.pop("self")
            if "cls" in all_args:
                all_args.pop("cls")
        except Exception:
            all_args = kwargs  # Fallback to just kwargs if binding fails

        try:
            result = func(*args, **kwargs)

            # Check for functional errors (status="ERROR")
            if isinstance(result, dict) and result.get("status") == "ERROR" and "message" in result:
                explanation = translator.translate(result["message"])
                result["vibe_explanation"] = explanation.friendly_message
                if explanation.fix_command:
                    result["vibe_fix"] = explanation.fix_command

                # Tutorial Hook for Error
                try:
                    from .tutorial import TutorialManager

                    TutorialManager().show_tutorial("first_error")
                except Exception as tutorial_err:
                    import sys

                    sys.stderr.write(f"[boring-audit] Tutorial hook failed: {tutorial_err}\n")

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # Translate exception
            error_msg = str(e)
            explanation = translator.translate(error_msg)

            # Tutorial Hook for Exception
            try:
                from .tutorial import TutorialManager

                TutorialManager().show_tutorial("first_error")
            except Exception as tutorial_err:
                import sys

                sys.stderr.write(f"[boring-audit] Tutorial hook failed: {tutorial_err}\n")

            AuditLogger.get_instance().log(
                tool_name=func.__name__,
                args=all_args,
                result={
                    "status": "EXCEPTION",
                    "error": error_msg,
                    "vibe_explanation": explanation.friendly_message,
                },
                duration_ms=duration_ms,
            )
            raise

        duration_ms = int((time.time() - start_time) * 1000)
        AuditLogger.get_instance().log(
            tool_name=func.__name__,
            args=all_args,
            result=result
            if isinstance(result, dict)
            else {"status": "OK", "value": str(result)[:200]},
            duration_ms=duration_ms,
        )

        return result

    return wrapper
