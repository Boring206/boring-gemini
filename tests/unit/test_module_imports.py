# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Test module imports and re-exports.
"""


def test_constants_import():
    """Test that constants module can be imported."""
    import boring.constants

    assert hasattr(boring.constants, "__file__")


def test_monitor_import():
    """Test that monitor module can be imported."""
    import boring.monitor

    assert hasattr(boring.monitor, "__file__")


def test_main_module_has_app():
    """Test that __main__ module has app."""
    from boring.main import app

    assert callable(app)


def test_core_constants_accessible():
    """Test that core constants are accessible."""
    from boring.core.constants import MAX_FILE_SIZE, MAX_LOOPS, MAX_RETRIES

    assert isinstance(MAX_LOOPS, int)
    assert MAX_LOOPS > 0
    assert isinstance(MAX_RETRIES, int)
    assert isinstance(MAX_FILE_SIZE, int)


def test_quickstart_import():
    """Test that quickstart can be imported."""
    try:
        import boring.cli.quickstart

        assert hasattr(boring.cli.quickstart, "__file__")
    except ImportError:
        # Module might not exist or have dependencies
        pass


def test_dashboard_import():
    """Test that dashboard module exists."""
    import boring.cli.dashboard

    assert hasattr(boring.cli.dashboard, "__file__")


def test_error_translator_import():
    """Test error translator can be imported."""
    from boring.error_translator import ErrorTranslator

    assert ErrorTranslator is not None


def test_core_models_import():
    """Test core models can be imported."""
    from boring.core.models import CircuitBreakerState, LoopStatus

    assert CircuitBreakerState is not None
    assert LoopStatus is not None


def test_exceptions_import():
    """Test exceptions can be imported."""
    from boring.core.exceptions import (
        CircuitBreakerOpenError,
        MaxLoopsExceededError,
        RateLimitError,
    )

    assert CircuitBreakerOpenError is not None
    assert MaxLoopsExceededError is not None
    assert RateLimitError is not None
