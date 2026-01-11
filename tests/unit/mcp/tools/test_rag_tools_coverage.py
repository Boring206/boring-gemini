
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.tools.rag import (
    register_rag_tools,
    reload_rag_dependencies,
)


class TestRAGTools:
    @pytest.fixture
    def mock_mcp(self):
        mcp = MagicMock()
        def tool_decorator(func):
            return func
        mcp.tool = MagicMock(return_value=tool_decorator)
        return mcp

    @pytest.fixture
    def mock_helpers(self):
        return {
            "get_project_root_or_error": MagicMock(return_value=(Path("."), None)),
            "get_session_id": MagicMock(return_value="session123"),
        }

    def test_reload_rag_dependencies(self):
        with patch("boring.rag.RAGRetriever", create=True):
            res = reload_rag_dependencies()
            assert "status" in res

    def test_rag_tools_integration(self, mock_mcp, mock_helpers):
        import boring.mcp.tools.rag as rag_mod

        tools = {}
        def fake_tool_decorator(func):
            tools[func.__name__] = func
            return func
        mock_mcp.tool = MagicMock(return_value=fake_tool_decorator)

        register_rag_tools(mock_mcp, mock_helpers)

        mock_ret = MagicMock()
        # Mock all needed methods
        mock_ret.build_index.return_value = 10
        mock_ret.retrieve.return_value = []

        class MockObj:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        mock_stats = MockObj(
            total_chunks_indexed=100,
            index_stats=MockObj(
                total_files=10,
                total_chunks=100,
                functions=50,
                classes=5,
                methods=30,
                script_chunks=5,
                skipped_files=0
            ),
            graph_stats=MockObj(
                total_nodes=15,
                total_edges=25
            )
        )
        mock_ret.get_stats.return_value = mock_stats

        # Mock for boring_rag_context target
        mock_chunk = MockObj(content="def test(): pass")
        mock_ret_obj = MockObj(chunk=mock_chunk)
        mock_ret.get_modification_context.return_value = {
            "target": [mock_ret_obj],
            "callers": [],
            "callees": [],
            "siblings": []
        }

        mock_ret.smart_expand.return_value = []
        mock_ret.collection = MagicMock()
        mock_ret.collection.count.return_value = 100
        mock_ret.persist_dir = Path("dummy_persist")
        mock_ret.is_available = True

        old_gr = rag_mod.get_retriever
        rag_mod.get_retriever = MagicMock(return_value=mock_ret)

        try:
            # 1. Index
            res = tools["boring_rag_index"](force=True)
            assert "10" in res

            # 2. Search
            res = tools["boring_rag_search"](query="test")
            assert "No results found" in res

            # 3. Status
            res = tools["boring_rag_status"]()
            assert "100" in str(res)

            # 4. Context
            res = tools["boring_rag_context"](file_path="test.py", function_name="test_func")
            assert "Context for" in res
            assert "Target" in res

            # 5. Expand
            res = tools["boring_rag_expand"](chunk_id="c1")
            assert "No additional context" in res
        finally:
            rag_mod.get_retriever = old_gr
