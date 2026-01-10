"""
Tests for backward compatibility stub modules.
These modules are re-exports for backward compatibility.
"""

import pytest


def test_auto_learner_import():
    """Test backward compatibility import for auto_learner."""
    from boring.auto_learner import AutoLearner, ErrorSolutionPair

    assert AutoLearner is not None
    assert ErrorSolutionPair is not None


def test_feedback_learner_import():
    """Test backward compatibility import for feedback_learner."""
    from boring.feedback_learner import FeedbackEntry, FeedbackLearner

    assert FeedbackLearner is not None
    assert FeedbackEntry is not None


def test_quickstart_import():
    """Test backward compatibility import for quickstart."""
    # Import should work without errors
    import boring.quickstart  # noqa: F401

    assert True


def test_dashboard_import():
    """Test backward compatibility import for dashboard."""
    # Import should work without errors
    import boring.dashboard  # noqa: F401

    assert True


def test_web_monitor_import():
    """Test backward compatibility import for web_monitor."""
    # Import should work without errors
    import boring.web_monitor  # noqa: F401

    assert True


def test_main_module():
    """Test __main__ module."""
    from boring.__main__ import app

    assert app is not None
    assert callable(app)
