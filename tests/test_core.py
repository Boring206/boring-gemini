"""
Tests for boring core functionality.

Uses pytest with mocking for file I/O operations.
"""

import json

# Import functions to test - using direct module imports (non-deprecated)
from boring.limiter import (
    can_make_call,
    get_calls_made,
    increment_call_counter,
    init_call_tracking,
    should_exit_gracefully,
)


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_can_make_call_within_limit(self, tmp_path):
        """Test that calls are allowed when under the limit."""
        call_count_file = tmp_path / ".call_count"
        call_count_file.write_text("5")

        assert can_make_call(call_count_file, max_calls_per_hour=100) is True

    def test_can_make_call_at_limit(self, tmp_path):
        """Test that calls are blocked when at the limit."""
        call_count_file = tmp_path / ".call_count"
        call_count_file.write_text("100")

        assert can_make_call(call_count_file, max_calls_per_hour=100) is False

    def test_can_make_call_over_limit(self, tmp_path):
        """Test that calls are blocked when over the limit."""
        call_count_file = tmp_path / ".call_count"
        call_count_file.write_text("150")

        assert can_make_call(call_count_file, max_calls_per_hour=100) is False

    def test_can_make_call_no_file(self, tmp_path):
        """Test that calls are allowed when no count file exists (assumes 0)."""
        call_count_file = tmp_path / ".call_count"
        # File doesn't exist

        assert can_make_call(call_count_file, max_calls_per_hour=100) is True

    def test_get_calls_made_existing_file(self, tmp_path):
        """Test reading call count from existing file."""
        call_count_file = tmp_path / ".call_count"
        call_count_file.write_text("42")

        assert get_calls_made(call_count_file) == 42

    def test_get_calls_made_no_file(self, tmp_path):
        """Test reading call count when file doesn't exist."""
        call_count_file = tmp_path / ".call_count"

        assert get_calls_made(call_count_file) == 0

    def test_increment_call_counter(self, tmp_path):
        """Test incrementing the call counter."""
        call_count_file = tmp_path / ".call_count"
        call_count_file.write_text("10")

        new_count = increment_call_counter(call_count_file)

        assert new_count == 11
        assert call_count_file.read_text() == "11"


class TestExitDetection:
    """Tests for exit detection functionality."""

    def test_should_exit_gracefully_no_signals(self, tmp_path):
        """Test that no exit occurs when no signals are present."""
        exit_signals_file = tmp_path / ".exit_signals"
        exit_signals_file.write_text(
            json.dumps({"test_only_loops": [], "done_signals": [], "completion_indicators": []})
        )

        result = should_exit_gracefully(exit_signals_file)

        assert result is None

    def test_should_exit_gracefully_test_saturation(self, tmp_path):
        """Test exit on test saturation (too many test-only loops)."""
        exit_signals_file = tmp_path / ".exit_signals"
        exit_signals_file.write_text(
            json.dumps(
                {
                    "test_only_loops": [1, 2, 3],  # MAX_CONSECUTIVE_TEST_LOOPS = 3
                    "done_signals": [],
                    "completion_indicators": [],
                }
            )
        )

        result = should_exit_gracefully(exit_signals_file)

        assert result == "test_saturation"

    def test_should_exit_gracefully_done_signals(self, tmp_path):
        """Test exit on multiple done signals."""
        exit_signals_file = tmp_path / ".exit_signals"
        exit_signals_file.write_text(
            json.dumps(
                {
                    "test_only_loops": [],
                    "done_signals": [1, 2],  # MAX_CONSECUTIVE_DONE_SIGNALS = 2
                    "completion_indicators": [],
                }
            )
        )

        result = should_exit_gracefully(exit_signals_file)

        assert result == "completion_signals"

    def test_should_exit_gracefully_completion_indicators(self, tmp_path):
        """Test exit on strong completion indicators."""
        exit_signals_file = tmp_path / ".exit_signals"
        exit_signals_file.write_text(
            json.dumps(
                {
                    "test_only_loops": [],
                    "done_signals": [],
                    "completion_indicators": ["indicator1", "indicator2"],
                }
            )
        )

        result = should_exit_gracefully(exit_signals_file)

        assert result == "project_complete"

    def test_should_exit_gracefully_no_file(self, tmp_path):
        """Test that no exit occurs when signals file doesn't exist."""
        exit_signals_file = tmp_path / ".exit_signals"
        # File doesn't exist

        result = should_exit_gracefully(exit_signals_file)

        assert result is None

    def test_should_exit_gracefully_fix_plan_complete(self, tmp_path, monkeypatch):
        """Test exit when all fix_plan.md items are completed."""
        exit_signals_file = tmp_path / ".exit_signals"
        exit_signals_file.write_text(
            json.dumps({"test_only_loops": [], "done_signals": [], "completion_indicators": []})
        )

        # Create a completed fix_plan.md
        fix_plan_file = tmp_path / "@fix_plan.md"
        fix_plan_file.write_text("""
# Fix Plan
- [x] Task 1
- [x] Task 2
- [x] Task 3
""")

        # Change working directory temporarily
        monkeypatch.chdir(tmp_path)

        result = should_exit_gracefully(exit_signals_file)

        assert result == "plan_complete"

    def test_should_exit_gracefully_fix_plan_incomplete(self, tmp_path, monkeypatch):
        """Test no exit when fix_plan.md has incomplete items."""
        exit_signals_file = tmp_path / ".exit_signals"
        exit_signals_file.write_text(
            json.dumps({"test_only_loops": [], "done_signals": [], "completion_indicators": []})
        )

        # Create an incomplete fix_plan.md
        fix_plan_file = tmp_path / "@fix_plan.md"
        fix_plan_file.write_text("""
# Fix Plan
- [x] Task 1
- [ ] Task 2 (incomplete)
- [x] Task 3
""")

        # Change working directory temporarily
        monkeypatch.chdir(tmp_path)

        result = should_exit_gracefully(exit_signals_file)

        assert result is None


class TestInitCallTracking:
    """Tests for call tracking initialization."""

    def test_init_creates_files(self, tmp_path, monkeypatch):
        """Test that init creates necessary files."""
        call_count_file = tmp_path / ".call_count"
        timestamp_file = tmp_path / ".last_reset"
        exit_signals_file = tmp_path / ".exit_signals"

        # Mock logs directory
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        monkeypatch.chdir(tmp_path)

        init_call_tracking(call_count_file, timestamp_file, exit_signals_file)

        assert exit_signals_file.exists()
        signals = json.loads(exit_signals_file.read_text())
        assert "test_only_loops" in signals
        assert "done_signals" in signals
        assert "completion_indicators" in signals
