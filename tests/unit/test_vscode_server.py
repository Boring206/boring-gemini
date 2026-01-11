import json
from unittest.mock import patch

import pytest

from boring.vscode_server import RPCResponse, VSCodeServer


class TestVSCodeServer:
    """Test suite for VSCode Integration Server."""

    @pytest.fixture
    def server(self, tmp_path):
        return VSCodeServer(project_root=tmp_path)

    @pytest.mark.asyncio
    async def test_handle_request_success(self, server):
        # Test boring.version
        request = json.dumps({"jsonrpc": "2.0", "method": "boring.version", "params": {}, "id": 1})
        response_json = await server.handle_request(request)
        response = json.loads(response_json)
        assert response["id"] == 1
        assert "version" in response["result"]

    @pytest.mark.asyncio
    async def test_handle_request_method_not_found(self, server):
        request = json.dumps({"jsonrpc": "2.0", "method": "boring.unknown", "params": {}, "id": 99})
        response_json = await server.handle_request(request)
        response = json.loads(response_json)
        assert response["error"]["code"] == -32601

    @pytest.mark.asyncio
    async def test_handle_request_parse_error(self, server):
        response_json = await server.handle_request("invalid json")
        response = json.loads(response_json)
        assert response["error"]["code"] == -32700

    @pytest.mark.asyncio
    async def test_handle_verify(self, server, tmp_path):
        with patch("boring.verification.CodeVerifier") as mock_verifier:
            mock_instance = mock_verifier.return_value
            mock_instance.verify_project.return_value = (True, "Success")

            params = {"level": "FULL"}
            result = await server._handle_verify(params)
            assert result["passed"] is True
            assert result["message"] == "Success"

    @pytest.mark.asyncio
    async def test_handle_evaluate_file_not_found(self, server):
        result = await server._handle_evaluate({"file": "missing.py"})
        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_handle_search_missing_query(self, server):
        result = await server._handle_search({})
        assert "error" in result
        assert "query parameter required" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_fix(self, server):
        result = await server._handle_fix({"file": "test.py"})
        assert "command" in result
        assert "boring auto-fix test.py" in result["command"]

    def test_rpc_response_to_dict(self):
        resp = RPCResponse(result={"data": 123}, id=1)
        d = resp.to_dict()
        assert d["result"]["data"] == 123
        assert d["id"] == 1

        err_resp = RPCResponse(error={"message": "fail"}, id=2)
        ed = err_resp.to_dict()
        assert "error" in ed
        assert "result" not in ed
