"""
Unit tests for cli_client.py

Tests Gemini CLI Adapter for privacy-focused backend.
"""

import json
import subprocess
from unittest.mock import Mock, patch

import pytest

from boring.cli_client import (
    CLIResponse,
    GeminiCLIAdapter,
    check_cli_authenticated,
    check_cli_available,
    create_cli_adapter,
)


class TestCLIResponse:
    """Test CLIResponse dataclass."""

    def test_cli_response_creation(self):
        """Test creating a CLIResponse."""
        response = CLIResponse(text="Hello", success=True)
        assert response.text == "Hello"
        assert response.success is True
        assert response.error is None

    def test_cli_response_with_error(self):
        """Test creating a CLIResponse with error."""
        response = CLIResponse(text="Error", success=False, error="Something went wrong")
        assert response.text == "Error"
        assert response.success is False
        assert response.error == "Something went wrong"


class TestGeminiCLIAdapter:
    """Test GeminiCLIAdapter class."""

    @pytest.fixture
    def temp_log_dir(self, tmp_path):
        """Create a temporary log directory."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        return log_dir

    @patch("boring.cli_client.shutil.which")
    @patch("boring.cli_client.log_status")
    def test_adapter_initialization_with_cli(self, mock_log_status, mock_which, temp_log_dir):
        """Test adapter initialization when CLI is available."""
        mock_which.return_value = "/usr/bin/gemini"
        adapter = GeminiCLIAdapter(model_name="test-model", log_dir=temp_log_dir)
        assert adapter._model_name == "test-model"
        assert adapter.log_dir == temp_log_dir
        assert adapter.cli_path == "/usr/bin/gemini"
        assert adapter.is_available is True
        mock_log_status.assert_called()

    @patch("boring.cli_client.shutil.which")
    @patch("boring.cli_client.log_status")
    def test_adapter_initialization_without_cli(self, mock_log_status, mock_which, temp_log_dir):
        """Test adapter initialization when CLI is not available."""
        mock_which.return_value = None
        adapter = GeminiCLIAdapter(model_name="test-model", log_dir=temp_log_dir)
        assert adapter.cli_path is None
        assert adapter.is_available is False
        mock_log_status.assert_called()

    def test_adapter_properties(self, temp_log_dir):
        """Test adapter properties."""
        with patch("boring.cli_client.shutil.which", return_value="/usr/bin/gemini"):
            adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
            assert adapter.provider_name == "gemini_cli"
            assert adapter.base_url is None
            assert adapter.model_name == "gemini-2.0-flash-exp"

    @patch("boring.cli_client.subprocess.run")
    @patch("boring.cli_client.shutil.which")
    def test_execute_cli_success(self, mock_which, mock_run, temp_log_dir):
        """Test _execute_cli with successful execution."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_run.return_value = Mock(returncode=0, stdout="Response text", stderr="")
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        response = adapter._execute_cli("Test prompt")
        assert response.success is True
        assert response.text == "Response text"
        mock_run.assert_called_once()

    @patch("boring.cli_client.subprocess.run")
    @patch("boring.cli_client.shutil.which")
    def test_execute_cli_with_model(self, mock_which, mock_run, temp_log_dir):
        """Test _execute_cli with custom model."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_run.return_value = Mock(returncode=0, stdout="Response", stderr="")
        adapter = GeminiCLIAdapter(model_name="custom-model", log_dir=temp_log_dir)
        adapter._execute_cli("Test")
        call_args = mock_run.call_args[0][0]
        assert "-m" in call_args
        assert "custom-model" in call_args

    @patch("boring.cli_client.subprocess.run")
    @patch("boring.cli_client.shutil.which")
    def test_execute_cli_authentication_error(self, mock_which, mock_run, temp_log_dir):
        """Test _execute_cli with authentication error."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Please login")
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        with pytest.raises(PermissionError):
            adapter._execute_cli("Test")

    @patch("boring.cli_client.subprocess.run")
    @patch("boring.cli_client.shutil.which")
    def test_execute_cli_returncode_error(self, mock_which, mock_run, temp_log_dir):
        """Test _execute_cli with non-zero return code."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Error message")
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        response = adapter._execute_cli("Test")
        assert response.success is False
        assert "Error message" in response.error

    @patch("boring.cli_client.subprocess.run")
    @patch("boring.cli_client.shutil.which")
    def test_execute_cli_timeout(self, mock_which, mock_run, temp_log_dir):
        """Test _execute_cli with timeout."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_run.side_effect = subprocess.TimeoutExpired("gemini", 10)
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        response = adapter._execute_cli("Test")
        assert response.success is False
        assert "timed out" in response.text

    @patch("boring.cli_client.subprocess.run")
    @patch("boring.cli_client.shutil.which")
    def test_execute_cli_file_not_found(self, mock_which, mock_run, temp_log_dir):
        """Test _execute_cli when CLI is not found."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_run.side_effect = FileNotFoundError()
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        with pytest.raises(FileNotFoundError):
            adapter._execute_cli("Test")

    @patch("boring.cli_client.subprocess.run")
    @patch("boring.cli_client.shutil.which")
    def test_execute_cli_json_success(self, mock_which, mock_run, temp_log_dir):
        """Test _execute_cli_json with successful execution."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_run.return_value = Mock(
            returncode=0, stdout=json.dumps({"text": "Response"}), stderr=""
        )
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        response = adapter._execute_cli_json("Test")
        assert response.success is True
        assert response.text == "Response"

    @patch("boring.cli_client.subprocess.run")
    @patch("boring.cli_client.shutil.which")
    def test_execute_cli_json_invalid_json(self, mock_which, mock_run, temp_log_dir):
        """Test _execute_cli_json with invalid JSON."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_run.return_value = Mock(returncode=0, stdout="Not JSON", stderr="")
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        response = adapter._execute_cli_json("Test")
        assert response.success is True
        assert response.text == "Not JSON"

    @patch("boring.cli_client.GeminiCLIAdapter._execute_cli")
    @patch("boring.cli_client.shutil.which")
    def test_generate_success(self, mock_which, mock_execute, temp_log_dir):
        """Test generate method with success."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_execute.return_value = CLIResponse(text="Response", success=True)
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        text, success = adapter.generate("Prompt", context="Context")
        assert success is True
        assert text == "Response"
        mock_execute.assert_called_once()

    @patch("boring.cli_client.GeminiCLIAdapter._execute_cli")
    @patch("boring.cli_client.shutil.which")
    @patch("boring.cli_client.log_status")
    def test_generate_permission_error(
        self, mock_log_status, mock_which, mock_execute, temp_log_dir
    ):
        """Test generate method with PermissionError."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_execute.side_effect = PermissionError("Not authenticated")
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        text, success = adapter.generate("Prompt")
        assert success is False
        assert "Not authenticated" in text

    @patch("boring.cli_client.GeminiCLIAdapter._execute_cli")
    @patch("boring.cli_client.shutil.which")
    @patch("boring.cli_client.log_status")
    def test_generate_exception(self, mock_log_status, mock_which, mock_execute, temp_log_dir):
        """Test generate method with general exception."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_execute.side_effect = Exception("CLI error")
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        text, success = adapter.generate("Prompt")
        assert success is False
        assert "CLI error" in text

    @patch("boring.cli_client.GeminiCLIAdapter.generate")
    @patch("boring.cli_client.shutil.which")
    def test_generate_with_tools_success(self, mock_which, mock_generate, temp_log_dir):
        """Test generate_with_tools with successful generation."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_generate.return_value = ("Response text", True)
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        response = adapter.generate_with_tools("Prompt", context="Context", tools=[])
        assert response.success is True
        assert response.text == "Response text"
        assert response.function_calls == []

    @patch("boring.cli_client.GeminiCLIAdapter.generate")
    @patch("boring.cli_client.shutil.which")
    def test_generate_with_tools_failure(self, mock_which, mock_generate, temp_log_dir):
        """Test generate_with_tools with generation failure."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_generate.return_value = ("Error", False)
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        response = adapter.generate_with_tools("Prompt")
        assert response.success is False
        assert response.error == "CLI generation failed"

    @patch("boring.cli_client.GeminiCLIAdapter.generate")
    @patch("boring.cli_client.shutil.which")
    @patch("boring.cli_client.log_status")
    def test_generate_with_tools_parse_json(
        self, mock_log_status, mock_which, mock_generate, temp_log_dir
    ):
        """Test generate_with_tools parsing JSON tool calls."""
        mock_which.return_value = "/usr/bin/gemini"
        tool_calls_json = json.dumps(
            {"tool_calls": [{"name": "test_tool", "arguments": {"arg": "value"}}]}
        )
        mock_generate.return_value = (f"Text\n```json\n{tool_calls_json}\n```", True)
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        response = adapter.generate_with_tools("Prompt", tools=[])
        assert response.success is True
        assert len(response.function_calls) == 1
        assert response.function_calls[0]["name"] == "test_tool"

    @patch("boring.cli_client.GeminiCLIAdapter.generate")
    @patch("boring.cli_client.shutil.which")
    @patch("boring.cli_client.log_status")
    def test_generate_with_tools_invalid_json(
        self, mock_log_status, mock_which, mock_generate, temp_log_dir
    ):
        """Test generate_with_tools with invalid JSON."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_generate.return_value = ("Text\n```json\n{invalid}\n```", True)
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        response = adapter.generate_with_tools("Prompt")
        assert response.success is True
        assert response.function_calls == []

    @patch("boring.cli_client.GeminiCLIAdapter.generate")
    @patch("boring.cli_client.shutil.which")
    def test_generate_with_retry_success(self, mock_which, mock_generate, temp_log_dir):
        """Test generate_with_retry with immediate success."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_generate.return_value = ("Response", True)
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        text, success = adapter.generate_with_retry("Prompt")
        assert success is True
        assert text == "Response"
        assert mock_generate.call_count == 1

    @patch("boring.cli_client.GeminiCLIAdapter.generate")
    @patch("boring.cli_client.shutil.which")
    @patch("boring.cli_client.log_status")
    def test_generate_with_retry_auth_error(
        self, mock_log_status, mock_which, mock_generate, temp_log_dir
    ):
        """Test generate_with_retry with authentication error (no retry)."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_generate.return_value = ("Please login", False)
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        text, success = adapter.generate_with_retry("Prompt")
        assert success is False
        assert mock_generate.call_count == 1  # No retry for auth errors

    @patch("boring.cli_client.GeminiCLIAdapter.generate")
    @patch("boring.cli_client.shutil.which")
    @patch("boring.cli_client.log_status")
    def test_generate_with_retry_transient_error(
        self, mock_log_status, mock_which, mock_generate, temp_log_dir
    ):
        """Test generate_with_retry with transient error (retries)."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_generate.side_effect = [("Error", False), ("Response", True)]
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        text, success = adapter.generate_with_retry("Prompt", max_retries=3)
        assert success is True
        assert mock_generate.call_count == 2

    @patch("boring.cli_client.GeminiCLIAdapter.generate")
    @patch("boring.cli_client.shutil.which")
    def test_chat_success(self, mock_which, mock_generate, temp_log_dir):
        """Test chat method with success."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_generate.return_value = ("Response", True)
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        result = adapter.chat("Prompt")
        assert result == "Response"

    @patch("boring.cli_client.GeminiCLIAdapter.generate")
    @patch("boring.cli_client.shutil.which")
    def test_chat_failure(self, mock_which, mock_generate, temp_log_dir):
        """Test chat method with failure."""
        mock_which.return_value = "/usr/bin/gemini"
        mock_generate.return_value = ("Error", False)
        adapter = GeminiCLIAdapter(log_dir=temp_log_dir)
        with pytest.raises(RuntimeError):
            adapter.chat("Prompt")


class TestCheckCLIAvailable:
    """Test check_cli_available function."""

    @patch("boring.cli_client.shutil.which")
    def test_check_cli_available_true(self, mock_which):
        """Test check_cli_available when CLI is available."""
        mock_which.return_value = "/usr/bin/gemini"
        assert check_cli_available() is True

    @patch("boring.cli_client.shutil.which")
    def test_check_cli_available_false(self, mock_which):
        """Test check_cli_available when CLI is not available."""
        mock_which.return_value = None
        assert check_cli_available() is False


class TestCheckCLIAuthenticated:
    """Test check_cli_authenticated function."""

    @patch("boring.cli_client.check_cli_available")
    @patch("boring.cli_client.subprocess.run")
    def test_check_cli_authenticated_not_installed(self, mock_run, mock_check):
        """Test check_cli_authenticated when CLI is not installed."""
        mock_check.return_value = False
        is_auth, message = check_cli_authenticated()
        assert is_auth is False
        assert "not installed" in message

    @patch("boring.cli_client.check_cli_available")
    @patch("boring.cli_client.subprocess.run")
    def test_check_cli_authenticated_success(self, mock_run, mock_check):
        """Test check_cli_authenticated when authenticated."""
        mock_check.return_value = True
        mock_run.return_value = Mock(returncode=0, stderr="")
        is_auth, message = check_cli_authenticated()
        assert is_auth is True
        assert message == "Authenticated"

    @patch("boring.cli_client.check_cli_available")
    @patch("boring.cli_client.subprocess.run")
    def test_check_cli_authenticated_not_authenticated(self, mock_run, mock_check):
        """Test check_cli_authenticated when not authenticated."""
        mock_check.return_value = True
        mock_run.return_value = Mock(returncode=1, stderr="Please login")
        is_auth, message = check_cli_authenticated()
        assert is_auth is False
        assert "login" in message.lower()

    @patch("boring.cli_client.check_cli_available")
    @patch("boring.cli_client.subprocess.run")
    def test_check_cli_authenticated_timeout(self, mock_run, mock_check):
        """Test check_cli_authenticated with timeout."""
        mock_check.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("gemini", 5)
        is_auth, message = check_cli_authenticated()
        assert is_auth is False
        assert "timed out" in message

    @patch("boring.cli_client.check_cli_available")
    @patch("boring.cli_client.subprocess.run")
    def test_check_cli_authenticated_exception(self, mock_run, mock_check):
        """Test check_cli_authenticated with exception."""
        mock_check.return_value = True
        mock_run.side_effect = Exception("Error")
        is_auth, message = check_cli_authenticated()
        assert is_auth is False
        assert "Error" in message


class TestCreateCLIAdapter:
    """Test create_cli_adapter function."""

    @patch("boring.cli_client.GeminiCLIAdapter")
    @patch("boring.cli_client.log_status")
    def test_create_cli_adapter_success(self, mock_log_status, mock_adapter_class, tmp_path):
        """Test create_cli_adapter when CLI is available."""
        mock_adapter = Mock()
        mock_adapter.is_available = True
        mock_adapter_class.return_value = mock_adapter
        result = create_cli_adapter(log_dir=tmp_path)
        assert result == mock_adapter

    @patch("boring.cli_client.GeminiCLIAdapter")
    @patch("boring.cli_client.log_status")
    def test_create_cli_adapter_not_available(self, mock_log_status, mock_adapter_class, tmp_path):
        """Test create_cli_adapter when CLI is not available."""
        mock_adapter = Mock()
        mock_adapter.is_available = False
        mock_adapter_class.return_value = mock_adapter
        result = create_cli_adapter(log_dir=tmp_path)
        assert result is None

    @patch("boring.cli_client.GeminiCLIAdapter")
    @patch("boring.cli_client.log_status")
    def test_create_cli_adapter_exception(self, mock_log_status, mock_adapter_class, tmp_path):
        """Test create_cli_adapter when exception occurs."""
        mock_adapter_class.side_effect = Exception("Error")
        result = create_cli_adapter(log_dir=tmp_path)
        assert result is None
        mock_log_status.assert_called()
