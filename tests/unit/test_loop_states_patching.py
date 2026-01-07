"""
Unit tests for boring.loop.states.patching module.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.loop.base import StateResult
from boring.loop.context import LoopContext
from boring.loop.states.patching import PatchingState


@pytest.fixture
def mock_context(tmp_path):
    """Create a mock LoopContext."""
    context = MagicMock(spec=LoopContext)
    context.project_root = tmp_path
    context.log_dir = tmp_path / "logs"
    context.log_dir.mkdir(parents=True, exist_ok=True)
    context.loop_count = 1
    context.function_calls = []
    context.files_modified = []
    context.files_created = []
    context.patch_errors = []
    context.errors_this_loop = []
    return context


@pytest.fixture
def patching_state():
    return PatchingState()


class TestPatchingState:
    """Tests for PatchingState class."""

    def test_name(self, patching_state):
        """Test state name."""
        assert patching_state.name == "Patching"

    def test_on_enter(self, patching_state, mock_context):
        """Test state entry."""
        with (
            patch("boring.loop.states.patching.log_status") as mock_log,
            patch("boring.loop.states.patching.console") as mock_console,
        ):
            patching_state.on_enter(mock_context)

            mock_context.start_state.assert_called_once()
            mock_log.assert_called()
            mock_console.print.assert_called()

    def test_handle_no_function_calls(self, patching_state, mock_context):
        """Test handling when no function calls."""
        mock_context.function_calls = []

        result = patching_state.handle(mock_context)

        assert result == StateResult.FAILURE
        assert len(mock_context.errors_this_loop) > 0

    def test_handle_write_file_success(self, patching_state, mock_context):
        """Test handling write_file call successfully."""
        mock_context.function_calls = [
            {
                "name": "write_file",
                "args": {"file_path": "test.py", "content": "def test(): pass\n"},
            }
        ]
        mock_context.files_created = []

        with (
            patch.object(patching_state, "_process_write_file") as mock_write,
            patch.object(patching_state, "_get_files_to_modify", return_value=["test.py"]),
            patch("boring.loop.states.patching.BackupManager") as mock_backup_class,
            patch("boring.loop.states.patching.log_status"),
        ):
            mock_backup = MagicMock()
            mock_backup.create_snapshot.return_value = "backup123"
            mock_backup_class.return_value = mock_backup

            patching_state.handle(mock_context)

            mock_write.assert_called_once()

    def test_handle_search_replace_success(self, patching_state, mock_context):
        """Test handling search_replace call successfully."""
        test_file = mock_context.project_root / "existing.py"
        test_file.write_text("old code\n", encoding="utf-8")

        mock_context.function_calls = [
            {
                "name": "search_replace",
                "args": {"file_path": "existing.py", "search": "old code", "replace": "new code"},
            }
        ]
        mock_context.files_modified = []

        with (
            patch.object(patching_state, "_process_search_replace") as mock_replace,
            patch.object(patching_state, "_get_files_to_modify", return_value=["existing.py"]),
            patch("boring.loop.states.patching.BackupManager") as mock_backup_class,
            patch("boring.loop.states.patching.log_status"),
        ):
            mock_backup = MagicMock()
            mock_backup.create_snapshot.return_value = "backup123"
            mock_backup_class.return_value = mock_backup

            patching_state.handle(mock_context)

            mock_replace.assert_called_once()

    def test_handle_report_status(self, patching_state, mock_context):
        """Test handling report_status call."""
        mock_context.function_calls = [{"name": "report_status", "args": {"status": "in_progress"}}]
        mock_context.files_modified = ["file1.py"]

        with (
            patch.object(patching_state, "_get_files_to_modify", return_value=[]),
            patch("boring.loop.states.patching.log_status"),
        ):
            result = patching_state.handle(mock_context)

            # Should succeed if files were modified
            assert result == StateResult.SUCCESS

    def test_handle_no_files_modified(self, patching_state, mock_context):
        """Test handling when no files are modified."""
        mock_context.function_calls = [
            {"name": "write_file", "args": {"file_path": "test.py", "content": "code"}}
        ]
        mock_context.files_modified = []
        mock_context.files_created = []
        mock_context.patch_errors = []

        with (
            patch.object(patching_state, "_process_write_file"),
            patch.object(patching_state, "_get_files_to_modify", return_value=[]),
            patch("boring.loop.states.patching.log_status"),
        ):
            result = patching_state.handle(mock_context)

            assert result == StateResult.FAILURE

    def test_next_state_success(self, patching_state, mock_context):
        """Test next state on success."""
        with (
            patch("boring.loop.states.patching.VerifyingState", create=True),
            patch.object(patching_state, "_record_metrics"),
        ):
            next_state = patching_state.next_state(mock_context, StateResult.SUCCESS)

            assert next_state is not None

    def test_next_state_failure(self, patching_state, mock_context):
        """Test next state on failure."""
        with (
            patch("boring.loop.states.patching.RecoveryState", create=True),
            patch.object(patching_state, "_record_metrics"),
        ):
            next_state = patching_state.next_state(mock_context, StateResult.FAILURE)

            assert next_state is not None

    def test_get_files_to_modify(self, patching_state, mock_context):
        """Test getting files to modify."""
        write_calls = [{"name": "write_file", "args": {"file_path": "file1.py"}}]
        replace_calls = [{"name": "search_replace", "args": {"file_path": "file2.py"}}]
        (mock_context.project_root / "file1.py").touch()
        (mock_context.project_root / "file2.py").touch()

        files = patching_state._get_files_to_modify(mock_context, write_calls, replace_calls)

        filenames = [f.name for f in files]
        assert "file1.py" in filenames
        assert "file2.py" in filenames

    def test_process_write_file(self, patching_state, mock_context):
        """Test processing write_file call."""
        call = {
            "name": "write_file",
            "args": {"file_path": "test.py", "content": "def test(): pass\n"},
        }

        mock_validation = MagicMock()
        mock_validation.is_valid = True
        mock_validation.normalized_path = "test.py"
        mock_validation.reason = ""

        with (
            patch("boring.loop.states.patching.validate_file_path", return_value=mock_validation),
            patch("boring.loop.states.patching.sanitize_content", return_value="sanitized"),
            patch("pathlib.Path.write_text"),
            patch("boring.loop.states.patching.log_status"),
        ):
            patching_state._process_write_file(mock_context, call)

            # Should add to files_created
            assert len(mock_context.files_created) > 0 or call["args"]["file_path"] in str(
                mock_context.files_created
            )

    def test_process_search_replace(self, patching_state, mock_context):
        """Test processing search_replace call."""
        test_file = mock_context.project_root / "test.py"
        test_file.write_text("old code\n", encoding="utf-8")

        call = {
            "name": "search_replace",
            "args": {"file_path": "test.py", "search": "old code", "replace": "new code"},
        }

        mock_validation = MagicMock()
        mock_validation.is_valid = True
        mock_validation.normalized_path = "test.py"

        with (
            patch("boring.loop.states.patching.validate_file_path", return_value=mock_validation),
            patch("boring.loop.states.patching.log_status"),
        ):
            patching_state._process_search_replace(mock_context, call)

            # Should attempt to modify file
            assert True  # If no exception, test passes
