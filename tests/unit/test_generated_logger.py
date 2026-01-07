# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.logger module.
"""

import json
from unittest.mock import patch

from boring.logger import get_logger, log_status, update_status

# =============================================================================
# GET LOGGER TESTS
# =============================================================================


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_default(self):
        """Test get_logger with default name."""
        logger = get_logger()
        assert logger is not None

    def test_get_logger_custom_name(self):
        """Test get_logger with custom name."""
        logger = get_logger("custom_module")
        assert logger is not None


# =============================================================================
# LOG STATUS TESTS
# =============================================================================


class TestLogStatus:
    """Tests for log_status function."""

    def test_log_status_info(self, tmp_path):
        """Test log_status with INFO level."""
        log_dir = tmp_path / "logs"
        log_status(log_dir, "INFO", "Test message")

        log_file = log_dir / "boring.log"
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_log_status_warn(self, tmp_path):
        """Test log_status with WARN level."""
        log_dir = tmp_path / "logs"
        log_status(log_dir, "WARN", "Warning message")

        log_file = log_dir / "boring.log"
        assert log_file.exists()

    def test_log_status_error(self, tmp_path):
        """Test log_status with ERROR level."""
        log_dir = tmp_path / "logs"
        log_status(log_dir, "ERROR", "Error message")

        log_file = log_dir / "boring.log"
        assert log_file.exists()

    def test_log_status_success(self, tmp_path):
        """Test log_status with SUCCESS level."""
        log_dir = tmp_path / "logs"
        log_status(log_dir, "SUCCESS", "Success message")

        log_file = log_dir / "boring.log"
        assert log_file.exists()

    def test_log_status_with_kwargs(self, tmp_path):
        """Test log_status with additional kwargs."""
        log_dir = tmp_path / "logs"
        log_status(log_dir, "INFO", "Test message", key1="value1", key2=42)

        log_file = log_dir / "boring.log"
        content = log_file.read_text()
        data = json.loads(content.strip())
        assert data["key1"] == "value1"
        assert data["key2"] == 42

    def test_log_status_string_path(self, tmp_path):
        """Test log_status with string path."""
        log_dir = str(tmp_path / "logs")
        log_status(log_dir, "INFO", "Test message")

        log_file = tmp_path / "logs" / "boring.log"
        assert log_file.exists()

    def test_log_status_no_log_dir(self):
        """Test log_status without log directory."""
        # Should not raise exception
        log_status(None, "INFO", "Test message")

    def test_log_status_creates_dir(self, tmp_path):
        """Test log_status creates directory if needed."""
        log_dir = tmp_path / "new_logs" / "subdir"
        log_status(log_dir, "INFO", "Test message")

        assert log_dir.exists()
        log_file = log_dir / "boring.log"
        assert log_file.exists()


# =============================================================================
# UPDATE STATUS TESTS
# =============================================================================


class TestUpdateStatus:
    """Tests for update_status function."""

    def test_update_status(self, tmp_path):
        """Test update_status creates status file."""
        status_file = tmp_path / "status.json"

        update_status(
            status_file=status_file,
            loop_count=5,
            max_calls=100,
            last_action="test action",
            status="running",
            exit_reason="",
            calls_made=10,
        )

        assert status_file.exists()
        data = json.loads(status_file.read_text())
        assert data["loop_count"] == 5
        assert data["status"] == "running"
        assert data["calls_made_this_hour"] == 10

    def test_update_status_with_exit_reason(self, tmp_path):
        """Test update_status with exit reason."""
        status_file = tmp_path / "status.json"

        update_status(
            status_file=status_file,
            loop_count=10,
            max_calls=100,
            last_action="completed",
            status="idle",
            exit_reason="task_complete",
        )

        data = json.loads(status_file.read_text())
        assert data["exit_reason"] == "task_complete"

    def test_update_status_creates_parent_dir(self, tmp_path):
        """Test update_status creates parent directory."""
        status_file = tmp_path / "nested" / "dir" / "status.json"

        update_status(
            status_file=status_file,
            loop_count=1,
            max_calls=100,
            last_action="test",
            status="idle",
        )

        assert status_file.exists()

    def test_update_status_without_calls_made(self, tmp_path):
        """Test update_status without explicit calls_made."""
        status_file = tmp_path / "status.json"

        with patch("boring.limiter.get_calls_made", return_value=5):
            update_status(
                status_file=status_file,
                loop_count=1,
                max_calls=100,
                last_action="test",
                status="idle",
            )

            data = json.loads(status_file.read_text())
            assert data["calls_made_this_hour"] == 5
