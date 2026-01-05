from unittest.mock import MagicMock, patch

from boring.mcp.tools.verification import boring_verify, boring_verify_file


class TestVerificationTools:
    @patch("boring.mcp.tools.verification.get_project_root_or_error")
    @patch("boring.verification.CodeVerifier")
    def test_boring_verify_success(self, mock_verifier_cls, mock_get_root):
        """Test successful project verification."""
        mock_get_root.return_value = (MagicMock(), None)

        mock_instance = MagicMock()
        mock_instance.verify_project.return_value = (True, "All passed")
        mock_verifier_cls.return_value = mock_instance

        res = boring_verify(level="STANDARD")
        assert res["passed"]
        assert res["level"] == "STANDARD"

    @patch("boring.mcp.tools.verification.get_project_root_or_error")
    @patch("boring.mcp.tools.verification.configure_runtime_for_project")
    @patch("boring.verification.CodeVerifier")
    def test_boring_verify_file(self, mock_verifier_cls, mock_configure, mock_get_root):
        """Test single file verification."""
        mock_root = MagicMock()

        # Mock / operator (project_root / file_path)
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.suffix = ".py"
        mock_file.relative_to.return_value = "src/test.py"
        mock_root.__truediv__.return_value = mock_file

        mock_get_root.return_value = (mock_root, None)

        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.passed = True
        mock_result.suggestions = []
        mock_instance.verify_file.return_value = [mock_result]
        mock_verifier_cls.return_value = mock_instance

        res = boring_verify_file("src/test.py")
        assert res["status"] == "SUCCESS"
        assert res["passed"]
