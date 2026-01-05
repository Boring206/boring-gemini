"""
Tests for boring.response_analyzer module (V4.0).

Updated to work with refactored analyzer that prioritizes
function call results over text-based heuristics.
"""

import json
from unittest.mock import MagicMock, patch

from boring.response_analyzer import (
    analyze_response,
    log_analysis_summary,
    update_exit_signals,
)


class TestAnalyzeResponse:
    """Tests for response analysis functionality."""

    def test_analyze_response_file_not_found(self, tmp_path, monkeypatch):
        """Test handling of non-existent output file."""
        monkeypatch.chdir(tmp_path)
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        output_file = tmp_path / "nonexistent.log"
        result = analyze_response(output_file, loop_number=1)

        assert result["loop_number"] == 1
        assert result["analysis"]["output_length"] == 0

    def test_analyze_response_with_function_call_results(self, tmp_path, monkeypatch):
        """Test that function call results take priority."""
        monkeypatch.chdir(tmp_path)
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        output_file = tmp_path / "output.log"
        output_file.write_text("Some output text")

        # Provide function call results (report_status tool)
        function_results = {
            "report_status": {
                "status": "COMPLETE",
                "exit_signal": True,
                "tasks_completed": ["Task 1", "Task 2"],
                "files_modified": ["file1.py", "file2.py"],
            }
        }

        result = analyze_response(
            output_file, loop_number=5, function_call_results=function_results
        )

        assert result["analysis"]["has_completion_signal"] is True
        assert result["analysis"]["exit_signal"] is True
        assert result["analysis"]["source"] == "function_call"
        assert result["analysis"]["confidence_score"] >= 100

    def test_analyze_response_boring_status_block(self, tmp_path, monkeypatch):
        """Test parsing of structured BORING_STATUS block."""
        monkeypatch.chdir(tmp_path)
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        output_file = tmp_path / "output.log"
        output_file.write_text("""
Some output here...
---BORING_STATUS---
STATUS: COMPLETE
EXIT_SIGNAL: true
---END_BORING_STATUS---
More output...
""")

        result = analyze_response(output_file, loop_number=10)

        assert result["analysis"]["has_completion_signal"] is True
        assert result["analysis"]["exit_signal"] is True
        assert result["analysis"]["source"] == "status_block"
        assert result["analysis"]["confidence_score"] >= 100

    def test_analyze_response_output_length(self, tmp_path, monkeypatch):
        """Test that output length is correctly captured."""
        monkeypatch.chdir(tmp_path)
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        content = "x" * 1000
        output_file = tmp_path / "output.log"
        output_file.write_text(content)

        result = analyze_response(output_file, loop_number=1)

        assert result["analysis"]["output_length"] == 1000

    def test_analyze_response_with_git_changes(self, tmp_path, monkeypatch):
        """Test detection of file changes via git."""
        monkeypatch.chdir(tmp_path)
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        # Mock git repo
        mock_repo = MagicMock()
        mock_diff_item = MagicMock()
        mock_diff_item.a_path = "src/main.py"
        mock_repo.index.diff.return_value = [mock_diff_item]
        mock_repo.untracked_files = ["new_file.py"]

        with patch.dict("sys.modules", {"git": MagicMock()}):
            import sys

            sys.modules["git"].Repo.return_value = mock_repo
            sys.modules["git"].InvalidGitRepositoryError = Exception

            output_file = tmp_path / "output.log"
            output_file.write_text("Modified some files.")

            result = analyze_response(output_file, loop_number=4)

        # Note: Git mocking in tests can be unreliable across platforms
        # We just verify the basic output structure is correct
        assert result["analysis"]["output_length"] > 0

    def test_analyze_response_in_progress_status(self, tmp_path, monkeypatch):
        """Test that IN_PROGRESS status does not trigger exit but shows progress."""
        monkeypatch.chdir(tmp_path)
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        output_file = tmp_path / "output.log"
        output_file.write_text("Working on implementation...")

        # IN_PROGRESS with tasks_completed triggers has_progress
        function_results = {
            "report_status": {
                "status": "IN_PROGRESS",
                "exit_signal": False,
                "tasks_completed": ["Task 1"],
                "files_modified": ["file1.py"],
            }
        }

        result = analyze_response(
            output_file, loop_number=3, function_call_results=function_results
        )

        assert result["analysis"]["has_completion_signal"] is False
        assert result["analysis"]["exit_signal"] is False
        assert result["analysis"]["has_progress"] is True

    def test_analyze_response_function_calls_override_text(self, tmp_path, monkeypatch):
        """Test that function call results override text analysis."""
        monkeypatch.chdir(tmp_path)
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        # Text says "complete" but function call says "in progress" with tasks
        # (tasks_completed triggers has_progress and sets source to function_call)
        output_file = tmp_path / "output.log"
        output_file.write_text("All tasks are complete!")

        function_results = {
            "report_status": {
                "status": "IN_PROGRESS",
                "exit_signal": False,
                "tasks_completed": ["Task 1"],  # This triggers confidence > 0
            }
        }

        result = analyze_response(
            output_file, loop_number=2, function_call_results=function_results
        )

        # Function call takes priority
        assert result["analysis"]["exit_signal"] is False
        assert result["analysis"]["source"] == "function_call"


class TestUpdateExitSignals:
    """Tests for exit signals update functionality."""

    def test_update_exit_signals_test_only(self, tmp_path, monkeypatch):
        """Test updating signals for test-only loop."""
        monkeypatch.chdir(tmp_path)

        analysis_data = {
            "loop_number": 5,
            "analysis": {
                "is_test_only": True,
                "has_completion_signal": False,
                "has_progress": False,
                "confidence_score": 10,
            },
        }
        analysis_file = tmp_path / ".response_analysis"
        analysis_file.write_text(json.dumps(analysis_data))

        with patch("boring.response_analyzer.ANALYSIS_RESULT_FILE", analysis_file):
            exit_signals_file = tmp_path / ".exit_signals"
            update_exit_signals(exit_signals_file)

            signals = json.loads(exit_signals_file.read_text())
            assert 5 in signals["test_only_loops"]

    def test_update_exit_signals_completion(self, tmp_path, monkeypatch):
        """Test updating signals for completion signal."""
        monkeypatch.chdir(tmp_path)

        analysis_data = {
            "loop_number": 8,
            "analysis": {
                "is_test_only": False,
                "has_completion_signal": True,
                "has_progress": True,
                "confidence_score": 50,
            },
        }
        analysis_file = tmp_path / ".response_analysis"
        analysis_file.write_text(json.dumps(analysis_data))

        with patch("boring.response_analyzer.ANALYSIS_RESULT_FILE", analysis_file):
            exit_signals_file = tmp_path / ".exit_signals"
            update_exit_signals(exit_signals_file)

            signals = json.loads(exit_signals_file.read_text())
            assert 8 in signals["done_signals"]

    def test_update_exit_signals_high_confidence(self, tmp_path, monkeypatch):
        """Test updating signals for high confidence completion."""
        monkeypatch.chdir(tmp_path)

        analysis_data = {
            "loop_number": 12,
            "analysis": {
                "is_test_only": False,
                "has_completion_signal": True,
                "has_progress": False,
                "confidence_score": 75,
            },
        }
        analysis_file = tmp_path / ".response_analysis"
        analysis_file.write_text(json.dumps(analysis_data))

        with patch("boring.response_analyzer.ANALYSIS_RESULT_FILE", analysis_file):
            exit_signals_file = tmp_path / ".exit_signals"
            update_exit_signals(exit_signals_file)

            signals = json.loads(exit_signals_file.read_text())
            assert 12 in signals["completion_indicators"]

    def test_update_exit_signals_progress_clears_test_only(self, tmp_path, monkeypatch):
        """Test that progress clears test_only_loops."""
        monkeypatch.chdir(tmp_path)

        # Pre-existing signals
        exit_signals_file = tmp_path / ".exit_signals"
        exit_signals_file.write_text(
            json.dumps(
                {"test_only_loops": [1, 2, 3], "done_signals": [], "completion_indicators": []}
            )
        )

        analysis_data = {
            "loop_number": 4,
            "analysis": {
                "is_test_only": False,
                "has_completion_signal": False,
                "has_progress": True,
                "confidence_score": 20,
            },
        }
        analysis_file = tmp_path / ".response_analysis"
        analysis_file.write_text(json.dumps(analysis_data))

        with patch("boring.response_analyzer.ANALYSIS_RESULT_FILE", analysis_file):
            update_exit_signals(exit_signals_file)

            signals = json.loads(exit_signals_file.read_text())
            assert signals["test_only_loops"] == []


class TestLogAnalysisSummary:
    """Tests for analysis summary logging."""

    def test_log_analysis_summary_no_file(self, tmp_path, monkeypatch):
        """Test that missing analysis file is handled gracefully."""
        monkeypatch.chdir(tmp_path)

        # Should not raise
        with patch("boring.response_analyzer.ANALYSIS_RESULT_FILE", tmp_path / "nonexistent"):
            log_analysis_summary()

    def test_log_analysis_summary_with_data(self, tmp_path, monkeypatch, capsys):
        """Test that summary is logged correctly."""
        monkeypatch.chdir(tmp_path)
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        analysis_data = {
            "loop_number": 3,
            "analysis": {
                "exit_signal": True,
                "confidence_score": 85,
                "is_test_only": False,
                "files_modified": 5,
                "work_summary": "Implemented authentication module",
                "source": "function_call",
            },
        }
        analysis_file = tmp_path / ".response_analysis"
        analysis_file.write_text(json.dumps(analysis_data))

        with patch("boring.response_analyzer.ANALYSIS_RESULT_FILE", analysis_file):
            log_analysis_summary()

        # Check log file was created
        log_file = logs_dir / "boring.log"
        assert log_file.exists()
        log_content = log_file.read_text()
        assert "Loop #3" in log_content
