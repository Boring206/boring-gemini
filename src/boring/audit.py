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
from typing import Any, Callable, Dict, Optional


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
        args: Dict[str, Any],
        result: Dict[str, Any],
        duration_ms: int,
        project_root: Optional[str] = None
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
            "result_status": result.get("status", "UNKNOWN") if isinstance(result, dict) else "UNKNOWN",
            "duration_ms": duration_ms,
            "project_root": project_root
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass  # Silent fail - audit should never break the tool
    
    def _sanitize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
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
        
        entries = []
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
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
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            AuditLogger.get_instance().log(
                tool_name=func.__name__,
                args=kwargs,
                result={"status": "EXCEPTION", "error": str(e)},
                duration_ms=duration_ms
            )
            raise
        
        duration_ms = int((time.time() - start_time) * 1000)
        AuditLogger.get_instance().log(
            tool_name=func.__name__,
            args=kwargs,
            result=result if isinstance(result, dict) else {"status": "OK", "value": str(result)[:200]},
            duration_ms=duration_ms
        )
        
        return result
    
    return wrapper
