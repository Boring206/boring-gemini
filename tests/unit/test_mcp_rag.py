from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.tools.rag import register_rag_tools


class TestRagTools:
    """Tests for RAG MCP Tools."""

    @pytest.fixture
    def rag_tools(self):
        mcp = MagicMock()
        tools = {}

        # Helper to capture tools
        def mock_tool(description, annotations=None):
            def decorator(f):
                tools[f.__name__] = f
                return f

            return decorator

        mcp.tool = mock_tool

        helpers = {"get_project_root_or_error": lambda p: (Path(p) if p else Path("."), None)}

        register_rag_tools(mcp, helpers)
        return tools

    def test_boring_rag_status_not_available(self, rag_tools, tmp_path):
        with patch("boring.mcp.tools.rag.get_retriever", return_value=None):
            result = rag_tools["boring_rag_status"](project_path=str(tmp_path))
            assert result["status"] == "error"
            assert "❌ RAG Not Available" in result["message"]

    def test_boring_rag_index_not_available(self, rag_tools, tmp_path):
        with patch("boring.mcp.tools.rag.get_retriever", return_value=None):
            result = rag_tools["boring_rag_index"](project_path=str(tmp_path))
            assert result["status"] == "error"
            assert "❌ RAG module not available" in result["message"]

    def test_boring_rag_index_success(self, rag_tools, tmp_path):
        with patch("boring.mcp.tools.rag.get_retriever") as mock_ret:
            mock_ret.return_value.is_available = True
            mock_ret.return_value.build_index.return_value = 10
            mock_ret.return_value.get_stats.return_value = MagicMock(index_stats=None)

            result = rag_tools["boring_rag_index"](project_path=str(tmp_path))
            assert result["status"] == "success"
            assert "10 chunks" in result["message"]

    def test_boring_rag_search_not_available(self, rag_tools, tmp_path):
        with patch("boring.mcp.tools.rag.get_retriever", return_value=None):
            result = rag_tools["boring_rag_search"](query="test", project_path=str(tmp_path))
            assert result["status"] == "error"
            assert "❌ RAG module not available" in result["message"]

    def test_boring_rag_reload(self, rag_tools):
        with patch("boring.mcp.tools.rag.reload_rag_dependencies") as mock_reload:
            mock_reload.return_value = {"status": "SUCCESS", "message": "Reloaded"}
            result = rag_tools["boring_rag_reload"]()
            assert result["status"] == "success"
            assert "Reloaded" in result["message"]
