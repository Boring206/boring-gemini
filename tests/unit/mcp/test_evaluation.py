from pathlib import Path
from unittest.mock import MagicMock, patch

from boring.mcp.tools.evaluation import boring_evaluate


class TestEvaluationTools:
    @patch("boring.mcp.tools.evaluation.detect_project_root")
    @patch("boring.mcp.tools.evaluation.check_rate_limit")
    @patch("boring.mcp.tools.evaluation.create_judge_provider")
    @patch("boring.mcp.tools.evaluation.LLMJudge")
    def test_boring_evaluate_file(
        self, mock_judge_cls, mock_create_provider, mock_limit, mock_root
    ):
        """Test file evaluation."""
        mock_limit.return_value = (True, "")
        mock_root.return_value = Path("/tmp/project")

        # Setup mock provider
        mock_provider = MagicMock()
        mock_provider.is_available = True
        mock_create_provider.return_value = mock_provider

        mock_judge = MagicMock()
        mock_judge.grade_code.return_value = {
            "score": 4.5,
            "summary": "Good",
            "suggestions": ["Fix this"],
        }
        mock_judge_cls.return_value = mock_judge

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("pathlib.Path.is_absolute", return_value=True),
            patch("pathlib.Path.read_text", return_value="code"),
        ):
            res = boring_evaluate("/tmp/project/file.py", interactive=False)

            assert "🟢 Evaluation: file.py" in res
            assert "Score**: 4.5" in res

    @patch("boring.mcp.tools.evaluation.detect_project_root")
    @patch("boring.mcp.tools.evaluation.check_rate_limit")
    @patch("boring.mcp.tools.evaluation.os.environ.get")
    @patch("boring.mcp.tools.evaluation.create_judge_provider")
    @patch("boring.mcp.tools.evaluation.LLMJudge")
    def test_boring_evaluate_interactive(
        self, mock_judge_cls, mock_create_provider, mock_env, mock_limit, mock_root
    ):
        """Test interactive mode (prompt return)."""
        mock_limit.return_value = (True, "")
        mock_root.return_value = Path("/tmp/project")
        mock_env.return_value = "1"  # Simulate MCP mode

        # Setup mock provider
        mock_provider = MagicMock()
        mock_provider.is_available = True
        mock_create_provider.return_value = mock_provider

        mock_judge = MagicMock()
        mock_judge.grade_code.return_value = {
            "prompt": "SELECT * FROM CODE",
            "status": "pending_manual_review",
        }
        mock_judge_cls.return_value = mock_judge

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("pathlib.Path.is_absolute", return_value=True),
            patch("pathlib.Path.read_text", return_value="code"),
        ):
            # Call without interactive param, should default to True in MCP
            res = boring_evaluate("/tmp/project/file.py")

            assert "### 📋 Evaluation Prompt" in res
            assert "SELECT * FROM CODE" in res

    @patch("boring.mcp.tools.evaluation.detect_project_root")
    @patch("boring.mcp.tools.evaluation.check_rate_limit")
    def test_boring_evaluate_rate_limited(self, mock_limit, mock_root):
        """Test rate limit."""
        mock_limit.return_value = (False, "Too fast")

        res = boring_evaluate("foo.py")
        assert "Rate limited" in res
