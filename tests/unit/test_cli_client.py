import subprocess
from unittest.mock import MagicMock, patch

from boring.cli_client import (
    GeminiCLIAdapter,
    check_cli_authenticated,
    check_cli_available,
    create_cli_adapter,
)


class TestGeminiCLIAdapter:
    @patch("shutil.which")
    def test_init_success(self, mock_which):
        mock_which.return_value = "/usr/bin/gemini"
        adapter = GeminiCLIAdapter()
        assert adapter.is_available
        assert adapter.cli_path == "/usr/bin/gemini"

    @patch("shutil.which")
    def test_init_failure(self, mock_which):
        mock_which.return_value = None
        adapter = GeminiCLIAdapter()
        assert not adapter.is_available

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_generate_success(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/gemini"
        adapter = GeminiCLIAdapter()

        mock_run.return_value = MagicMock(returncode=0, stdout="Response text", stderr="")

        text, success = adapter.generate("Hello")
        assert success
        assert text == "Response text"
        mock_run.assert_called_once()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_generate_auth_error(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/gemini"
        adapter = GeminiCLIAdapter()

        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error: please login")

        text, success = adapter.generate("Hello")
        assert not success
        assert "login" in text.lower()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_generate_timeout(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/gemini"
        adapter = GeminiCLIAdapter()

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="gemini", timeout=300)

        text, success = adapter.generate("Hello")
        assert not success
        # assert "timeout" in text.lower()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_execute_cli_json_success(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/gemini"
        adapter = GeminiCLIAdapter()

        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"text": "JSON response"}', stderr=""
        )

        response = adapter._execute_cli_json("Hello")
        assert response.success
        assert response.text == "JSON response"

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_execute_cli_json_invalid(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/gemini"
        adapter = GeminiCLIAdapter()

        mock_run.return_value = MagicMock(returncode=0, stdout="Not JSON", stderr="")

        response = adapter._execute_cli_json("Hello")
        assert response.success
        assert response.text == "Not JSON"

    @patch("shutil.which")
    def test_create_cli_adapter_factory(self, mock_which):
        mock_which.return_value = "/bin/gemini"
        assert create_cli_adapter() is not None

        mock_which.return_value = None
        assert create_cli_adapter() is None


class TestCLIUtilities:
    @patch("shutil.which")
    def test_check_cli_available(self, mock_which):
        mock_which.return_value = "/bin/gemini"
        assert check_cli_available()

        mock_which.return_value = None
        assert not check_cli_available()

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_check_cli_authenticated_success(self, mock_which, mock_run):
        mock_which.return_value = "/bin/gemini"
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        is_auth, msg = check_cli_authenticated()
        assert is_auth
        assert "Authenticated" in msg

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_check_cli_authenticated_failure(self, mock_which, mock_run):
        mock_which.return_value = "/bin/gemini"
        mock_run.return_value = MagicMock(returncode=1, stderr="Please login")

        is_auth, msg = check_cli_authenticated()
        assert not is_auth
        assert "login" in msg.lower()
