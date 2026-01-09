"""
Core Module for Boring V4.0 (DEPRECATED Compatibility Layer)

⚠️ DEPRECATION NOTICE:
This module is deprecated and will be removed in V5.0.
Please import directly from the appropriate modules:

- from .circuit import should_halt_execution, reset_circuit_breaker, ...
- from .logger import log_status, update_status, get_log_tail
- from .limiter import can_make_call, increment_call_counter, ...

Modules:
- circuit.py: Circuit Breaker logic
- logger.py: Logging and status management
- limiter.py: Rate limiting and exit detection
"""

import warnings

# Re-export from circuit.py (with deprecation)
# Legacy constants (for backward compatibility)
from .circuit import (
    CB_HISTORY_FILE,
    CB_STATE_FILE,
    CIRCUIT_BREAKER_MAX_FAILURES,
    CIRCUIT_BREAKER_RESET_TIMEOUT,
    CircuitState,
    get_circuit_state,
    init_circuit_breaker,
    record_loop_result,
    reset_circuit_breaker,
    should_halt_execution,
    show_circuit_status,
)

# Re-export from limiter.py (with deprecation)
from .limiter import (
    MAX_CONSECUTIVE_DONE_SIGNALS,
    MAX_CONSECUTIVE_TEST_LOOPS,
    can_make_call,
    get_calls_made,
    increment_call_counter,
    init_call_tracking,
    should_exit_gracefully,
    wait_for_reset,
)

# Re-export from logger.py (with deprecation)
from .logger import (
    get_log_tail,
    log_status,
    update_status,
)

# Configuration constants
TEST_PERCENTAGE_THRESHOLD = 30  # Not directly used, kept for reference


def __getattr__(name: str):
    """Emit deprecation warning when accessing attributes from this module."""
    # This is called when an attribute is accessed that doesn't exist directly
    # Since we're re-exporting, this will only catch truly missing attributes
    warnings.warn(
        "Importing from 'boring.core' is deprecated. "
        "Please import directly from the appropriate module "
        "(.circuit, .logger, or .limiter) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    raise AttributeError(f"module 'boring.core' has no attribute '{name}'")


__all__ = [
    # Circuit Breaker
    "CB_STATE_FILE",
    "CB_HISTORY_FILE",
    "CircuitState",
    "init_circuit_breaker",
    "record_loop_result",
    "should_halt_execution",
    "reset_circuit_breaker",
    "show_circuit_status",
    "get_circuit_state",
    "CIRCUIT_BREAKER_MAX_FAILURES",
    "CIRCUIT_BREAKER_RESET_TIMEOUT",
    # Logging
    "log_status",
    "update_status",
    "get_log_tail",
    # Rate Limiting
    "init_call_tracking",
    "get_calls_made",
    "increment_call_counter",
    "can_make_call",
    "wait_for_reset",
    "should_exit_gracefully",
    "MAX_CONSECUTIVE_TEST_LOOPS",
    "MAX_CONSECUTIVE_DONE_SIGNALS",
    # Legacy
    "TEST_PERCENTAGE_THRESHOLD",
]
