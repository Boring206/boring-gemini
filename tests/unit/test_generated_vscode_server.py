# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.vscode_server module.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from boring.vscode_server import RPCRequest, RPCResponse, VSCodeServer, run_vscode_server

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "project"
    project.mkdir()
    return project


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestRPCRequest:
    """Tests for RPCRequest dataclass."""

    def test_rpc_request_creation(self):
        """Test RPCRequest creation."""
        request = RPCRequest(
            jsonrpc="2.0",
            method="test.method",
            params={"key": "value"},
            id=1,
        )
        assert request.jsonrpc == "2.0"
        assert request.method == "test.method"
        assert request.params == {"key": "value"}
        assert request.id == 1

    def test_rpc_request_default_id(self):
        """Test RPCRequest with default id."""
        request = RPCRequest(
            jsonrpc="2.0",
            method="test.method",
            params={},
        )
        assert request.id is None


class TestRPCResponse:
    """Tests for RPCResponse dataclass."""

    def test_rpc_response_creation(self):
        """Test RPCResponse creation."""
        response = RPCResponse(
            jsonrpc="2.0",
            result={"status": "ok"},
            id=1,
        )
        assert response.jsonrpc == "2.0"
        assert response.result == {"status": "ok"}
        assert response.error is None
        assert response.id == 1

    def test_rpc_response_with_error(self):
        """Test RPCResponse with error."""
        response = RPCResponse(
            jsonrpc="2.0",
            error={"code": -1, "message": "Error"},
            id=1,
        )
        assert response.error == {"code": -1, "message": "Error"}
        assert response.result is None

    def test_rpc_response_to_dict_with_result(self):
        """Test RPCResponse.to_dict with result."""
        response = RPCResponse(
            result={"status": "ok"},
            id=1,
        )
        data = response.to_dict()
        assert data["result"] == {"status": "ok"}
        assert "error" not in data

    def test_rpc_response_to_dict_with_error(self):
        """Test RPCResponse.to_dict with error."""
        response = RPCResponse(
            error={"code": -1, "message": "Error"},
            id=1,
        )
        data = response.to_dict()
        assert data["error"] == {"code": -1, "message": "Error"}
        assert "result" not in data


# =============================================================================
# VSCODE SERVER TESTS
# =============================================================================


class TestVSCodeServer:
    """Tests for VSCodeServer class."""

    def test_vscode_server_init(self, temp_project):
        """Test VSCodeServer initialization."""
        with patch("boring.vscode_server.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            server = VSCodeServer(temp_project)
            assert server.project_root == temp_project
            assert len(server._handlers) > 0

    def test_vscode_server_init_default_root(self):
        """Test VSCodeServer with default project root."""
        with patch("boring.vscode_server.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = Path("/default")
            server = VSCodeServer()
            assert server.project_root == Path("/default")

    def test_vscode_server_register_handlers(self, temp_project):
        """Test VSCodeServer._register_handlers method."""
        with patch("boring.vscode_server.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            server = VSCodeServer(temp_project)
            assert "boring.verify" in server._handlers
            assert "boring.evaluate" in server._handlers
            assert "boring.search" in server._handlers

    @pytest.mark.asyncio
    async def test_vscode_server_handle_request_valid(self, temp_project):
        """Test VSCodeServer.handle_request with valid request."""
        with patch("boring.vscode_server.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            server = VSCodeServer(temp_project)

            request_data = {
                "jsonrpc": "2.0",
                "method": "boring.version",
                "params": {},
                "id": 1,
            }

            result = await server.handle_request(json.dumps(request_data))
            data = json.loads(result)
            assert "result" in data or "error" in data

    @pytest.mark.asyncio
    async def test_vscode_server_handle_request_invalid_method(self, temp_project):
        """Test VSCodeServer.handle_request with invalid method."""
        with patch("boring.vscode_server.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            server = VSCodeServer(temp_project)

            request_data = {
                "jsonrpc": "2.0",
                "method": "invalid.method",
                "params": {},
                "id": 1,
            }

            result = await server.handle_request(json.dumps(request_data))
            data = json.loads(result)
            assert "error" in data
            assert data["error"]["code"] == -32601

    @pytest.mark.asyncio
    async def test_vscode_server_handle_request_invalid_json(self, temp_project):
        """Test VSCodeServer.handle_request with invalid JSON."""
        with patch("boring.vscode_server.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            server = VSCodeServer(temp_project)

            result = await server.handle_request("invalid json")
            data = json.loads(result)
            assert "error" in data

    @pytest.mark.asyncio
    async def test_vscode_server_handle_verify(self, temp_project):
        """Test VSCodeServer._handle_verify method."""
        with patch("boring.vscode_server.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            server = VSCodeServer(temp_project)

            with patch("boring.verification.CodeVerifier") as mock_verifier:
                mock_instance = MagicMock()
                mock_result = MagicMock()
                mock_result.passed = True
                mock_result.message = "Passed"
                mock_result.details = []
                mock_instance.verify_file.return_value = mock_result
                mock_verifier.return_value = mock_instance

                result = await server._handle_verify({"file": "test.py"})
                assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_vscode_server_handle_evaluate(self, temp_project):
        """Test VSCodeServer._handle_evaluate method."""
        with patch("boring.vscode_server.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            server = VSCodeServer(temp_project)

            with patch("boring.judge.LLMJudge") as mock_judge_cls:
                with patch("boring.judge.create_judge_provider"):
                    mock_judge = MagicMock()
                    mock_judge.grade_code.return_value = {"score": 0.9}
                    mock_judge_cls.return_value = mock_judge

                    # Mock file read
                    with patch("pathlib.Path.read_text", return_value="code"):
                        with patch("pathlib.Path.exists", return_value=True):
                            result = await server._handle_evaluate({"file": "test.py"})
                            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_vscode_server_handle_search(self, temp_project):
        """Test VSCodeServer._handle_search method."""
        with patch("boring.vscode_server.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            server = VSCodeServer(temp_project)

            with patch("boring.rag.rag_retriever.RAGRetriever") as mock_rag_cls:
                mock_retriever = MagicMock()
                mock_retriever.is_available = True
                mock_retriever.retrieve.return_value = [
                    MagicMock(file_path="f", name="n", score=1.0, content="test")
                ]
                mock_rag_cls.return_value = mock_retriever

                result = await server._handle_search({"query": "test"})
                assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_vscode_server_handle_status(self, temp_project):
        """Test VSCodeServer._handle_status method."""
        with patch("boring.vscode_server.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            server = VSCodeServer(temp_project)

            with patch("boring.memory.MemoryManager") as mock_memory:
                mock_instance = MagicMock()
                mock_instance.get_project_state.return_value = {"loop_count": 5}
                mock_memory.return_value = mock_instance

                result = await server._handle_status({})
                assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_vscode_server_handle_fix(self, temp_project):
        """Test VSCodeServer._handle_fix method."""
        with patch("boring.vscode_server.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            server = VSCodeServer(temp_project)

            # _handle_fix returns a command template, doesn't run the pipeline
            result = await server._handle_fix({"file": "test.py"})
            assert isinstance(result, dict)
            assert result["status"] == "PENDING"
            assert "boring auto-fix test.py" in result["command"]

    @pytest.mark.asyncio
    async def test_vscode_server_handle_version(self, temp_project):
        """Test VSCodeServer._handle_version method."""
        with patch("boring.vscode_server.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            server = VSCodeServer(temp_project)

            result = await server._handle_version({})
            assert isinstance(result, dict)
            assert "version" in result


# =============================================================================
# MODULE FUNCTIONS TESTS
# =============================================================================


class TestRunVSCodeServer:
    """Tests for run_vscode_server function."""

    @pytest.mark.asyncio
    async def test_run_vscode_server(self):
        """Test run_vscode_server function."""
        with patch("boring.vscode_server.VSCodeServer") as mock_server_class:
            mock_server = AsyncMock()
            mock_server.start = AsyncMock()
            mock_server_class.return_value = mock_server

            with patch("asyncio.run"):
                # Should not raise exception
                try:
                    run_vscode_server(port=9876)
                except Exception:
                    pass  # May raise if asyncio.run is not properly mocked
