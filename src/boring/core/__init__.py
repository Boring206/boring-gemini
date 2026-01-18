"""
Core Module for Boring V4.0 (DEPRECATED Compatibility Layer)

⚠️ DEPRECATION NOTICE:
This module is deprecated and will be removed in a future release.
Please import directly from the appropriate modules:

- from .circuit import should_halt_execution, reset_circuit_breaker, ...
- from .logger import log_status, update_status, get_log_tail
- from .limiter import can_make_call, increment_call_counter, ...
"""

import warnings
from typing import Any

# Map attributes to their source modules
_RE_EXPORTS = {
    # From .circuit
    "CB_HISTORY_FILE": ".circuit",
    "CB_STATE_FILE": ".circuit",
    "CIRCUIT_BREAKER_MAX_FAILURES": ".circuit",
    "CIRCUIT_BREAKER_RESET_TIMEOUT": ".circuit",
    "CircuitState": ".circuit",
    "get_circuit_state": ".circuit",
    "init_circuit_breaker": ".circuit",
    "record_loop_result": ".circuit",
    "reset_circuit_breaker": ".circuit",
    "should_halt_execution": ".circuit",
    "show_circuit_status": ".circuit",
    # From .limiter
    "MAX_CONSECUTIVE_DONE_SIGNALS": ".limiter",
    "MAX_CONSECUTIVE_TEST_LOOPS": ".limiter",
    "can_make_call": ".limiter",
    "get_calls_made": ".limiter",
    "increment_call_counter": ".limiter",
    "init_call_tracking": ".limiter",
    "should_exit_gracefully": ".limiter",
    "wait_for_reset": ".limiter",
    # From .logger
    "get_log_tail": ".logger",
    "log_status": ".logger",
    "update_status": ".logger",
}

# Configuration constants
TEST_PERCENTAGE_THRESHOLD = 30


def __getattr__(name: str) -> Any:
    """Lazy re-export with deprecation warning."""
    if name in _RE_EXPORTS:
        warnings.warn(
            f"Importing '{name}' from 'boring.core' is deprecated. "
            f"Please import from 'boring.core{_RE_EXPORTS[name]}' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        import importlib

        module = importlib.import_module(_RE_EXPORTS[name], __package__)
        return getattr(module, name)

    raise AttributeError(f"module 'boring.core' has no attribute '{name}'")


__all__ = list(_RE_EXPORTS.keys()) + ["TEST_PERCENTAGE_THRESHOLD"]
