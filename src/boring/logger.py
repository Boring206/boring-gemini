"""
Logging Module for Boring V4.0

Provides centralized logging and status management.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from rich.console import Console

console = Console()


def log_status(log_dir: Path, level: str, message: str):
    """
    Logs status messages to console and a file.
    
    Args:
        log_dir: Directory for log files
        level: Log level (INFO, WARN, ERROR, SUCCESS, LOOP)
        message: Message to log
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "boring.log"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    color_map = {
        "INFO": "blue",
        "WARN": "yellow",
        "ERROR": "red",
        "SUCCESS": "green",
        "LOOP": "purple",
        "DEBUG": "dim",
        "CRITICAL": "bold red",
    }
    style = color_map.get(level.upper(), "default")
    console.print(f"[{timestamp}] [[{level.upper()}]] {message}", style=style)
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{level.upper()}] {message}\n")


def update_status(
    status_file: Path,
    loop_count: int,
    max_calls: int,
    last_action: str,
    status: str,
    exit_reason: str = "",
    calls_made: Optional[int] = None
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
    next_reset_time = (datetime.now() + timedelta(hours=1)).strftime('%H:%M:%S')

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

    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(status_data, f, indent=4)


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
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            return [line.strip() for line in all_lines[-lines:]]
    except Exception:
        return []
