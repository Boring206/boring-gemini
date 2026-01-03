import pytest
from unittest.mock import MagicMock, patch
from boring.mcp.tools.speckit import speckit_plan, speckit_analyze

class TestSpecKitTools:

    @patch("boring.mcp.tools.speckit.get_project_root_or_error")
    @patch("boring.mcp.tools.speckit._read_workflow")
    @patch("boring.cli_client.GeminiCLIAdapter") # Mock CLI path
    def test_speckit_tool_execution(self, mock_cli_cls, mock_read_workflow, mock_get_root):
        """Test a speckit tool execution via CLI adapter."""
        mock_get_root.return_value = (MagicMock(), None)
        mock_read_workflow.return_value = "# Workflow Plan"
        
        # Mock CLI execution
        mock_cli_instance = MagicMock()
        mock_cli_instance.generate_with_retry.return_value = "Plan Generated"
        mock_cli_cls.return_value = mock_cli_instance
        
        # Mock shutil.which to simulate CLI presence
        with patch("shutil.which", return_value="/usr/bin/gemini"):
            res = speckit_plan(context="Context")
            
            assert res["status"] == "SUCCESS"
            assert res["mode"] == "CLI"
            assert res["result"] == "Plan Generated"

    @patch("boring.mcp.tools.speckit.get_project_root_or_error")
    @patch("boring.mcp.tools.speckit._read_workflow")
    @patch("boring.gemini_client.GeminiClient") # Mock SDK path
    def test_speckit_sdk_fallback(self, mock_sdk_cls, mock_read_workflow, mock_get_root):
        """Test fallback to SDK when CLI is missing."""
        mock_get_root.return_value = (MagicMock(), None)
        mock_read_workflow.return_value = "# Workflow"
        
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.generate.return_value = "Result"
        mock_sdk_cls.return_value = mock_sdk_instance
        
        # Mock no CLI
        with patch("shutil.which", return_value=None):
            res = speckit_analyze()
            
            assert res["status"] == "SUCCESS"
            assert res["mode"] == "SDK"
