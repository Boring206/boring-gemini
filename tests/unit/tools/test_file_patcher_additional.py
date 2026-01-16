"""
Additional tests for file_patcher to increase coverage.
"""

from unittest.mock import MagicMock, patch

from boring.tools.file_patcher import _search_replace, _write_file


class TestWriteFile:
    """Tests for _write_file function."""

    def test_write_new_file(self, tmp_path):
        """Test writing a new file."""
        result = _write_file("test.py", "content", tmp_path, tmp_path)
        assert result[0] is True  # success
        assert result[1] == "created"
        assert (tmp_path / "test.py").exists()

    def test_write_existing_file(self, tmp_path):
        """Test writing to existing file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("old", encoding="utf-8")

        result = _write_file("test.py", "new", tmp_path, tmp_path)
        assert result[0] is True
        assert result[1] == "modified"
        assert test_file.read_text(encoding="utf-8") == "new"

    def test_write_blocked_path(self, tmp_path):
        """Test writing to blocked path."""
        result = _write_file("../blocked.py", "content", tmp_path, tmp_path)
        assert result[0] is False  # Should be blocked

    def test_write_with_shadow_mode(self, tmp_path):
        """Test writing with shadow mode enabled."""
        with patch("boring.mcp.tools.shadow.get_shadow_guard") as mock_guard:
            mock_guard_instance = MagicMock()
            mock_pending = MagicMock()
            mock_pending.operation_id = "test-op"
            mock_guard_instance.check_operation.return_value = mock_pending
            mock_guard_instance.request_approval.return_value = False
            mock_guard.return_value = mock_guard_instance

            result = _write_file("test.py", "content", tmp_path, tmp_path)
            # Should be blocked
            assert result[0] is False


class TestSearchReplace:
    """Tests for _search_replace function."""

    def test_search_replace_success(self, tmp_path):
        """Test successful search/replace."""
        test_file = tmp_path / "test.py"
        test_file.write_text("old content\n", encoding="utf-8")

        result = _search_replace("test.py", "old content", "new content", tmp_path, tmp_path)
        assert result[0] is True  # success
        assert "new content" in test_file.read_text(encoding="utf-8")

    def test_search_replace_no_match(self, tmp_path):
        """Test search/replace when pattern doesn't match."""
        test_file = tmp_path / "test.py"
        test_file.write_text("different content\n", encoding="utf-8")

        result = _search_replace("test.py", "old", "new", tmp_path, tmp_path)
        assert result[0] is False  # Should fail

    def test_search_replace_file_not_found(self, tmp_path):
        """Test search/replace on non-existent file."""
        result = _search_replace("nonexistent.py", "old", "new", tmp_path, tmp_path)
        assert result[0] is False
