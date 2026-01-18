import time

import pytest

from boring.core.circuit import (
    CIRCUIT_BREAKER_BASE_TIMEOUT,
    CIRCUIT_BREAKER_MAX_FAILURES,
    AdaptiveCircuitBreaker,
    CircuitState,
)


@pytest.fixture
def circuit_root(tmp_path):
    return tmp_path


def test_exponential_backoff_calculation(circuit_root):
    cb = AdaptiveCircuitBreaker(project_root=circuit_root)

    # Simulate failures
    state = cb._load_state()
    # 0 failures -> Timeout should be base (or not applicable)
    assert cb.current_recovery_timeout == CIRCUIT_BREAKER_BASE_TIMEOUT

    # 3 failures (Threshold) -> Timeout = Base
    state["failures"] = CIRCUIT_BREAKER_MAX_FAILURES
    cb._save_state(state)
    assert cb.current_recovery_timeout == CIRCUIT_BREAKER_BASE_TIMEOUT

    # 4 failures -> Timeout = Base * 2^0 = Base (Wait, logic check)
    # effective_failures = failures - THRESHOLD + 1
    # If 4 failures, Threshold=3. Effective = 4 - 3 + 1 = 2?
    # No, usually 1st retry after open is base. 2nd is 2x.

    # Let's check my implementation:
    # effective_failures = max(0, failures - CIRCUIT_BREAKER_MAX_FAILURES + 1)
    # timeout = base * (2 ** (effective - 1)) if effective > 0 else base

    # Failures=3 (Just opened). Effective = 3-3+1 = 1.
    # timeout = base * 2^(1-1) = base * 1 = base. Correct.

    # Failures=4 (Failed once in HALF_OPEN). Effective = 2.
    # timeout = base * 2^(1) = 2 * base. Correct.

    state["failures"] = CIRCUIT_BREAKER_MAX_FAILURES + 1
    cb._save_state(state)
    assert cb.current_recovery_timeout == CIRCUIT_BREAKER_BASE_TIMEOUT * 2.0

    state["failures"] = CIRCUIT_BREAKER_MAX_FAILURES + 2
    cb._save_state(state)
    assert cb.current_recovery_timeout == CIRCUIT_BREAKER_BASE_TIMEOUT * 4.0


def test_state_transitions(circuit_root):
    cb = AdaptiveCircuitBreaker(project_root=circuit_root)

    # 1. Closed -> Open
    for i in range(CIRCUIT_BREAKER_MAX_FAILURES):
        cb.record_result(loop_num=i, files_changed=0, has_errors=True, output_length=0)

    state = cb._load_state()
    assert state["state"] == CircuitState.OPEN.value
    assert state["failures"] == CIRCUIT_BREAKER_MAX_FAILURES

    # 2. Open -> Half Open (Time travel)
    # Force time passed > timeout
    state["last_failure_time"] = int(time.time()) - int(cb.current_recovery_timeout * 2)
    cb._save_state(state)

    # should_allow_request triggers transition check
    allowed = cb.should_allow_request()
    assert allowed is True

    # Verify state is NOT strictly HALF_OPEN in file yet?
    # My implementation lazily transitions in `should_allow_request`?
    # "self._transition(state_data, CircuitState.HALF_OPEN.value..."
    # Yes, it updates state.
    state = cb._load_state()
    assert state["state"] == CircuitState.HALF_OPEN.value

    # 3. Half Open -> Open (Failure)
    cb.record_result(loop_num=10, files_changed=0, has_errors=True, output_length=0)
    state = cb._load_state()
    assert state["state"] == CircuitState.OPEN.value
    assert state["failures"] == CIRCUIT_BREAKER_MAX_FAILURES + 1

    # 4. Success resets
    cb.record_result(loop_num=11, files_changed=1, has_errors=False, output_length=100)
    state = cb._load_state()
    assert state["state"] == CircuitState.CLOSED.value
    assert state["failures"] == 0
