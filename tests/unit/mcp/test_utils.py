"""
Critical Path Tests for MCP Utils Module
Achieves high coverage for the core utility functions used by all MCP tools
"""
import pytest
import time
import os
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path


class TestRateLimiting:
    """Tests for check_rate_limit function."""

    def test_rate_limit_allowed(self):
        """Test rate limit allows first call."""
        from boring.mcp.utils import check_rate_limit, _TOOL_CALL_COUNTS
        
        # Clear previous state
        _TOOL_CALL_COUNTS.clear()
        
        allowed, msg = check_rate_limit("test_tool")
        assert allowed == True
        assert msg == ""

    def test_rate_limit_tracks_calls(self):
        """Test rate limit tracks call timestamps."""
        from boring.mcp.utils import check_rate_limit, _TOOL_CALL_COUNTS
        
        _TOOL_CALL_COUNTS.clear()
        
        check_rate_limit("tracked_tool")
        assert len(_TOOL_CALL_COUNTS["tracked_tool"]) == 1

    def test_rate_limit_exceeded(self):
        """Test rate limit blocks when exceeded."""
        from boring.mcp.utils import check_rate_limit, _TOOL_CALL_COUNTS, _RATE_LIMITS
        
        _TOOL_CALL_COUNTS.clear()
        
        # Fill up rate limit for run_boring (limit=10)
        now = time.time()
        _TOOL_CALL_COUNTS["run_boring"] = [now - i for i in range(10)]
        
        allowed, msg = check_rate_limit("run_boring")
        assert allowed == False
        assert "Rate limit exceeded" in msg

    def test_rate_limit_cleans_old_entries(self):
        """Test rate limit cleans entries older than 1 hour."""
        from boring.mcp.utils import check_rate_limit, _TOOL_CALL_COUNTS
        
        _TOOL_CALL_COUNTS.clear()
        
        # Add old entries (more than 1 hour ago)
        old_time = time.time() - 3700
        _TOOL_CALL_COUNTS["old_tool"] = [old_time] * 100
        
        allowed, msg = check_rate_limit("old_tool")
        
        assert allowed == True
        # Old entries should be cleaned
        assert len([t for t in _TOOL_CALL_COUNTS["old_tool"] if t > time.time() - 3600]) <= 1

    def test_rate_limit_uses_default(self):
        """Test rate limit uses default limit for unknown tools."""
        from boring.mcp.utils import check_rate_limit, _TOOL_CALL_COUNTS, _RATE_LIMITS
        
        _TOOL_CALL_COUNTS.clear()
        
        # Default limit is 60
        for i in range(_RATE_LIMITS["default"]):
            allowed, _ = check_rate_limit("unknown_tool")
            if i < _RATE_LIMITS["default"] - 1:
                assert allowed == True


class TestProjectDetection:
    """Tests for detect_project_root function."""

    def test_detect_with_explicit_path(self, tmp_path):
        """Test detection with explicit path."""
        from boring.mcp.utils import detect_project_root
        
        result = detect_project_root(str(tmp_path))
        assert result == tmp_path

    def test_detect_with_nonexistent_path(self):
        """Test detection with non-existent path."""
        from boring.mcp.utils import detect_project_root
        
        result = detect_project_root("/nonexistent/path")
        # Should fall back to other detection methods
        assert result is None or result.exists()

    @patch.dict(os.environ, {"BORING_PROJECT_ROOT": ""})
    def test_detect_with_env_var(self, tmp_path):
        """Test detection with environment variable."""
        from boring.mcp.utils import detect_project_root
        
        os.environ["BORING_PROJECT_ROOT"] = str(tmp_path)
        
        result = detect_project_root(None)
        assert result == tmp_path
        
        del os.environ["BORING_PROJECT_ROOT"]

    def test_detect_with_anchor_file(self, tmp_path):
        """Test detection finds anchor files."""
        from boring.mcp.utils import detect_project_root
        
        # Create .git anchor
        (tmp_path / ".git").mkdir()
        
        with patch("boring.mcp.utils.Path.cwd", return_value=tmp_path):
            result = detect_project_root(None)
            assert result == tmp_path

    def test_detect_with_prompt_md(self, tmp_path):
        """Test detection finds PROMPT.md anchor."""
        from boring.mcp.utils import detect_project_root
        
        (tmp_path / "PROMPT.md").write_text("# Project")
        
        with patch("boring.mcp.utils.Path.cwd", return_value=tmp_path):
            result = detect_project_root(None)
            assert result == tmp_path


class TestEnsureProjectInitialized:
    """Tests for ensure_project_initialized function."""

    def test_creates_workflows_dir(self, tmp_path):
        """Test creates .agent/workflows directory."""
        from boring.mcp.utils import ensure_project_initialized
        
        ensure_project_initialized(tmp_path)
        
        assert (tmp_path / ".agent" / "workflows").exists()

    def test_creates_memory_dir(self, tmp_path):
        """Test creates .boring_memory directory."""
        from boring.mcp.utils import ensure_project_initialized
        
        ensure_project_initialized(tmp_path)
        
        assert (tmp_path / ".boring_memory").exists()

    def test_creates_gemini_dir(self, tmp_path):
        """Test creates .gemini directory."""
        from boring.mcp.utils import ensure_project_initialized
        
        ensure_project_initialized(tmp_path)
        
        assert (tmp_path / ".gemini").exists()

    def test_creates_prompt_md(self, tmp_path):
        """Test creates PROMPT.md if missing."""
        from boring.mcp.utils import ensure_project_initialized
        
        ensure_project_initialized(tmp_path)
        
        prompt_file = tmp_path / "PROMPT.md"
        assert prompt_file.exists()
        assert "Boring Project" in prompt_file.read_text() or "Task" in prompt_file.read_text()

    def test_does_not_overwrite_existing(self, tmp_path):
        """Test does not overwrite existing PROMPT.md."""
        from boring.mcp.utils import ensure_project_initialized
        
        prompt_file = tmp_path / "PROMPT.md"
        prompt_file.write_text("Original content")
        
        ensure_project_initialized(tmp_path)
        
        assert prompt_file.read_text() == "Original content"


class TestConfigureRuntime:
    """Tests for configure_runtime_for_project function."""

    def test_creates_log_dir(self, tmp_path):
        """Test creates logs directory."""
        from boring.mcp.utils import configure_runtime_for_project
        
        configure_runtime_for_project(tmp_path)
        
        assert (tmp_path / "logs").exists()

    @patch("boring.mcp.utils.config")
    def test_updates_settings(self, mock_config, tmp_path):
        """Test updates global settings."""
        from boring.mcp.utils import configure_runtime_for_project
        
        mock_settings = MagicMock()
        mock_config.settings = mock_settings
        
        configure_runtime_for_project(tmp_path)
        
        # Should have called object.__setattr__ to update settings
        # (Can't easily verify, but function shouldn't raise)


class TestGetProjectRootOrError:
    """Tests for get_project_root_or_error function."""

    def test_returns_root_when_found(self, tmp_path):
        """Test returns root when detected."""
        from boring.mcp.utils import get_project_root_or_error
        
        root, error = get_project_root_or_error(str(tmp_path))
        
        assert root == tmp_path
        assert error is None

    def test_returns_error_when_not_found(self):
        """Test returns error when not found."""
        from boring.mcp.utils import get_project_root_or_error
        
        with patch("boring.mcp.utils.detect_project_root", return_value=None):
            root, error = get_project_root_or_error(None)
            
            assert root is None
            assert error is not None
            assert error["status"] == "PROJECT_NOT_FOUND"

    def test_auto_init_when_found(self, tmp_path):
        """Test auto-initializes project when found."""
        from boring.mcp.utils import get_project_root_or_error
        
        with patch("boring.mcp.utils.ensure_project_initialized") as mock_init:
            get_project_root_or_error(str(tmp_path), auto_init=True)
            mock_init.assert_called_once()

    def test_skip_auto_init_when_disabled(self, tmp_path):
        """Test skips auto-init when disabled."""
        from boring.mcp.utils import get_project_root_or_error
        
        with patch("boring.mcp.utils.ensure_project_initialized") as mock_init:
            get_project_root_or_error(str(tmp_path), auto_init=False)
            mock_init.assert_not_called()


class TestTaskResult:
    """Tests for TaskResult dataclass."""

    def test_create_task_result(self):
        """Test TaskResult creation."""
        from boring.mcp.utils import TaskResult
        
        result = TaskResult(
            status="SUCCESS",
            files_modified=5,
            message="Done",
            loops_completed=3
        )
        
        assert result.status == "SUCCESS"
        assert result.files_modified == 5
        assert result.message == "Done"
        assert result.loops_completed == 3
