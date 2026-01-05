from unittest.mock import MagicMock, patch

from boring.mcp.tools.speckit import speckit_analyze, speckit_plan


class TestSpecKitTools:
    @patch("boring.mcp.tools.speckit.get_project_root_or_error")
    @patch("boring.mcp.tools.speckit._read_workflow")
    def test_speckit_tool_execution(self, mock_read_workflow, mock_get_root):
        """Test a speckit tool returns WORKFLOW_TEMPLATE."""
        mock_get_root.return_value = (MagicMock(), None)
        mock_read_workflow.return_value = """---
description: Test Description
---
# Workflow Plan
1. Step A
2. Step B"""

        # Call the tool
        res = speckit_plan(context="Context")

        # Assert workflow template structure
        assert res["status"] == "WORKFLOW_TEMPLATE"
        assert res["workflow"] == "speckit-plan"
        assert "cli_command" in res
        assert "suggested_prompt" in res
        assert res["auto_execute"] is False  # Default
        assert res["description"] == "Test Description"
        assert res["steps_count"] == 2

    @patch("boring.mcp.tools.speckit.get_project_root_or_error")
    @patch("boring.mcp.tools.speckit._read_workflow")
    def test_speckit_auto_execute(self, mock_read_workflow, mock_get_root):
        """Test speckit tool with auto_execute=True."""
        mock_get_root.return_value = (MagicMock(), None)
        mock_read_workflow.return_value = """---
description: Auto Exec
---
1. Step 1"""

        res = speckit_analyze(auto_execute=True)

        assert res["status"] == "WORKFLOW_TEMPLATE"
        assert res["auto_execute"] is True
        assert "Auto-Execute Requested" in res["message"]
