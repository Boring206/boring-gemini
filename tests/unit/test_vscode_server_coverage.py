"""
Additional tests for VSCodeServer to increase coverage.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from boring.vscode_server import RPCResponse, VSCodeServer


class TestVSCodeServerCoverage:
    """Additional tests for VSCodeServer coverage."""

    @pytest.fixture
    def server(self, tmp_path):
        return VSCodeServer(project_root=tmp_path)

    @pytest.mark.asyncio
    async def test_handle_search_no_query(self, server):
        """Test search without query."""
        result = await server._handle_search({})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_handle_search_rag_not_available(self, server):
        """Test search when RAG is not available."""
        with patch("boring.rag.rag_retriever.RAGRetriever") as mock_rag:
            mock_instance = MagicMock()
            mock_instance.is_available = False
            mock_rag.return_value = mock_instance

            result = await server._handle_search({"query": "test"})
            assert "error" in result

    @pytest.mark.asyncio
    async def test_handle_status_error(self, server):
        """Test status handler with error."""
        with patch("boring.intelligence.memory.MemoryManager", side_effect=Exception("Test error")):
            result = await server._handle_status({})
            assert "error" in result

    @pytest.mark.asyncio
    async def test_handle_fix_no_file(self, server):
        """Test fix handler without file."""
        result = await server._handle_fix({})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_handle_evaluate_error(self, server):
        """Test evaluate handler with error."""
        with patch("boring.judge.create_judge_provider", side_effect=Exception("Error")):
            result = await server._handle_evaluate({"file": "test.py"})
            assert "error" in result

    @pytest.mark.asyncio
    async def test_handle_request_internal_error(self, server):
        """Test handle_request with internal error."""
        with patch.object(
            server, "_handlers", {"boring.test": lambda p: (_ for _ in ()).throw(Exception("Test"))}
        ):
            request = json.dumps({"jsonrpc": "2.0", "method": "boring.test", "params": {}, "id": 1})
            response = await server.handle_request(request)
            data = json.loads(response)
            assert "error" in data

    def test_rpc_response_to_dict_with_error(self):
        """Test RPCResponse.to_dict with error."""
        response = RPCResponse(error={"code": -1, "message": "Test error"}, id=1)
        d = response.to_dict()
        assert "error" in d
        assert d["error"]["code"] == -1

    def test_rpc_response_to_dict_with_result(self):
        """Test RPCResponse.to_dict with result."""
        response = RPCResponse(result={"status": "ok"}, id=1)
        d = response.to_dict()
        assert "result" in d
        assert d["result"]["status"] == "ok"
