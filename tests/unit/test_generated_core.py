"""
Unit tests for boring.core module (deprecated compatibility layer).

This module tests the deprecated core.py compatibility layer that re-exports
functions from circuit.py, logger.py, and limiter.py.
"""

import warnings

import pytest

from boring.core import (
    CB_HISTORY_FILE,
    CB_STATE_FILE,
    CIRCUIT_BREAKER_MAX_FAILURES,
    CIRCUIT_BREAKER_RESET_TIMEOUT,
    MAX_CONSECUTIVE_DONE_SIGNALS,
    MAX_CONSECUTIVE_TEST_LOOPS,
    TEST_PERCENTAGE_THRESHOLD,
    CircuitState,
    can_make_call,
    get_calls_made,
    get_circuit_state,
    get_log_tail,
    increment_call_counter,
    init_call_tracking,
    init_circuit_breaker,
    log_status,
    record_loop_result,
    reset_circuit_breaker,
    should_exit_gracefully,
    should_halt_execution,
    show_circuit_status,
    update_status,
    wait_for_reset,
)


class TestCoreReExports:
    """Test that core.py correctly re-exports functions and constants."""

    def test_circuit_constants_exported(self):
        """Test that circuit breaker constants are exported."""
        assert CB_HISTORY_FILE is not None
        assert CB_STATE_FILE is not None
        assert CIRCUIT_BREAKER_MAX_FAILURES is not None
        assert CIRCUIT_BREAKER_RESET_TIMEOUT is not None

    def test_limiter_constants_exported(self):
        """Test that limiter constants are exported."""
        assert MAX_CONSECUTIVE_DONE_SIGNALS is not None
        assert MAX_CONSECUTIVE_TEST_LOOPS is not None

    def test_legacy_constant_exported(self):
        """Test that legacy TEST_PERCENTAGE_THRESHOLD is exported."""
        assert TEST_PERCENTAGE_THRESHOLD == 30

    def test_circuit_state_exported(self):
        """Test that CircuitState enum is exported."""
        assert CircuitState is not None
        assert hasattr(CircuitState, "CLOSED")
        assert hasattr(CircuitState, "OPEN")
        assert hasattr(CircuitState, "HALF_OPEN")

    def test_circuit_functions_exported(self):
        """Test that circuit breaker functions are exported."""
        assert callable(get_circuit_state)
        assert callable(init_circuit_breaker)
        assert callable(record_loop_result)
        assert callable(reset_circuit_breaker)
        assert callable(should_halt_execution)
        assert callable(show_circuit_status)

    def test_limiter_functions_exported(self):
        """Test that limiter functions are exported."""
        assert callable(can_make_call)
        assert callable(get_calls_made)
        assert callable(increment_call_counter)
        assert callable(init_call_tracking)
        assert callable(should_exit_gracefully)
        assert callable(wait_for_reset)

    def test_logger_functions_exported(self):
        """Test that logger functions are exported."""
        assert callable(log_status)
        assert callable(update_status)
        assert callable(get_log_tail)


class TestCoreGetAttr:
    """Test __getattr__ deprecation warning behavior."""

    def test_getattr_missing_attribute_raises_warning(self):
        """Test that accessing missing attributes emits deprecation warning."""
        import boring.core

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                _ = boring.core.nonexistent_attribute
            except AttributeError:
                pass

            # Should have emitted a deprecation warning
            assert len(w) > 0
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)

    def test_getattr_missing_attribute_raises_attribute_error(self):
        """Test that accessing missing attributes raises AttributeError."""
        import boring.core

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(
                AttributeError, match="module 'boring.core' has no attribute 'nonexistent'"
            ):
                _ = boring.core.nonexistent

    def test_getattr_existing_attribute_no_warning(self):
        """Test that accessing existing attributes doesn't emit warning."""
        import boring.core

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _ = boring.core.TEST_PERCENTAGE_THRESHOLD

            # Should not emit deprecation warning for existing attributes
            deprecation_warnings = [
                warning for warning in w if issubclass(warning.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) == 0

    def test_getattr_re_exported_functions_accessible(self):
        """Test that re-exported functions are accessible without warning."""
        import boring.core

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _ = boring.core.should_halt_execution
            _ = boring.core.log_status
            _ = boring.core.can_make_call

            # Should not emit deprecation warning for re-exported functions
            deprecation_warnings = [
                warning for warning in w if issubclass(warning.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) == 0


class TestCoreImports:
    """Test that imports from core.py work correctly."""

    def test_import_circuit_functions(self):
        """Test importing circuit functions from core."""
        from boring.core import get_circuit_state, should_halt_execution

        assert callable(get_circuit_state)
        assert callable(should_halt_execution)

    def test_import_limiter_functions(self):
        """Test importing limiter functions from core."""
        from boring.core import can_make_call, get_calls_made

        assert callable(can_make_call)
        assert callable(get_calls_made)

    def test_import_logger_functions(self):
        """Test importing logger functions from core."""
        from boring.core import log_status, update_status

        assert callable(log_status)
        assert callable(update_status)

    def test_import_all_constants(self):
        """Test importing all constants from core."""
        from boring.core import (
            CB_HISTORY_FILE,
            CB_STATE_FILE,
            CIRCUIT_BREAKER_MAX_FAILURES,
            CIRCUIT_BREAKER_RESET_TIMEOUT,
            MAX_CONSECUTIVE_DONE_SIGNALS,
            MAX_CONSECUTIVE_TEST_LOOPS,
            TEST_PERCENTAGE_THRESHOLD,
        )

        assert all(
            [
                CB_HISTORY_FILE,
                CB_STATE_FILE,
                CIRCUIT_BREAKER_MAX_FAILURES,
                CIRCUIT_BREAKER_RESET_TIMEOUT,
                MAX_CONSECUTIVE_DONE_SIGNALS,
                MAX_CONSECUTIVE_TEST_LOOPS,
                TEST_PERCENTAGE_THRESHOLD,
            ]
        )
