"""
Circuit Breaker Module for Boring V5.0

Implements the Circuit Breaker pattern to prevent infinite loops
when the agent keeps failing repeatedly.

States:
- CLOSED: Normal operation
- OPEN: Halted due to failures
- HALF_OPEN: Testing recovery (allows 1 test request)
"""

import json
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.json import JSON
from rich.panel import Panel

from ..paths import get_state_file
from .config import settings

console = Console()

# Configuration
CIRCUIT_BREAKER_MAX_FAILURES = 3
CIRCUIT_BREAKER_RESET_TIMEOUT = 600  # 10 minutes


def _get_circuit_files(project_root: Path | None = None) -> tuple[Path, Path]:
    root = project_root or settings.PROJECT_ROOT
    return (
        get_state_file(root, "circuit_breaker_state"),
        get_state_file(root, "circuit_breaker_history"),
    )


# Legacy constants for backward compatibility.
CB_STATE_FILE, CB_HISTORY_FILE = _get_circuit_files()


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class LoopInfo:
    """Information about the last loop."""

    loop: int
    files_changed: int
    has_errors: bool
    output_length: int


def init_circuit_breaker(project_root: Path | None = None):
    """Initializes the circuit breaker state file."""
    state_file, history_file = _get_circuit_files(project_root)
    if not state_file.exists():
        state = {
            "state": CircuitState.CLOSED.value,
            "failures": 0,
            "last_failure_time": 0,
            "last_loop_info": {
                "loop": 0,
                "files_changed": 0,
                "has_errors": False,
                "output_length": 0,
            },
        }
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state, indent=4))
    if not history_file.exists():
        history_file.parent.mkdir(parents=True, exist_ok=True)
        history_file.write_text(json.dumps([], indent=4))


def _log_circuit_state_change(new_state: str, reason: str, project_root: Path | None = None):
    """Logs circuit breaker state changes to history."""
    _, history_file = _get_circuit_files(project_root)
    if not history_file.exists():
        history_file.parent.mkdir(parents=True, exist_ok=True)
        history_file.write_text(json.dumps([], indent=4))

    history = json.loads(history_file.read_text())
    history.append({"timestamp": datetime.now().isoformat(), "state": new_state, "reason": reason})
    # Keep only last 50 entries
    history = history[-50:]
    history_file.write_text(json.dumps(history, indent=4))


def get_circuit_state(project_root: Path | None = None) -> dict[str, Any]:
    """Get current circuit breaker state."""
    init_circuit_breaker(project_root)
    state_file, _ = _get_circuit_files(project_root)
    return json.loads(state_file.read_text())


def record_loop_result(
    loop_num: int,
    files_changed: int,
    has_errors: bool,
    output_length: int,
    project_root: Path | None = None,
) -> int:
    """
    Records the result of a loop and updates circuit breaker state.

    Returns:
        0 if OK to continue, 1 if should halt
    """
    init_circuit_breaker(project_root)
    state_file, _ = _get_circuit_files(project_root)
    state_data = json.loads(state_file.read_text())
    current_state = state_data["state"]
    failures = state_data["failures"]
    last_loop_info = state_data["last_loop_info"]

    new_state = current_state

    # Heuristic for progress
    progress_made = files_changed > 0 or (
        output_length > 0 and output_length > last_loop_info.get("output_length", 0) * 0.5
    )

    if has_errors or not progress_made:
        failures += 1
        state_data["last_failure_time"] = int(time.time())
    else:
        failures = 0  # Reset failures on success

    # State transitions
    if current_state == CircuitState.CLOSED.value and failures >= CIRCUIT_BREAKER_MAX_FAILURES:
        new_state = CircuitState.OPEN.value
        _log_circuit_state_change(
            CircuitState.OPEN.value, "Too many consecutive failures/no progress", project_root
        )
    elif current_state == CircuitState.OPEN.value:
        if (int(time.time()) - state_data["last_failure_time"]) > CIRCUIT_BREAKER_RESET_TIMEOUT:
            new_state = CircuitState.HALF_OPEN.value
            _log_circuit_state_change(
                CircuitState.HALF_OPEN.value, "Reset timeout reached", project_root
            )
    elif current_state == CircuitState.HALF_OPEN.value:
        if has_errors or not progress_made:
            new_state = CircuitState.OPEN.value
            _log_circuit_state_change(
                CircuitState.OPEN.value, "Failed in HALF_OPEN state", project_root
            )
        else:
            new_state = CircuitState.CLOSED.value
            _log_circuit_state_change(
                CircuitState.CLOSED.value, "Recovered in HALF_OPEN state", project_root
            )

    state_data["state"] = new_state
    state_data["failures"] = failures
    state_data["last_loop_info"] = {
        "loop": loop_num,
        "files_changed": files_changed,
        "has_errors": has_errors,
        "output_length": output_length,
    }
    state_file.write_text(json.dumps(state_data, indent=4))

    return 1 if new_state == CircuitState.OPEN.value else 0


def should_halt_execution(project_root: Path | None = None) -> bool:
    """Checks if the circuit breaker is in OPEN state."""
    state_data = get_circuit_state(project_root)
    return state_data["state"] == CircuitState.OPEN.value


def reset_circuit_breaker(reason: str = "Manual reset", project_root: Path | None = None):
    """Resets the circuit breaker to CLOSED state."""
    state_file, _ = _get_circuit_files(project_root)
    state = {
        "state": CircuitState.CLOSED.value,
        "failures": 0,
        "last_failure_time": 0,
        "last_loop_info": {"loop": 0, "files_changed": 0, "has_errors": False, "output_length": 0},
    }
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=4))
    _log_circuit_state_change(CircuitState.CLOSED.value, reason, project_root)


def show_circuit_status(project_root: Path | None = None):
    """Displays the current circuit breaker status."""
    state_data = get_circuit_state(project_root)
    _, history_file = _get_circuit_files(project_root)
    console.print(
        Panel(
            JSON(json.dumps(state_data, indent=4)),
            title="[bold blue]Circuit Breaker Status[/bold blue]",
            border_style="blue",
        )
    )
    if history_file.exists():
        history_data = json.loads(history_file.read_text())
        console.print(
            Panel(
                JSON(json.dumps(history_data[-10:], indent=4)),  # Show last 10
                title="[bold blue]Circuit Breaker History[/bold blue]",
                border_style="blue",
            )
        )
