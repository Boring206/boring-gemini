"""
Circuit Breaker Module for Boring V15.0

Implements the Adaptive Circuit Breaker pattern with exponential backoff
to prevent infinite loops when the agent keeps failing repeatedly.

States:
- CLOSED: Normal operation
- OPEN: Halted due to failures
- HALF_OPEN: Testing recovery (allows 1 test request)
"""

import json
import random
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..paths import get_state_file
from .config import settings

# Configuration
CIRCUIT_BREAKER_MAX_FAILURES = 3
CIRCUIT_BREAKER_BASE_TIMEOUT = 60.0  # 1 minute
CIRCUIT_BREAKER_MAX_TIMEOUT = 3600.0  # 1 hour

# Use a lazy cache for circuit files
_CIRCUIT_FILES_CACHE = {}


def _get_circuit_files(project_root: Path | None = None) -> tuple[Path, Path]:
    root = project_root or settings.PROJECT_ROOT
    if root not in _CIRCUIT_FILES_CACHE:
        _CIRCUIT_FILES_CACHE[root] = (
            get_state_file(root, "circuit_breaker_state"),
            get_state_file(root, "circuit_breaker_history"),
        )
    return _CIRCUIT_FILES_CACHE[root]


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


class AdaptiveCircuitBreaker:
    """
    Adaptive Circuit Breaker with Exponential Backoff.
    Manages state persistence and transitions.
    """

    def __init__(self, name: str = "default", project_root: Path | None = None):
        self.name = name
        self.project_root = project_root
        self.state_file, self.history_file = _get_circuit_files(project_root)
        self._ensure_init()

    def _ensure_init(self):
        """Initialize state files if missing."""
        if not self.state_file.exists():
            initial_state = {
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
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text(json.dumps(initial_state, indent=4))

        if not self.history_file.exists():
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            self.history_file.write_text(json.dumps([], indent=4))

    def _load_state(self) -> dict:
        return json.loads(self.state_file.read_text())

    def _save_state(self, data: dict):
        self.state_file.write_text(json.dumps(data, indent=4))

    def _log_transition(self, new_state: str, reason: str):
        """Log state transition to history file."""
        try:
            history = json.loads(self.history_file.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            history = []

        history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "state": new_state,
                "reason": reason,
                "recovery_timeout": self.current_recovery_timeout,
            }
        )
        # Keep only last 50 entries
        self.history_file.write_text(json.dumps(history[-50:], indent=4))

    @property
    def consecutive_failures(self) -> int:
        state = self._load_state()
        return state.get("failures", 0)

    @property
    def current_recovery_timeout(self) -> float:
        """Calculate exponential backoff timeout."""
        failures = self.consecutive_failures
        # If failures < threshold, timeout applies to potential next failure
        # Effective failures for calculation start after threshold
        effective_failures = max(0, failures - CIRCUIT_BREAKER_MAX_FAILURES + 1)

        timeout = min(
            CIRCUIT_BREAKER_BASE_TIMEOUT * (2 ** (effective_failures - 1))
            if effective_failures > 0
            else CIRCUIT_BREAKER_BASE_TIMEOUT,
            CIRCUIT_BREAKER_MAX_TIMEOUT,
        )
        return timeout

    def should_allow_request(self) -> bool:
        """Check if request is allowed (Stateless check based on file)."""
        state_data = self._load_state()
        state = state_data["state"]

        if state == CircuitState.CLOSED.value:
            return True

        if state == CircuitState.OPEN.value:
            last_fail = state_data["last_failure_time"]
            # Add Jitter (0-10% of timeout) to prevent thundering herd
            timeout = self.current_recovery_timeout
            jitter = random.uniform(0, timeout * 0.1)

            if (time.time() - last_fail) > (timeout + jitter):
                # Transition to HALF_OPEN strictly?
                # Or just allow this one request and update state?
                # Ideally, we update state to HALF_OPEN now.
                self._transition(
                    state_data, CircuitState.HALF_OPEN.value, "Recovery timeout reached (Adaptive)"
                )
                return True
            return False

        if state == CircuitState.HALF_OPEN.value:
            # In strict distributed systems, we might need a lock here to allow only 1.
            # For now, we allow it, assuming the caller will look at the result.
            return True

        return False

    def record_result(
        self, loop_num: int, files_changed: int, has_errors: bool, output_length: int
    ) -> int:
        """
        Record execution result and update state.
        Returns: 1 if should halt (OPEN), 0 otherwise.
        """
        state_data = self._load_state()
        current_state = state_data["state"]
        last_loop_info = state_data.get("last_loop_info", {})

        # Heuristic for progress
        progress_made = files_changed > 0 or (
            output_length > 0 and output_length > last_loop_info.get("output_length", 0) * 0.5
        )

        # Update metrics
        from ..core.telemetry import get_telemetry

        telemetry = get_telemetry()

        is_failure = has_errors or not progress_made

        if is_failure:
            state_data["failures"] = state_data.get("failures", 0) + 1
            state_data["last_failure_time"] = int(time.time())
            telemetry.counter(f"circuit.{self.name}.failure")
        else:
            state_data["failures"] = 0  # Reset on success
            telemetry.counter(f"circuit.{self.name}.success")

        failures = state_data["failures"]
        new_state = current_state

        # State Machine Transitions
        if current_state == CircuitState.CLOSED.value:
            if failures >= CIRCUIT_BREAKER_MAX_FAILURES:
                new_state = CircuitState.OPEN.value
                self._log_transition(new_state, "Too many consecutive failures/no progress")

        elif current_state == CircuitState.HALF_OPEN.value:
            if is_failure:
                new_state = CircuitState.OPEN.value
                self._log_transition(new_state, "Failed in HALF_OPEN state")
            else:
                new_state = CircuitState.CLOSED.value
                self._log_transition(new_state, "Recovered in HALF_OPEN state")

        # If we were OPEN, we only transition to HALF_OPEN via should_allow_request (lazy)
        # But if we executed successfully despite being OPEN (race condition?), close it.
        elif current_state == CircuitState.OPEN.value and not is_failure:
            new_state = CircuitState.CLOSED.value
            self._log_transition(new_state, "Recovered unexpectedly from OPEN")

        state_data["state"] = new_state
        state_data["last_loop_info"] = {
            "loop": loop_num,
            "files_changed": files_changed,
            "has_errors": has_errors,
            "output_length": output_length,
        }

        self._save_state(state_data)

        # Report Metrics
        telemetry.gauge(f"circuit.{self.name}.failures", failures)
        telemetry.gauge(f"circuit.{self.name}.recovery_timeout", self.current_recovery_timeout)

        return 1 if new_state == CircuitState.OPEN.value else 0

    def _transition(self, state_data: dict, new_state: str, reason: str):
        state_data["state"] = new_state
        self._save_state(state_data)
        self._log_transition(new_state, reason)

    def reset(self, reason: str = "Manual reset"):
        state_data = self._load_state()
        state_data["state"] = CircuitState.CLOSED.value
        state_data["failures"] = 0
        state_data["last_failure_time"] = 0
        self._save_state(state_data)
        self._log_transition(CircuitState.CLOSED.value, reason)


# --- Legacy Function Adapters (Preserving API Compatibility) ---


def init_circuit_breaker(project_root: Path | None = None):
    AdaptiveCircuitBreaker(project_root=project_root)


def get_circuit_state(project_root: Path | None = None) -> dict[str, Any]:
    cb = AdaptiveCircuitBreaker(project_root=project_root)
    return cb._load_state()


def record_loop_result(
    loop_num: int,
    files_changed: int,
    has_errors: bool,
    output_length: int,
    project_root: Path | None = None,
) -> int:
    cb = AdaptiveCircuitBreaker(project_root=project_root)
    return cb.record_result(loop_num, files_changed, has_errors, output_length)


def should_halt_execution(project_root: Path | None = None) -> bool:
    """Checks if the circuit breaker is in OPEN state."""
    cb = AdaptiveCircuitBreaker(project_root=project_root)
    # If not allowed, it means it's OPEN and timeout hasn't passed (or just passed and set to HALF_OPEN)
    # Legacy semantics: returns True if HALTED (OPEN).
    # If HALF_OPEN, we should proceed (return False).

    # Check allow_request to trigger lazy transitions
    allowed = cb.should_allow_request()
    return not allowed


def reset_circuit_breaker(reason: str = "Manual reset", project_root: Path | None = None):
    cb = AdaptiveCircuitBreaker(project_root=project_root)
    cb.reset(reason)


def show_circuit_status(project_root: Path | None = None):
    """Displays the current circuit breaker status."""
    from rich.console import Console
    from rich.json import JSON
    from rich.panel import Panel

    console = Console()
    cb = AdaptiveCircuitBreaker(project_root=project_root)
    state_data = cb._load_state()
    try:
        history_data = json.loads(cb.history_file.read_text())
    except Exception:
        history_data = []

    console.print(
        Panel(
            JSON(json.dumps(state_data, indent=4)),
            title="[bold blue]Circuit Breaker Status (Adaptive)[/bold blue]",
            border_style="blue",
        )
    )
    if history_data:
        console.print(
            Panel(
                JSON(json.dumps(history_data[-10:], indent=4)),
                title="[bold blue]Circuit Breaker History[/bold blue]",
                border_style="blue",
            )
        )
