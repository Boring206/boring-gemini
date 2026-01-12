import os
from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.verbosity import Verbosity, get_verbosity


class TestTokenOptimization:
    """Integration tests for Token Optimization features."""

    @pytest.fixture
    def mock_env_verbosity(self):
        """Fixture to manage environment variable."""
        original = os.environ.get("BORING_MCP_VERBOSITY")
        yield
        if original:
            os.environ["BORING_MCP_VERBOSITY"] = original
        else:
            os.environ.pop("BORING_MCP_VERBOSITY", None)

    def test_verbosity_resolution(self, mock_env_verbosity):
        """Test verbosity resolution priority: Arg > Env > Default."""
        # 1. Default
        os.environ.pop("BORING_MCP_VERBOSITY", None)
        assert get_verbosity(None) == Verbosity.STANDARD

        # 2. Env Var
        os.environ["BORING_MCP_VERBOSITY"] = "minimal"
        assert get_verbosity(None) == Verbosity.MINIMAL

        # 3. Argument Override (should win over Env)
        assert get_verbosity("verbose") == Verbosity.VERBOSE

        # 4. Unknown string check
        assert get_verbosity("unknown") == Verbosity.STANDARD

    def test_boring_discover_caching(self):
        """Test prompt caching markers in boring_discover (static check)."""
        from pathlib import Path

        # Read server.py directly to avoid complex import dependencies
        # Assuming current working directory is project root or we can find it
        # Based on file structure: src/boring/mcp/server.py

        # Try to locate the file relative to this test file
        current_dir = Path(__file__).parent
        # tests/integration -> ... -> src/boring/mcp/server.py
        # relative path: ../../src/boring/mcp/server.py
        server_py = current_dir.parent.parent / "src" / "boring" / "mcp" / "server.py"

        if not server_py.exists():
            # Fallback for different CWD
            server_py = Path("src/boring/mcp/server.py")

        if not server_py.exists():
            pytest.skip("Could not locate server.py for static analysis")

        content = server_py.read_text(encoding="utf-8")
        assert "<!-- CACHEABLE_CONTENT_START -->" in content
        assert "<!-- CACHEABLE_CONTENT_END -->" in content

    @patch("boring.config.settings")
    @patch("boring.security.SecurityScanner")
    def test_security_scan_verbosity(self, MockScanner, mock_settings):
        """Test boring_security_scan output formats."""
        from pathlib import Path

        from boring.mcp.tools.advanced import boring_security_scan

        # Mock settings
        mock_settings.PROJECT_ROOT = Path(".")

        # Setup mock report
        mock_report = MagicMock()
        mock_report.passed = False
        mock_report.total_issues = 15
        mock_report.secrets_found = 5
        mock_report.vulnerabilities_found = 5
        mock_report.dependency_issues = 5
        mock_report.issues = [
            MagicMock(severity="high", category="Secrets", message="Key found", line=10),
            MagicMock(severity="critical", category="SAST", message="Injection", line=20),
            MagicMock(severity="medium", category="Deps", message="Old lib", line=5),
        ] * 5  # 15 issues total

        mock_scanner_instance = MockScanner.return_value
        # Important: The tool accesses scanner.report property, not return value of scan()
        mock_scanner_instance.report = mock_report
        mock_scanner_instance.scan.return_value = None  # scan methods modify state in place

        # Mock Path.exists and read_text (if needed, though security scan uses its own logic)
        with (
            patch("pathlib.Path.is_absolute", return_value=True),
            patch("pathlib.Path.exists", return_value=True),
        ):
            # 1. MINIMAL
            result_min = boring_security_scan("test.py", verbosity="minimal")
            assert result_min["status"] == "failed"
            assert "issues" not in result_min  # Should not list issues
            assert "summary" in result_min
            assert "15 issues" in result_min["summary"]

            # 2. STANDARD
            result_std = boring_security_scan("test.py", verbosity="standard")
            assert "top_issues" in result_std
            assert len(result_std["top_issues"]) <= 5
            assert result_std["total_issues"] == 15

            # 3. VERBOSE
            result_verb = boring_security_scan("test.py", verbosity="verbose")
            assert "issues" in result_verb
            assert len(result_verb["issues"]) == 15

    @patch("boring.mcp.tools.vibe.vibe_engine.perform_code_review")
    def test_perf_tips_verbosity(self, mock_review):
        """Test boring_perf_tips output formats via factory."""
        from pathlib import Path

        from boring.mcp.tools.vibe import register_vibe_tools

        # Setup mocks for factory
        mock_mcp = MagicMock()
        # IMPORTANT: Mock decorator factories to return identity function
        # mcp.tool(args) -> decorator -> function
        mock_mcp.tool.return_value = lambda func: func

        def mock_audited(x):
            return x

        # Helper that returns success path
        mock_get_root = MagicMock()
        mock_get_root.return_value = (Path("."), None)
        helpers = {"get_project_root_or_error": mock_get_root}

        # Get tools map
        tools_map = register_vibe_tools(mock_mcp, mock_audited, helpers)
        boring_perf_tips = tools_map["boring_perf_tips"]

        # Setup mock result for code review
        mock_issue = MagicMock(severity="high", message="N+1 query", line=10, suggestion="Fix it")
        mock_result = MagicMock()
        mock_result.issues = [mock_issue] * 10  # 10 issues

        mock_review.return_value = mock_result

        # Mock Path.exists and read_text
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value="code"),
            patch("pathlib.Path.is_absolute", return_value=True),
        ):
            # 1. MINIMAL
            result_min = boring_perf_tips("api.py", verbosity="minimal")
            # assert "vibe_summary" in result_min["data"]
            assert "10 效能問題" in result_min["message"]

            # 2. STANDARD
            result_std = boring_perf_tips("api.py", verbosity="standard")
            # assert "vibe_summary" in result_std
            summary = result_std["message"]
            assert "🐌" in summary or "⚡" in summary
            assert "... and 5 more issues" in summary

            # 3. VERBOSE
            result_verb = boring_perf_tips("api.py", verbosity="verbose")
            assert "tips" in result_verb["data"]
            assert len(result_verb["data"]["tips"]) == 10
