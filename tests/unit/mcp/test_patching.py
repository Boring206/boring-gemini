import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from boring.mcp.tools.patching import boring_apply_patch, boring_extract_patches

class TestPatchingTools:

    @patch("boring.mcp.tools.patching.get_project_root_or_error")
    @patch("boring.mcp.tools.patching.configure_runtime_for_project")
    def test_boring_apply_patch_success(self, mock_config, mock_get_root):
        """Test successful patch application."""
        mock_root = MagicMock()
        mock_get_root.return_value = (mock_root, None)
        
        # Setup file mock
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = "def old():\n    pass"
        mock_root.__truediv__.return_value = mock_file
        
        res = boring_apply_patch(
            file_path="test.py",
            search_text="def old():",
            replace_text="def new():"
        )
        
        assert res["status"] == "SUCCESS"
        mock_file.write_text.assert_called_with("def new():\n    pass", encoding="utf-8")

    @patch("boring.mcp.tools.patching.get_project_root_or_error")
    @patch("boring.mcp.tools.patching.configure_runtime_for_project")
    def test_boring_apply_patch_not_found(self, mock_config, mock_get_root):
        """Test patch on non-existent file."""
        mock_root = MagicMock()
        mock_get_root.return_value = (mock_root, None)
        mock_root.__truediv__.return_value.exists.return_value = False
        
        res = boring_apply_patch("missing.py", "foo", "bar")
        assert res["status"] == "ERROR"
        assert "File not found" in res["error"]

    @patch("boring.mcp.tools.patching.get_project_root_or_error")
    @patch("boring.mcp.tools.patching.configure_runtime_for_project")
    @patch("boring.diff_patcher.apply_search_replace_blocks")
    @patch("boring.diff_patcher.extract_search_replace_blocks")
    def test_boring_extract_patches_success(self, mock_extract, mock_apply, mock_configure, mock_get_root):
        """Test patch extraction and application."""
        mock_get_root.return_value = (MagicMock(), None)
        
        # Mock extract
        mock_extract.return_value = [{"file_path": "test.py", "search": "old", "replace": "new"}]
        
        # Mock apply
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.file_path = "test.py"
        mock_apply.return_value = [mock_result]
        
        res = boring_extract_patches("AI output with patches")
        
        assert res["status"] == "SUCCESS"
        assert res["applied"] == 1
        assert res["failed"] == 0

    @patch("boring.mcp.tools.patching.get_project_root_or_error")
    @patch("boring.mcp.tools.patching.configure_runtime_for_project")
    @patch("boring.diff_patcher.extract_search_replace_blocks")
    def test_boring_extract_patches_dry_run(self, mock_extract, mock_configure, mock_get_root):
        """Test dry run mode."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_extract.return_value = [{"file_path": "test.py", "search": "old", "replace": "new"}]
        
        res = boring_extract_patches("AI output", dry_run=True)
        
        assert res["status"] == "SUCCESS"
        assert res["dry_run"] is True
        assert len(res["preview"]) == 1
