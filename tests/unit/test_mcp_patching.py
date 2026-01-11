
from unittest.mock import MagicMock, patch

from boring.mcp.tools.patching import boring_apply_patch, boring_extract_patches


class TestPatchingTools:
    """Tests for Patching MCP Tools."""

    def test_boring_apply_patch_success(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world\nline 2", encoding="utf-8")

        with patch("boring.mcp.tools.patching.get_project_root_or_error", return_value=(tmp_path, None)), \
             patch("boring.mcp.tools.patching.get_shadow_guard") as mock_guard:

            mock_guard_instance = mock_guard.return_value
            mock_guard_instance.check_operation.return_value = None

            result = boring_apply_patch(
                file_path="test.txt",
                search_text="hello world",
                replace_text="HELLO WORLD"
            )

            assert result["status"] == "SUCCESS"
            assert test_file.read_text() == "HELLO WORLD\nline 2"

    def test_boring_apply_patch_not_found(self, tmp_path):
        with patch("boring.mcp.tools.patching.get_project_root_or_error", return_value=(tmp_path, None)), \
             patch("boring.mcp.tools.patching.get_shadow_guard") as mock_guard:

            mock_guard_instance = mock_guard.return_value
            mock_guard_instance.check_operation.return_value = None

            result = boring_apply_patch(
                file_path="missing.txt",
                search_text="foo",
                replace_text="bar"
            )
            assert result["status"] == "ERROR"
            assert "not found" in result["error"].lower()

    def test_boring_apply_patch_ambiguous(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("same\nsame", encoding="utf-8")

        with patch("boring.mcp.tools.patching.get_project_root_or_error", return_value=(tmp_path, None)), \
             patch("boring.mcp.tools.patching.get_shadow_guard") as mock_guard:

            mock_guard_instance = mock_guard.return_value
            mock_guard_instance.check_operation.return_value = None

            result = boring_apply_patch(
                file_path="test.txt",
                search_text="same",
                replace_text="diff"
            )
            assert result["status"] == "ERROR"
            assert "ambiguous" in result["error"].lower()

    @patch("boring.mcp.tools.patching.extract_search_replace_blocks")
    @patch("boring.mcp.tools.patching.apply_search_replace_blocks")
    def test_boring_extract_patches_dry_run(self, mock_apply, mock_extract, tmp_path):
        mock_extract.return_value = [{"file_path": "test.py", "search": "old", "replace": "new"}]

        with patch("boring.mcp.tools.patching.get_project_root_or_error", return_value=(tmp_path, None)), \
             patch("boring.mcp.tools.patching.get_shadow_guard") as mock_guard:

            mock_guard_instance = mock_guard.return_value
            mock_guard_instance.check_operation.return_value = None

            result = boring_extract_patches("dummy output", dry_run=True)
            assert result["status"] == "SUCCESS"
            assert result["dry_run"] is True
            assert result["patches_found"] == 1
            mock_apply.assert_not_called()

    @patch("boring.mcp.tools.patching.extract_search_replace_blocks")
    @patch("boring.mcp.tools.patching.apply_search_replace_blocks")
    def test_boring_extract_patches_apply(self, mock_apply, mock_extract, tmp_path):
        mock_extract.return_value = [{"file_path": "test.py", "search": "old", "replace": "new"}]

        # Mock result from apply_search_replace_blocks
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.file_path = "test.py"
        mock_apply.return_value = [mock_result]

        with patch("boring.mcp.tools.patching.get_project_root_or_error", return_value=(tmp_path, None)), \
             patch("boring.mcp.tools.patching.get_shadow_guard") as mock_guard:

            mock_guard_instance = mock_guard.return_value
            mock_guard_instance.check_operation.return_value = None

            result = boring_extract_patches("dummy output", dry_run=False)
            assert result["status"] == "SUCCESS"
            assert result["applied"] == 1
            mock_apply.assert_called_once()
