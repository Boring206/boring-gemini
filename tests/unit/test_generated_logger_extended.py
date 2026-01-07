# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Extended unit tests for boring.logger module.
"""

from unittest.mock import patch

from boring.logger import get_log_tail

# =============================================================================
# GET LOG TAIL TESTS
# =============================================================================


class TestGetLogTail:
    """Tests for get_log_tail function."""

    def test_get_log_tail_existing(self, tmp_path):
        """Test get_log_tail with existing log file."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        log_file = log_dir / "boring.log"

        # Write multiple lines
        with open(log_file, "w", encoding="utf-8") as f:
            for i in range(20):
                f.write(f"Log line {i}\n")

        lines = get_log_tail(log_dir, lines=10)
        assert len(lines) == 10
        assert "Log line 19" in lines[-1]

    def test_get_log_tail_nonexistent(self, tmp_path):
        """Test get_log_tail with nonexistent log file."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        lines = get_log_tail(log_dir)
        assert lines == []

    def test_get_log_tail_custom_lines(self, tmp_path):
        """Test get_log_tail with custom line count."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        log_file = log_dir / "boring.log"

        with open(log_file, "w", encoding="utf-8") as f:
            for i in range(5):
                f.write(f"Line {i}\n")

        lines = get_log_tail(log_dir, lines=3)
        assert len(lines) == 3

    def test_get_log_tail_read_error(self, tmp_path):
        """Test get_log_tail with read error."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        log_file = log_dir / "boring.log"
        log_file.write_text("test")

        with patch("builtins.open", side_effect=OSError("Read error")):
            lines = get_log_tail(log_dir)
            assert lines == []
