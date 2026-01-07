# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.response_analyzer module.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boring.response_analyzer import (
    ANALYSIS_RESULT_FILE,
    EXIT_SIGNALS_FILE,
    analyze_response,
    log_analysis_summary,
    update_exit_signals,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_output_file(tmp_path):
    """Create a temporary output file."""
    output_file = tmp_path / "output.txt"
    return output_file


@pytest.fixture
def cleanup_analysis_files():
    """Cleanup analysis files after test."""
    yield
    if ANALYSIS_RESULT_FILE.exists():
        ANALYSIS_RESULT_FILE.unlink()
    if EXIT_SIGNALS_FILE.exists():
        EXIT_SIGNALS_FILE.unlink()


# =============================================================================
# ANALYZE RESPONSE TESTS
# =============================================================================


class TestAnalyzeResponse:
    """Tests for analyze_response function."""

    def test_analyze_response_with_function_call_exit_signal(
        self, temp_output_file, cleanup_analysis_files
    ):
        """Test analyze_response with function call exit signal."""
        function_call_results = {
            "report_status": {
                "exit_signal": True,
                "status": "COMPLETE",
                "tasks_completed": ["task1"],
                "files_modified": ["file1.py"],
            }
        }

        result = analyze_response(
            temp_output_file, loop_number=1, function_call_results=function_call_results
        )

        assert result["analysis"]["has_completion_signal"] is True
        assert result["analysis"]["exit_signal"] is True
        # Base 100 + 20 (completion) + 20 (files/tasks progress) = 140
        assert result["analysis"]["confidence_score"] == 140
        assert result["analysis"]["source"] == "function_call"

    def test_analyze_response_with_function_call_status_complete(
        self, temp_output_file, cleanup_analysis_files
    ):
        """Test analyze_response with function call status COMPLETE."""
        function_call_results = {
            "report_status": {
                "status": "COMPLETE",
            }
        }

        result = analyze_response(
            temp_output_file, loop_number=1, function_call_results=function_call_results
        )

        assert result["analysis"]["has_completion_signal"] is True
        assert result["analysis"]["exit_signal"] is True

    def test_analyze_response_with_function_call_tasks(
        self, temp_output_file, cleanup_analysis_files
    ):
        """Test analyze_response with function call tasks."""
        function_call_results = {
            "report_status": {
                "tasks_completed": ["task1", "task2"],
            }
        }

        result = analyze_response(
            temp_output_file, loop_number=1, function_call_results=function_call_results
        )

        assert result["analysis"]["has_progress"] is True
        assert "task1" in result["analysis"]["work_summary"]

    def test_analyze_response_with_status_block(self, temp_output_file, cleanup_analysis_files):
        """Test analyze_response with status block."""
        temp_output_file.write_text(
            "---BORING_STATUS---\nSTATUS: COMPLETE\n---END_BORING_STATUS---"
        )

        result = analyze_response(temp_output_file, loop_number=1)

        assert result["analysis"]["has_completion_signal"] is True
        assert result["analysis"]["exit_signal"] is True
        assert result["analysis"]["source"] == "status_block"

    def test_analyze_response_with_status_block_exit_signal(
        self, temp_output_file, cleanup_analysis_files
    ):
        """Test analyze_response with status block exit signal."""
        temp_output_file.write_text(
            "---BORING_STATUS---\nEXIT_SIGNAL: true\n---END_BORING_STATUS---"
        )

        result = analyze_response(temp_output_file, loop_number=1)

        assert result["analysis"]["exit_signal"] is True

    def test_analyze_response_with_git_diff(self, temp_output_file, cleanup_analysis_files):
        """Test analyze_response with git diff."""
        temp_output_file.write_text("Some output")

        # Patch git.Repo via sys.modules to handle local import
        mock_repo = MagicMock()
        mock_repo.index.diff.return_value = [MagicMock(a_path="file1.py")]
        mock_repo.untracked_files = ["file2.py"]

        mock_git = MagicMock()
        mock_git.Repo.return_value = mock_repo
        # We need InvalidGitRepositoryError to exist on the mock
        mock_git.InvalidGitRepositoryError = Exception

        with patch.dict("sys.modules", {"git": mock_git}):
            with patch("boring.response_analyzer.Path.cwd", return_value=Path(".")):
                result = analyze_response(temp_output_file, loop_number=1)

                assert result["analysis"]["has_progress"] is True
                assert result["analysis"]["files_modified"] == 2

    def test_analyze_response_minimal_output(self, temp_output_file, cleanup_analysis_files):
        """Test analyze_response with minimal output."""
        temp_output_file.write_text("")  # Empty file content

        # Ensure git doesn't interfere by finding changes
        mock_repo = MagicMock()
        mock_repo.index.diff.return_value = []
        mock_repo.untracked_files = []

        mock_git = MagicMock()
        mock_git.Repo.return_value = mock_repo
        mock_git.InvalidGitRepositoryError = Exception

        with patch.dict("sys.modules", {"git": mock_git}):
            result = analyze_response(temp_output_file, loop_number=1)

            assert result["analysis"]["source"] == "fallback"
            assert "Minimal output" in result["analysis"]["work_summary"]

    def test_analyze_response_nonexistent_file(self, tmp_path, cleanup_analysis_files):
        """Test analyze_response with nonexistent output file."""
        nonexistent = tmp_path / "nonexistent.txt"

        with patch("boring.response_analyzer.log_status"):
            result = analyze_response(nonexistent, loop_number=1)

            assert result["analysis"]["output_length"] == 0

    def test_analyze_response_empty_function_call_results(
        self, temp_output_file, cleanup_analysis_files
    ):
        """Test analyze_response with empty function call results."""
        result = analyze_response(temp_output_file, loop_number=1, function_call_results={})

        assert isinstance(result, dict)
        assert result["loop_number"] == 1


# =============================================================================
# UPDATE EXIT SIGNALS TESTS
# =============================================================================


class TestUpdateExitSignals:
    """Tests for update_exit_signals function."""

    def test_update_exit_signals_with_completion(self, tmp_path, cleanup_analysis_files):
        """Test update_exit_signals with completion signal."""
        exit_signals_file = tmp_path / ".exit_signals"

        # Create analysis result file
        analysis_data = {
            "loop_number": 1,
            "analysis": {
                "has_completion_signal": True,
                "has_progress": True,
                "confidence_score": 80,
            },
        }
        ANALYSIS_RESULT_FILE.write_text(json.dumps(analysis_data))

        update_exit_signals(exit_signals_file)

        assert exit_signals_file.exists()
        signals_data = json.loads(exit_signals_file.read_text())
        assert 1 in signals_data["done_signals"]
        assert 1 in signals_data["completion_indicators"]

    def test_update_exit_signals_with_test_only(self, tmp_path, cleanup_analysis_files):
        """Test update_exit_signals with test_only flag."""
        exit_signals_file = tmp_path / ".exit_signals"

        analysis_data = {
            "loop_number": 2,
            "analysis": {
                "is_test_only": True,
                "has_progress": False,
            },
        }
        ANALYSIS_RESULT_FILE.write_text(json.dumps(analysis_data))

        update_exit_signals(exit_signals_file)

        signals_data = json.loads(exit_signals_file.read_text())
        assert 2 in signals_data["test_only_loops"]

    def test_update_exit_signals_rolling_window(self, tmp_path, cleanup_analysis_files):
        """Test update_exit_signals keeps only last 5 signals."""
        exit_signals_file = tmp_path / ".exit_signals"

        # Add 7 completion signals
        for loop_num in range(1, 8):
            analysis_data = {
                "loop_number": loop_num,
                "analysis": {
                    "has_completion_signal": True,
                    "confidence_score": 80,
                },
            }
            ANALYSIS_RESULT_FILE.write_text(json.dumps(analysis_data))
            update_exit_signals(exit_signals_file)

        signals_data = json.loads(exit_signals_file.read_text())
        assert len(signals_data["done_signals"]) <= 5

    def test_update_exit_signals_no_analysis_file(self, tmp_path, cleanup_analysis_files):
        """Test update_exit_signals when analysis file doesn't exist."""
        exit_signals_file = tmp_path / ".exit_signals"

        # Ensure analysis file doesn't exist
        if ANALYSIS_RESULT_FILE.exists():
            ANALYSIS_RESULT_FILE.unlink()

        update_exit_signals(exit_signals_file)

        # Should not raise exception
        assert True

    def test_update_exit_signals_existing_signals_file(self, tmp_path, cleanup_analysis_files):
        """Test update_exit_signals with existing signals file."""
        exit_signals_file = tmp_path / ".exit_signals"
        exit_signals_file.write_text(
            json.dumps({"done_signals": [1], "test_only_loops": [], "completion_indicators": []})
        )

        analysis_data = {
            "loop_number": 2,
            "analysis": {
                "has_completion_signal": True,
                "confidence_score": 80,
            },
        }
        ANALYSIS_RESULT_FILE.write_text(json.dumps(analysis_data))

        update_exit_signals(exit_signals_file)

        signals_data = json.loads(exit_signals_file.read_text())
        assert 1 in signals_data["done_signals"]
        assert 2 in signals_data["done_signals"]


# =============================================================================
# LOG ANALYSIS SUMMARY TESTS
# =============================================================================


class TestLogAnalysisSummary:
    """Tests for log_analysis_summary function."""

    def test_log_analysis_summary(self, cleanup_analysis_files):
        """Test log_analysis_summary."""
        analysis_data = {
            "loop_number": 1,
            "analysis": {
                "exit_signal": True,
                "confidence_score": 90,
                "source": "function_call",
                "files_modified": 3,
                "work_summary": "Completed tasks",
            },
        }
        ANALYSIS_RESULT_FILE.write_text(json.dumps(analysis_data))

        with patch("boring.response_analyzer.log_status") as mock_log:
            log_analysis_summary()

            assert mock_log.called

    def test_log_analysis_summary_no_file(self, cleanup_analysis_files):
        """Test log_analysis_summary when file doesn't exist."""
        if ANALYSIS_RESULT_FILE.exists():
            ANALYSIS_RESULT_FILE.unlink()

        # Should not raise exception
        log_analysis_summary()
        assert True
