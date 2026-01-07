# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.limiter module.
"""

import json
from datetime import datetime
from unittest.mock import patch

import pytest

from boring.limiter import (
    MAX_CONSECUTIVE_DONE_SIGNALS,
    MAX_CONSECUTIVE_TEST_LOOPS,
    can_make_call,
    get_calls_made,
    increment_call_counter,
    init_call_tracking,
    should_exit_gracefully,
    wait_for_reset,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path


# =============================================================================
# INIT CALL TRACKING TESTS
# =============================================================================


class TestInitCallTracking:
    """Tests for init_call_tracking function."""

    def test_init_call_tracking_new_hour(self, temp_dir):
        """Test init_call_tracking for new hour."""
        call_count_file = temp_dir / "calls.txt"
        timestamp_file = temp_dir / "timestamp.txt"
        exit_signals_file = temp_dir / "exit_signals.json"

        init_call_tracking(call_count_file, timestamp_file, exit_signals_file)

        assert call_count_file.exists()
        assert call_count_file.read_text().strip() == "0"
        assert timestamp_file.exists()
        assert exit_signals_file.exists()

    def test_init_call_tracking_same_hour(self, temp_dir):
        """Test init_call_tracking for same hour."""
        call_count_file = temp_dir / "calls.txt"
        timestamp_file = temp_dir / "timestamp.txt"
        exit_signals_file = temp_dir / "exit_signals.json"

        # Set up existing files
        call_count_file.write_text("5")
        current_hour = datetime.now().strftime("%Y%m%d%H")
        timestamp_file.write_text(current_hour)

        init_call_tracking(call_count_file, timestamp_file, exit_signals_file)

        # Should not reset
        assert call_count_file.read_text().strip() == "5"

    def test_init_call_tracking_exit_signals_exists(self, temp_dir):
        """Test init_call_tracking when exit_signals file exists."""
        call_count_file = temp_dir / "calls.txt"
        timestamp_file = temp_dir / "timestamp.txt"
        exit_signals_file = temp_dir / "exit_signals.json"

        exit_signals_file.write_text('{"test_only_loops": [1, 2]}')

        init_call_tracking(call_count_file, timestamp_file, exit_signals_file)

        # Should not overwrite existing file
        data = json.loads(exit_signals_file.read_text())
        assert "test_only_loops" in data


# =============================================================================
# CALL TRACKING TESTS
# =============================================================================


class TestGetCallsMade:
    """Tests for get_calls_made function."""

    def test_get_calls_made_existing(self, temp_dir):
        """Test get_calls_made with existing file."""
        call_count_file = temp_dir / "calls.txt"
        call_count_file.write_text("10")

        count = get_calls_made(call_count_file)
        assert count == 10

    def test_get_calls_made_nonexistent(self, temp_dir):
        """Test get_calls_made with nonexistent file."""
        call_count_file = temp_dir / "calls.txt"

        count = get_calls_made(call_count_file)
        assert count == 0

    def test_get_calls_made_invalid_content(self, temp_dir):
        """Test get_calls_made with invalid content."""
        call_count_file = temp_dir / "calls.txt"
        call_count_file.write_text("invalid")

        count = get_calls_made(call_count_file)
        assert count == 0


class TestIncrementCallCounter:
    """Tests for increment_call_counter function."""

    def test_increment_call_counter_new(self, temp_dir):
        """Test increment_call_counter with new file."""
        call_count_file = temp_dir / "calls.txt"

        count = increment_call_counter(call_count_file)
        assert count == 1
        assert call_count_file.read_text().strip() == "1"

    def test_increment_call_counter_existing(self, temp_dir):
        """Test increment_call_counter with existing count."""
        call_count_file = temp_dir / "calls.txt"
        call_count_file.write_text("5")

        count = increment_call_counter(call_count_file)
        assert count == 6
        assert call_count_file.read_text().strip() == "6"


class TestCanMakeCall:
    """Tests for can_make_call function."""

    def test_can_make_call_under_limit(self, temp_dir):
        """Test can_make_call when under limit."""
        call_count_file = temp_dir / "calls.txt"
        call_count_file.write_text("5")

        result = can_make_call(call_count_file, max_calls_per_hour=10)
        assert result is True

    def test_can_make_call_at_limit(self, temp_dir):
        """Test can_make_call when at limit."""
        call_count_file = temp_dir / "calls.txt"
        call_count_file.write_text("10")

        result = can_make_call(call_count_file, max_calls_per_hour=10)
        assert result is False

    def test_can_make_call_over_limit(self, temp_dir):
        """Test can_make_call when over limit."""
        call_count_file = temp_dir / "calls.txt"
        call_count_file.write_text("15")

        result = can_make_call(call_count_file, max_calls_per_hour=10)
        assert result is False


class TestWaitForReset:
    """Tests for wait_for_reset function."""

    @patch("boring.limiter.time.sleep")
    @patch("boring.limiter.init_call_tracking")
    def test_wait_for_reset(self, mock_init, mock_sleep, temp_dir):
        """Test wait_for_reset function."""
        call_count_file = temp_dir / "calls.txt"
        timestamp_file = temp_dir / "timestamp.txt"
        call_count_file.write_text("10")

        wait_for_reset(call_count_file, timestamp_file, max_calls_per_hour=10)

        # Should call init_call_tracking
        mock_init.assert_called_once()


# =============================================================================
# EXIT DETECTION TESTS
# =============================================================================


class TestShouldExitGracefully:
    """Tests for should_exit_gracefully function."""

    def test_should_exit_gracefully_nonexistent(self, temp_dir):
        """Test should_exit_gracefully with nonexistent file."""
        exit_signals_file = temp_dir / "exit_signals.json"

        result = should_exit_gracefully(exit_signals_file)
        assert result is None

    def test_should_exit_gracefully_test_saturation(self, temp_dir):
        """Test should_exit_gracefully with test saturation."""
        exit_signals_file = temp_dir / "exit_signals.json"
        signals_data = {
            "test_only_loops": [1, 2, 3],
            "done_signals": [],
            "completion_indicators": [],
        }
        exit_signals_file.write_text(json.dumps(signals_data))

        result = should_exit_gracefully(exit_signals_file)
        assert result == "test_saturation"

    def test_should_exit_gracefully_completion_signals(self, temp_dir):
        """Test should_exit_gracefully with completion signals."""
        exit_signals_file = temp_dir / "exit_signals.json"
        signals_data = {
            "test_only_loops": [],
            "done_signals": [1, 2],
            "completion_indicators": [],
        }
        exit_signals_file.write_text(json.dumps(signals_data))

        result = should_exit_gracefully(exit_signals_file)
        assert result == "completion_signals"

    def test_should_exit_gracefully_project_complete(self, temp_dir):
        """Test should_exit_gracefully with project complete."""
        exit_signals_file = temp_dir / "exit_signals.json"
        signals_data = {
            "test_only_loops": [],
            "done_signals": [],
            "completion_indicators": ["complete", "done"],
        }
        exit_signals_file.write_text(json.dumps(signals_data))

        result = should_exit_gracefully(exit_signals_file)
        assert result == "project_complete"

    def test_should_exit_gracefully_plan_complete(self, temp_dir):
        """Test should_exit_gracefully with fix_plan.md complete."""
        exit_signals_file = temp_dir / "exit_signals.json"
        signals_data = {
            "test_only_loops": [],
            "done_signals": [],
            "completion_indicators": [],
        }
        exit_signals_file.write_text(json.dumps(signals_data))

        fix_plan_file = temp_dir / "@fix_plan.md"
        fix_plan_file.write_text("- [x] Task 1\n- [x] Task 2")

        with patch("boring.limiter.Path", return_value=fix_plan_file):
            with patch("boring.limiter.log_status"):
                result = should_exit_gracefully(exit_signals_file)
                assert result == "plan_complete"

    def test_should_exit_gracefully_no_exit(self, temp_dir):
        """Test should_exit_gracefully with no exit conditions."""
        exit_signals_file = temp_dir / "exit_signals.json"
        signals_data = {
            "test_only_loops": [1],
            "done_signals": [1],
            "completion_indicators": [],
        }
        exit_signals_file.write_text(json.dumps(signals_data))

        result = should_exit_gracefully(exit_signals_file)
        assert result is None


# =============================================================================
# CONSTANTS TESTS
# =============================================================================


class TestConstants:
    """Tests for module constants."""

    def test_max_consecutive_test_loops(self):
        """Test MAX_CONSECUTIVE_TEST_LOOPS constant."""
        assert MAX_CONSECUTIVE_TEST_LOOPS == 3

    def test_max_consecutive_done_signals(self):
        """Test MAX_CONSECUTIVE_DONE_SIGNALS constant."""
        assert MAX_CONSECUTIVE_DONE_SIGNALS == 2
