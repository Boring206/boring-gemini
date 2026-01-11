"""
Logging Module for Boring V5.0

Provides centralized structured logging using structlog.
Supports both console and JSON file output for observability.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import structlog
from rich.console import Console

from boring.core.utils import TransactionalFileWriter

# MCP-compatible Rich Console (stderr, quiet in MCP mode)
_is_mcp_mode = os.environ.get("BORING_MCP_MODE") == "1"
console = Console(stderr=True, quiet=_is_mcp_mode)

# Configure Python's logging first
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
)

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


def get_logger(name: str = "boring") -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Global logger for module-level use
_logger = get_logger()
logger = _logger


def log_status(log_dir: Any, level: str, message: str, **kwargs: Any):
    """
    Logs status messages using structlog with console and file output.

    Args:
        log_dir: Directory for log files (Path or str). If None/False, only logs to console.
        level: Log level (INFO, WARN, ERROR, SUCCESS, LOOP)
        message: Message to log
        **kwargs: Additional structured fields
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if log_dir:
        if isinstance(log_dir, str):
            log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "boring.log"
    else:
        log_file = None

    # Console output with Rich colors
    color_map = {
        "INFO": "blue",
        "WARN": "yellow",
        "ERROR": "red",
        "SUCCESS": "green",
        "LOOP": "purple",
        "DEBUG": "dim",
        "CRITICAL": "bold red",
        "PLAN": "cyan",  # New level for Vibe Coder planning
        "VIBE": "magenta",  # New level for Vibe Coder interactions
    }

    # Emoji mapping for Vibe Coder
    emoji_map = {
        "INFO": "ℹ️ ",
        "WARN": "⚠️ ",
        "ERROR": "❌ ",
        "SUCCESS": "✅ ",
        "LOOP": "🔄 ",
        "DEBUG": "🐛 ",
        "CRITICAL": "🚨 ",
        "PLAN": "🗺️ ",
        "VIBE": "✨ ",
    }

    style = color_map.get(level.upper(), "default")
    emoji = emoji_map.get(level.upper(), "")

    # Format extra fields for display
    extra_str = ""
    if kwargs:
        extra_str = " " + " ".join(f"{k}={v}" for k, v in kwargs.items())

    console.print(f"[{timestamp}] [[{level.upper()}]] {emoji}{message}{extra_str}", style=style)

    # File output in JSON Lines format for analysis
    if log_file:
        log_entry = {"timestamp": timestamp, "level": level.upper(), "message": message, **kwargs}

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

    # Also log via structlog for consistent observability
    log_method = getattr(_logger, level.lower(), _logger.info)
    log_method(message, **kwargs)


def update_status(
    status_file: Path,
    loop_count: int,
    max_calls: int,
    last_action: str,
    status: str,
    exit_reason: str = "",
    calls_made: Optional[int] = None,
):
    """
    Updates the status.json file for external monitoring.

    Args:
        status_file: Path to status.json
        loop_count: Current loop number
        max_calls: Maximum calls per hour
        last_action: Description of last action
        status: Current status string
        exit_reason: Reason for exit (if any)
        calls_made: Number of API calls made
    """
    status_file.parent.mkdir(parents=True, exist_ok=True)
    next_reset_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M:%S")

    if calls_made is None:
        from .limiter import get_calls_made

        calls_made = get_calls_made(Path(".call_count"))

    status_data = {
        "timestamp": datetime.now().isoformat(),
        "loop_count": loop_count,
        "calls_made_this_hour": calls_made,
        "max_calls_per_hour": max_calls,
        "last_action": last_action,
        "status": status,
        "exit_reason": exit_reason,
        "next_reset": next_reset_time,
    }

    TransactionalFileWriter.write_json(status_file, status_data, indent=4)

    # Log status update structurally
    _logger.debug("status_updated", loop=loop_count, status=status, calls=calls_made)


def get_log_tail(log_dir: Path, lines: int = 10) -> list[str]:
    """
    Get the last N lines from the log file.

    Args:
        log_dir: Directory containing boring.log
        lines: Number of lines to return

    Returns:
        List of log lines
    """
    log_file = log_dir / "boring.log"
    if not log_file.exists():
        return []

    try:
        with open(log_file, encoding="utf-8") as f:
            all_lines = f.readlines()
            return [line.strip() for line in all_lines[-lines:]]
    except Exception:
        return []
