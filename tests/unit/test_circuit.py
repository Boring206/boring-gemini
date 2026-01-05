"""
Tests for circuit breaker module.
"""

import json


class TestCircuitState:
    """Tests for CircuitState enum."""

    def test_circuit_state_values(self):
        """Test that circuit state values exist."""
        from boring.circuit import CircuitState

        assert CircuitState.CLOSED.value == "CLOSED"
        assert CircuitState.OPEN.value == "OPEN"
        assert CircuitState.HALF_OPEN.value == "HALF_OPEN"


class TestLoopInfo:
    """Tests for LoopInfo dataclass."""

    def test_loop_info_creation(self):
        """Test creating a LoopInfo."""
        from boring.circuit import LoopInfo

        info = LoopInfo(loop=1, files_changed=5, has_errors=False, output_length=100)

        assert info.loop == 1
        assert info.files_changed == 5
        assert info.has_errors is False
        assert info.output_length == 100


class TestInitCircuitBreaker:
    """Tests for init_circuit_breaker function."""

    def test_init_creates_state_file(self, tmp_path, monkeypatch):
        """Test that init creates state file."""
        from boring import circuit

        state_file = tmp_path / ".circuit_breaker_state"
        history_file = tmp_path / ".circuit_breaker_history"

        monkeypatch.setattr(circuit, "CB_STATE_FILE", state_file)
        monkeypatch.setattr(circuit, "CB_HISTORY_FILE", history_file)

        circuit.init_circuit_breaker()

        assert state_file.exists()
        assert history_file.exists()

    def test_init_sets_closed_state(self, tmp_path, monkeypatch):
        """Test that init sets CLOSED state."""
        from boring import circuit

        state_file = tmp_path / ".circuit_breaker_state"
        history_file = tmp_path / ".circuit_breaker_history"

        monkeypatch.setattr(circuit, "CB_STATE_FILE", state_file)
        monkeypatch.setattr(circuit, "CB_HISTORY_FILE", history_file)

        circuit.init_circuit_breaker()

        state = json.loads(state_file.read_text())
        assert state["state"] == "CLOSED"
        assert state["failures"] == 0


class TestGetCircuitState:
    """Tests for get_circuit_state function."""

    def test_get_circuit_state_returns_dict(self, tmp_path, monkeypatch):
        """Test that get_circuit_state returns a dict."""
        from boring import circuit

        state_file = tmp_path / ".circuit_breaker_state"
        history_file = tmp_path / ".circuit_breaker_history"

        monkeypatch.setattr(circuit, "CB_STATE_FILE", state_file)
        monkeypatch.setattr(circuit, "CB_HISTORY_FILE", history_file)

        state = circuit.get_circuit_state()

        assert isinstance(state, dict)
        assert "state" in state
        assert "failures" in state


class TestRecordLoopResult:
    """Tests for record_loop_result function."""

    def test_record_success(self, tmp_path, monkeypatch):
        """Test recording a successful loop."""
        from boring import circuit

        state_file = tmp_path / ".circuit_breaker_state"
        history_file = tmp_path / ".circuit_breaker_history"

        monkeypatch.setattr(circuit, "CB_STATE_FILE", state_file)
        monkeypatch.setattr(circuit, "CB_HISTORY_FILE", history_file)

        result = circuit.record_loop_result(
            loop_num=1, files_changed=5, has_errors=False, output_length=100
        )

        assert result == 0  # OK to continue

    def test_record_failure(self, tmp_path, monkeypatch):
        """Test recording a failed loop."""
        from boring import circuit

        state_file = tmp_path / ".circuit_breaker_state"
        history_file = tmp_path / ".circuit_breaker_history"

        monkeypatch.setattr(circuit, "CB_STATE_FILE", state_file)
        monkeypatch.setattr(circuit, "CB_HISTORY_FILE", history_file)

        result = circuit.record_loop_result(
            loop_num=1, files_changed=0, has_errors=True, output_length=0
        )

        # First failure shouldn't halt
        assert result == 0


class TestShouldHaltExecution:
    """Tests for should_halt_execution function."""

    def test_should_not_halt_initially(self, tmp_path, monkeypatch):
        """Test that execution should not halt initially."""
        from boring import circuit

        state_file = tmp_path / ".circuit_breaker_state"
        history_file = tmp_path / ".circuit_breaker_history"

        monkeypatch.setattr(circuit, "CB_STATE_FILE", state_file)
        monkeypatch.setattr(circuit, "CB_HISTORY_FILE", history_file)

        result = circuit.should_halt_execution()

        assert result is False


class TestResetCircuitBreaker:
    """Tests for reset_circuit_breaker function."""

    def test_reset_sets_closed_state(self, tmp_path, monkeypatch):
        """Test that reset sets CLOSED state."""
        from boring import circuit

        state_file = tmp_path / ".circuit_breaker_state"
        history_file = tmp_path / ".circuit_breaker_history"

        monkeypatch.setattr(circuit, "CB_STATE_FILE", state_file)
        monkeypatch.setattr(circuit, "CB_HISTORY_FILE", history_file)

        # First init
        circuit.init_circuit_breaker()

        # Record some failures
        for _ in range(5):
            circuit.record_loop_result(1, 0, True, 0)

        # Reset
        circuit.reset_circuit_breaker("Test reset")

        state = circuit.get_circuit_state()
        assert state["state"] == "CLOSED"
        assert state["failures"] == 0
