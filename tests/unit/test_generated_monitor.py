# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.monitor module.
"""

import json
from unittest.mock import patch

import pytest

from boring.monitor import (
    get_circuit_panel,
    get_logs_panel,
    get_progress_panel,
    get_status_panel,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_status_file(tmp_path):
    """Create a temporary status.json file."""
    status_file = tmp_path / "status.json"
    return status_file


@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_file = log_dir / "boring.log"
    return log_file


@pytest.fixture
def temp_progress_file(tmp_path):
    """Create a temporary progress file."""
    progress_file = tmp_path / ".progress.json"
    return progress_file


# =============================================================================
# STATUS PANEL TESTS
# =============================================================================


class TestGetStatusPanel:
    """Tests for get_status_panel function."""

    def test_get_status_panel_file_not_found(self, tmp_path):
        """Test get_status_panel when status file doesn't exist."""
        with patch("boring.monitor.STATUS_FILE", tmp_path / "nonexistent.json"):
            panel = get_status_panel()
            assert panel is not None

    def test_get_status_panel_success(self, temp_status_file):
        """Test get_status_panel with valid status file."""
        status_data = {
            "loop_count": 5,
            "status": "running",
            "calls_made_this_hour": 10,
            "max_calls_per_hour": 100,
            "exit_reason": "",
        }
        temp_status_file.write_text(json.dumps(status_data))

        with patch("boring.monitor.STATUS_FILE", temp_status_file):
            panel = get_status_panel()
            assert panel is not None

    def test_get_status_panel_error_status(self, temp_status_file):
        """Test get_status_panel with error status."""
        status_data = {
            "loop_count": 5,
            "status": "error",
            "calls_made_this_hour": 10,
            "max_calls_per_hour": 100,
        }
        temp_status_file.write_text(json.dumps(status_data))

        with patch("boring.monitor.STATUS_FILE", temp_status_file):
            panel = get_status_panel()
            assert panel is not None

    def test_get_status_panel_corrupted_json(self, temp_status_file):
        """Test get_status_panel with corrupted JSON."""
        temp_status_file.write_text("invalid json")

        with patch("boring.monitor.STATUS_FILE", temp_status_file):
            panel = get_status_panel()
            assert panel is not None

    def test_get_status_panel_with_exit_reason(self, temp_status_file):
        """Test get_status_panel with exit reason."""
        status_data = {
            "loop_count": 10,
            "status": "idle",
            "calls_made_this_hour": 0,
            "max_calls_per_hour": 100,
            "exit_reason": "task_complete",
        }
        temp_status_file.write_text(json.dumps(status_data))

        with patch("boring.monitor.STATUS_FILE", temp_status_file):
            panel = get_status_panel()
            assert panel is not None


# =============================================================================
# PROGRESS PANEL TESTS
# =============================================================================


class TestGetProgressPanel:
    """Tests for get_progress_panel function."""

    def test_get_progress_panel_file_not_found(self, tmp_path):
        """Test get_progress_panel when progress file doesn't exist."""
        with patch("boring.monitor.PROGRESS_FILE", tmp_path / "nonexistent.json"):
            panel = get_progress_panel()
            assert panel is None

    def test_get_progress_panel_executing(self, temp_progress_file):
        """Test get_progress_panel with executing status."""
        progress_data = {
            "status": "executing",
            "indicator": "●",
            "elapsed_seconds": 10,
            "last_output": "Processing...",
        }
        temp_progress_file.write_text(json.dumps(progress_data))

        with patch("boring.monitor.PROGRESS_FILE", temp_progress_file):
            panel = get_progress_panel()
            assert panel is not None

    def test_get_progress_panel_idle(self, temp_progress_file):
        """Test get_progress_panel with idle status."""
        progress_data = {"status": "idle"}
        temp_progress_file.write_text(json.dumps(progress_data))

        with patch("boring.monitor.PROGRESS_FILE", temp_progress_file):
            panel = get_progress_panel()
            assert panel is None

    def test_get_progress_panel_corrupted_json(self, temp_progress_file):
        """Test get_progress_panel with corrupted JSON."""
        temp_progress_file.write_text("invalid json")

        with patch("boring.monitor.PROGRESS_FILE", temp_progress_file):
            panel = get_progress_panel()
            assert panel is None


# =============================================================================
# CIRCUIT PANEL TESTS
# =============================================================================


class TestGetCircuitPanel:
    """Tests for get_circuit_panel function."""

    def test_get_circuit_panel(self):
        """Test get_circuit_panel function."""
        with patch("boring.monitor.Path") as mock_path:
            mock_cb_file = mock_path.return_value
            mock_cb_file.exists.return_value = True
            mock_cb_file.read_text.return_value = json.dumps(
                {
                    "state": "CLOSED",
                    "failure_count": 0,
                }
            )

            panel = get_circuit_panel()
            assert panel is not None

    def test_get_circuit_panel_file_not_found(self):
        """Test get_circuit_panel when circuit breaker file doesn't exist."""
        with patch("boring.monitor.Path") as mock_path:
            mock_cb_file = mock_path.return_value
            mock_cb_file.exists.return_value = False

            panel = get_circuit_panel()
            assert panel is not None


# =============================================================================
# LOGS PANEL TESTS
# =============================================================================


class TestGetLogsPanel:
    """Tests for get_logs_panel function."""

    def test_get_logs_panel_file_not_found(self, tmp_path):
        """Test get_logs_panel when log file doesn't exist."""
        log_file = tmp_path / "logs" / "boring.log"

        with patch("boring.monitor.LOG_FILE", log_file):
            panel = get_logs_panel()
            assert panel is not None

    def test_get_logs_panel_with_logs(self, temp_log_file):
        """Test get_logs_panel with log entries."""
        temp_log_file.write_text(
            '{"timestamp": "2024-01-01 12:00:00", "level": "INFO", "message": "Test log"}\n'
            '{"timestamp": "2024-01-01 12:00:01", "level": "ERROR", "message": "Error log"}\n'
        )

        with patch("boring.monitor.LOG_FILE", temp_log_file):
            panel = get_logs_panel()
            assert panel is not None

    def test_get_logs_panel_empty_file(self, temp_log_file):
        """Test get_logs_panel with empty log file."""
        temp_log_file.write_text("")

        with patch("boring.monitor.LOG_FILE", temp_log_file):
            panel = get_logs_panel()
            assert panel is not None

    def test_get_logs_panel_invalid_json(self, temp_log_file):
        """Test get_logs_panel with invalid JSON in log file."""
        temp_log_file.write_text("invalid json lines\n")

        with patch("boring.monitor.LOG_FILE", temp_log_file):
            panel = get_logs_panel()
            assert panel is not None
