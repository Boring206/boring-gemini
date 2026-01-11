from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.brain_tools import register_brain_tools


class TestBrainTools:
    """Test suite for Brain MCP tools."""

    @pytest.fixture
    def mock_mcp(self):
        mcp = MagicMock()
        # Mock the tool decorator
        mcp.tool = MagicMock(return_value=lambda x: x)
        return mcp

    @pytest.fixture
    def helpers(self):
        return {
            "get_project_root_or_error": MagicMock(return_value=(MagicMock(), None)),
            "configure_runtime": MagicMock(),
        }

    def test_registration(self, mock_mcp, helpers):
        def audited(x):
            return x

        tools = register_brain_tools(mock_mcp, audited, helpers)
        assert "boring_learn" in tools
        assert "boring_brain_health" in tools
        assert mock_mcp.tool.call_count >= 10

    @patch("boring.intelligence.brain_manager.BrainManager")
    @patch("boring.storage.SQLiteStorage")
    def test_boring_learn_flow(self, mock_storage, mock_brain, mock_mcp, helpers):
        def audited(x):
            return x

        tools = register_brain_tools(mock_mcp, audited, helpers)
        learn_tool = tools["boring_learn"]

        learn_tool(project_path="/tmp/fake")
        assert mock_brain.return_value.learn_from_memory.called
        assert helpers["get_project_root_or_error"].called

    @patch("boring.intelligence.brain_manager.BrainManager")
    def test_boring_brain_health_fallback(self, mock_brain, mock_mcp, helpers):
        def audited(x):
            return x

        tools = register_brain_tools(mock_mcp, audited, helpers)
        health_tool = tools["boring_brain_health"]

        # Mock missing V10.23 method to test fallback
        del mock_brain.return_value.get_brain_health_report

        result = health_tool()
        assert "note" in result
        assert "using summary" in result["note"]

    @patch("boring.intelligence.brain_manager.BrainManager")
    def test_boring_incremental_learn(self, mock_brain, mock_mcp, helpers):
        def audited(x):
            return x

        tools = register_brain_tools(mock_mcp, audited, helpers)
        inc_tool = tools["boring_incremental_learn"]

        mock_brain.return_value.incremental_learn.return_value = {"pattern_id": "test-123"}

        result = inc_tool(error_message="msg", solution="sol")
        assert result["status"] == "SUCCESS"
        assert result["pattern_id"] == "test-123"

    @patch("boring.intelligence.brain_manager.get_global_knowledge_store")
    def test_boring_global_export(self, mock_global, mock_mcp, helpers):
        def audited(x):
            return x

        tools = register_brain_tools(mock_mcp, audited, helpers)
        export_tool = tools["boring_global_export"]

        mock_store = mock_global.return_value
        mock_store.export_from_project.return_value = {
            "status": "SUCCESS",
            "exported": 5,
            "total_global": 10,
        }

        result = export_tool()
        assert result["exported"] == 5
