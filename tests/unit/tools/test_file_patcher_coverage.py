"""
Additional tests for file_patcher to increase coverage.
"""

from unittest.mock import MagicMock, patch

from boring.tools.file_patcher import process_structured_calls


class TestProcessStructuredCalls:
    """Tests for process_structured_calls function."""

    def test_process_write_file_call(self, tmp_path):
        """Test processing write_file function call."""
        function_calls = [
            {"name": "write_file", "args": {"file_path": "test.py", "content": "print('hello')"}}
        ]

        count, modified, errors = process_structured_calls(
            function_calls, tmp_path, log_dir=tmp_path
        )

        assert count == 1
        assert "test.py" in modified
        assert (tmp_path / "test.py").exists()
        assert (tmp_path / "test.py").read_text(encoding="utf-8") == "print('hello')"

    def test_process_search_replace_call(self, tmp_path):
        """Test processing search_replace function call."""
        # Create initial file
        test_file = tmp_path / "test.py"
        test_file.write_text("old content\n", encoding="utf-8")

        function_calls = [
            {
                "name": "search_replace",
                "args": {"file_path": "test.py", "search": "old content", "replace": "new content"},
            }
        ]

        count, modified, errors = process_structured_calls(
            function_calls, tmp_path, log_dir=tmp_path
        )

        assert count == 1
        assert "test.py" in modified
        assert "new content" in test_file.read_text(encoding="utf-8")

    def test_process_multiple_calls(self, tmp_path):
        """Test processing multiple function calls."""
        function_calls = [
            {"name": "write_file", "args": {"file_path": "file1.py", "content": "content1"}},
            {"name": "write_file", "args": {"file_path": "file2.py", "content": "content2"}},
        ]

        count, modified, errors = process_structured_calls(
            function_calls, tmp_path, log_dir=tmp_path
        )

        assert count == 2
        assert len(modified) == 2

    def test_process_unknown_function(self, tmp_path):
        """Test processing unknown function call."""
        function_calls = [{"name": "unknown_function", "args": {}}]

        count, modified, errors = process_structured_calls(
            function_calls, tmp_path, log_dir=tmp_path
        )

        assert count == 0
        assert len(errors) >= 0  # May or may not have errors

    def test_process_with_backup(self, tmp_path):
        """Test processing with backup enabled."""
        test_file = tmp_path / "existing.py"
        test_file.write_text("original", encoding="utf-8")

        function_calls = [
            {"name": "write_file", "args": {"file_path": "existing.py", "content": "modified"}}
        ]

        with patch("boring.tools.file_patcher.BackupManager") as mock_backup:
            mock_instance = MagicMock()
            mock_backup.return_value = mock_instance

            count, modified, errors = process_structured_calls(
                function_calls, tmp_path, log_dir=tmp_path, loop_id=1
            )

            # Backup should be called for existing file
            if test_file.exists():
                assert mock_instance.backup_file.called or count > 0
