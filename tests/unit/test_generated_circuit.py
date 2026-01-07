# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.circuit module.
"""

import json
import time

import pytest

from boring.circuit import (
    CIRCUIT_BREAKER_MAX_FAILURES,
    CIRCUIT_BREAKER_RESET_TIMEOUT,
    CircuitState,
    LoopInfo,
    get_circuit_state,
    init_circuit_breaker,
    record_loop_result,
    reset_circuit_breaker,
    should_halt_execution,
    show_circuit_status,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_dir(tmp_path, monkeypatch):
    """Create a temporary directory and patch state files."""
    # Patch the state file paths to use temp directory
    monkeypatch.setattr("boring.circuit.CB_STATE_FILE", tmp_path / ".circuit_breaker_state")
    monkeypatch.setattr("boring.circuit.CB_HISTORY_FILE", tmp_path / ".circuit_breaker_history")
    return tmp_path


# =============================================================================
# ENUM TESTS
# =============================================================================


class TestCircuitState:
    """Tests for CircuitState enum."""

    def test_circuit_state_values(self):
        """Test CircuitState enum values."""
        assert CircuitState.CLOSED.value == "CLOSED"
        assert CircuitState.OPEN.value == "OPEN"
        assert CircuitState.HALF_OPEN.value == "HALF_OPEN"


# =============================================================================
# LOOP INFO TESTS
# =============================================================================


class TestLoopInfo:
    """Tests for LoopInfo dataclass."""

    def test_loop_info_creation(self):
        """Test LoopInfo creation."""
        info = LoopInfo(loop=1, files_changed=2, has_errors=False, output_length=100)
        assert info.loop == 1
        assert info.files_changed == 2
        assert info.has_errors is False
        assert info.output_length == 100


# =============================================================================
# CIRCUIT BREAKER TESTS
# =============================================================================


class TestInitCircuitBreaker:
    """Tests for init_circuit_breaker function."""

    def test_init_circuit_breaker_new(self, temp_dir):
        """Test init_circuit_breaker creates new state file."""
        init_circuit_breaker()

        state_file = temp_dir / ".circuit_breaker_state"
        assert state_file.exists()
        state = json.loads(state_file.read_text())
        assert state["state"] == CircuitState.CLOSED.value
        assert state["failures"] == 0

    def test_init_circuit_breaker_existing(self, temp_dir):
        """Test init_circuit_breaker with existing state file."""
        # Create existing state
        state = {
            "state": CircuitState.OPEN.value,
            "failures": 5,
            "last_failure_time": 1234567890,
            "last_loop_info": {
                "loop": 1,
                "files_changed": 0,
                "has_errors": True,
                "output_length": 0,
            },
        }
        (temp_dir / ".circuit_breaker_state").write_text(json.dumps(state))

        init_circuit_breaker()

        # Should not overwrite existing state
        # Should not overwrite existing state
        state_file = temp_dir / ".circuit_breaker_state"
        new_state = json.loads(state_file.read_text())
        assert new_state["state"] == CircuitState.OPEN.value

    def test_init_circuit_breaker_creates_history(self, temp_dir):
        """Test init_circuit_breaker creates history file."""
        init_circuit_breaker()

        history_file = temp_dir / ".circuit_breaker_history"
        assert history_file.exists()
        history = json.loads(history_file.read_text())
        assert isinstance(history, list)


class TestGetCircuitState:
    """Tests for get_circuit_state function."""

    def test_get_circuit_state(self, temp_dir):
        """Test get_circuit_state returns state."""
        init_circuit_breaker()

        state = get_circuit_state()
        assert isinstance(state, dict)
        assert "state" in state
        assert "failures" in state


class TestRecordLoopResult:
    """Tests for record_loop_result function."""

    def test_record_loop_result_success(self, temp_dir):
        """Test record_loop_result with successful loop."""
        init_circuit_breaker()

        result = record_loop_result(
            loop_num=1, files_changed=2, has_errors=False, output_length=100
        )
        assert result == 0  # Should not halt

        state = get_circuit_state()
        assert state["failures"] == 0

    def test_record_loop_result_failure(self, temp_dir):
        """Test record_loop_result with failed loop."""
        init_circuit_breaker()

        result = record_loop_result(loop_num=1, files_changed=0, has_errors=True, output_length=0)
        assert result == 0  # Not enough failures yet

        state = get_circuit_state()
        assert state["failures"] == 1

    def test_record_loop_result_opens_circuit(self, temp_dir):
        """Test record_loop_result opens circuit after max failures."""
        init_circuit_breaker()

        # Record multiple failures
        for i in range(CIRCUIT_BREAKER_MAX_FAILURES):
            record_loop_result(loop_num=i, files_changed=0, has_errors=True, output_length=0)

        state = get_circuit_state()
        assert state["state"] == CircuitState.OPEN.value

        # Next call should return halt signal
        result = record_loop_result(loop_num=4, files_changed=0, has_errors=True, output_length=0)
        assert result == 1  # Should halt

    def test_record_loop_result_progress_resets_failures(self, temp_dir):
        """Test record_loop_result resets failures on progress."""
        init_circuit_breaker()

        # Record a failure
        record_loop_result(loop_num=1, files_changed=0, has_errors=True, output_length=0)

        # Record success with progress
        record_loop_result(loop_num=2, files_changed=1, has_errors=False, output_length=100)

        state = get_circuit_state()
        assert state["failures"] == 0

    def test_record_loop_result_half_open_recovery(self, temp_dir):
        """Test record_loop_result recovery from HALF_OPEN state."""
        init_circuit_breaker()

        # Open the circuit
        for i in range(CIRCUIT_BREAKER_MAX_FAILURES):
            record_loop_result(loop_num=i, files_changed=0, has_errors=True, output_length=0)

        # Move to HALF_OPEN
        state_data = get_circuit_state()
        state_data["state"] = CircuitState.HALF_OPEN.value
        state_data["last_failure_time"] = int(time.time()) - CIRCUIT_BREAKER_RESET_TIMEOUT - 1
        (temp_dir / ".circuit_breaker_state").write_text(json.dumps(state_data))

        # Record success in HALF_OPEN
        result = record_loop_result(
            loop_num=10, files_changed=1, has_errors=False, output_length=100
        )
        assert result == 0

        state = get_circuit_state()
        assert state["state"] == CircuitState.CLOSED.value

    def test_record_loop_result_half_open_failure(self, temp_dir):
        """Test record_loop_result failure in HALF_OPEN state."""
        init_circuit_breaker()

        # Open the circuit
        for i in range(CIRCUIT_BREAKER_MAX_FAILURES):
            record_loop_result(loop_num=i, files_changed=0, has_errors=True, output_length=0)

        # Move to HALF_OPEN
        state_data = get_circuit_state()
        # Move to HALF_OPEN
        state_data = get_circuit_state()
        state_data["state"] = CircuitState.HALF_OPEN.value
        state_data["last_failure_time"] = int(time.time()) - CIRCUIT_BREAKER_RESET_TIMEOUT - 1
        (temp_dir / ".circuit_breaker_state").write_text(json.dumps(state_data))

        # Record failure in HALF_OPEN
        result = record_loop_result(loop_num=10, files_changed=0, has_errors=True, output_length=0)
        assert result == 1

        state = get_circuit_state()
        assert state["state"] == CircuitState.OPEN.value


class TestShouldHaltExecution:
    """Tests for should_halt_execution function."""

    def test_should_halt_execution_closed(self, temp_dir):
        """Test should_halt_execution when circuit is CLOSED."""
        init_circuit_breaker()

        result = should_halt_execution()
        assert result is False

    def test_should_halt_execution_open(self, temp_dir):
        """Test should_halt_execution when circuit is OPEN."""
        init_circuit_breaker()

        # Open the circuit
        for i in range(CIRCUIT_BREAKER_MAX_FAILURES):
            record_loop_result(loop_num=i, files_changed=0, has_errors=True, output_length=0)

        result = should_halt_execution()
        assert result is True


class TestResetCircuitBreaker:
    """Tests for reset_circuit_breaker function."""

    def test_reset_circuit_breaker(self, temp_dir):
        """Test reset_circuit_breaker resets state."""
        init_circuit_breaker()

        # Open the circuit
        for i in range(CIRCUIT_BREAKER_MAX_FAILURES):
            record_loop_result(loop_num=i, files_changed=0, has_errors=True, output_length=0)

        # Reset
        reset_circuit_breaker("Test reset")

        state = get_circuit_state()
        assert state["state"] == CircuitState.CLOSED.value
        assert state["failures"] == 0

    def test_reset_circuit_breaker_logs(self, temp_dir):
        """Test reset_circuit_breaker logs to history."""
        init_circuit_breaker()

        reset_circuit_breaker("Test reset")

        history_file = temp_dir / ".circuit_breaker_history"
        history = json.loads(history_file.read_text())
        assert len(history) > 0
        assert history[-1]["state"] == CircuitState.CLOSED.value


class TestShowCircuitStatus:
    """Tests for show_circuit_status function."""

    def test_show_circuit_status(self, temp_dir):
        """Test show_circuit_status displays status."""
        init_circuit_breaker()

        # Should not raise exception
        show_circuit_status()


# =============================================================================
# CONSTANTS TESTS
# =============================================================================


class TestConstants:
    """Tests for module constants."""

    def test_circuit_breaker_max_failures(self):
        """Test CIRCUIT_BREAKER_MAX_FAILURES constant."""
        assert CIRCUIT_BREAKER_MAX_FAILURES == 3

    def test_circuit_breaker_reset_timeout(self):
        """Test CIRCUIT_BREAKER_RESET_TIMEOUT constant."""
        assert CIRCUIT_BREAKER_RESET_TIMEOUT == 600
