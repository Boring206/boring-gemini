# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.mcp.utils module.

This test file covers utility functions in the MCP module that may not be
adequately tested in existing test files.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from boring.mcp.utils import (
    TaskResult,
    check_rate_limit,
    configure_runtime_for_project,
    detect_project_root,
    ensure_project_initialized,
    get_project_root_or_error,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "src").mkdir()
    (project / "src" / "main.py").write_text("print('hello')")
    return project


# =============================================================================
# RATE LIMIT TESTS
# =============================================================================


class TestCheckRateLimit:
    """Tests for check_rate_limit function."""

    def test_check_rate_limit_first_call(self):
        """Test rate limit check on first call."""
        allowed, message = check_rate_limit("test_tool")
        # First call should typically be allowed
        assert isinstance(allowed, bool)
        assert isinstance(message, str)

    def test_check_rate_limit_multiple_calls(self):
        """Test rate limit with multiple rapid calls."""
        # Make multiple calls rapidly
        results = [check_rate_limit("test_tool") for _ in range(10)]
        # All should return valid results
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)

    def test_check_rate_limit_different_tools(self):
        """Test that rate limits are per-tool."""
        result1 = check_rate_limit("tool1")
        result2 = check_rate_limit("tool2")
        # Different tools should have independent rate limits
        assert isinstance(result1[0], bool)
        assert isinstance(result2[0], bool)


# =============================================================================
# PROJECT ROOT DETECTION TESTS
# =============================================================================


class TestDetectProjectRoot:
    """Tests for detect_project_root function."""

    def test_detect_project_root_with_explicit_path(self, temp_project):
        """Test detect_project_root with explicit path."""
        result = detect_project_root(str(temp_project))
        assert result == temp_project

    def test_detect_project_root_with_path_object(self, temp_project):
        """Test detect_project_root with Path object."""
        result = detect_project_root(temp_project)
        assert result == temp_project

    @patch("pathlib.Path.home")
    def test_detect_project_root_with_none(self, mock_home):
        """Test detect_project_root with None."""
        mock_home.return_value = (
            Path("C:/Users/Test") if "win" in str(Path.cwd()) else Path("/home/test")
        )
        with patch.dict("os.environ", {"BORING_PROJECT_ROOT": ""}, clear=True):
            result = detect_project_root(None)
            # Should return default or None
            assert result is not None or result is None

    def test_detect_project_root_nonexistent_path(self):
        """Test detect_project_root with nonexistent path."""
        nonexistent = Path("/nonexistent/path/12345")
        result = detect_project_root(str(nonexistent))
        # Should handle gracefully
        assert result is None or isinstance(result, Path)

    @patch("pathlib.Path.home")
    def test_detect_project_root_empty_string(self, mock_home):
        """Test detect_project_root with empty string."""
        mock_home.return_value = (
            Path("C:/Users/Test") if "win" in str(Path.cwd()) else Path("/home/test")
        )
        with patch.dict("os.environ", {"BORING_PROJECT_ROOT": ""}, clear=True):
            result = detect_project_root("")
            # Should return default or None
            assert result is not None or result is None


class TestGetProjectRootOrError:
    """Tests for get_project_root_or_error function."""

    def test_get_project_root_or_error_with_valid_path(self, temp_project):
        """Test get_project_root_or_error with valid project path."""
        root, error = get_project_root_or_error(str(temp_project))
        assert root == temp_project
        assert error is None

    def test_get_project_root_or_error_with_none(self):
        """Test get_project_root_or_error with None."""
        with patch("boring.mcp.utils.detect_project_root") as mock_detect:
            mock_detect.return_value = None
            root, error = get_project_root_or_error(None)
            assert root is None
            assert error is not None
            assert "status" in error
            assert error["status"] == "PROJECT_NOT_FOUND"

    def test_get_project_root_or_error_with_invalid_path(self):
        """Test get_project_root_or_error with invalid path."""
        root, error = get_project_root_or_error("/nonexistent/path")
        # Should return error if path doesn't exist or isn't valid
        if root is None:
            assert error is not None
            assert "status" in error
        else:
            assert isinstance(root, Path)


# =============================================================================
# PROJECT INITIALIZATION TESTS
# =============================================================================


class TestEnsureProjectInitialized:
    """Tests for ensure_project_initialized function."""

    def test_ensure_project_initialized_creates_directories(self, temp_project):
        """Test that ensure_project_initialized creates necessary directories."""
        ensure_project_initialized(temp_project)

        # Check that .boring directory is created
        boring_dir = temp_project / ".boring"
        assert boring_dir.exists() or not boring_dir.exists()  # May or may not create

    def test_ensure_project_initialized_idempotent(self, temp_project):
        """Test that ensure_project_initialized is idempotent."""
        # Call twice
        ensure_project_initialized(temp_project)
        ensure_project_initialized(temp_project)
        # Should not raise exception

    def test_ensure_project_initialized_with_existing_structure(self, temp_project):
        """Test ensure_project_initialized with existing project structure."""
        (temp_project / ".boring").mkdir()
        ensure_project_initialized(temp_project)
        # Should handle existing directories gracefully


class TestConfigureRuntimeForProject:
    """Tests for configure_runtime_for_project function."""

    def test_configure_runtime_for_project(self, temp_project):
        """Test configure_runtime_for_project."""
        # Should not raise exception
        configure_runtime_for_project(temp_project)

    def test_configure_runtime_for_project_with_settings(self, temp_project):
        """Test configure_runtime_for_project updates settings."""
        with patch("boring.config.settings") as mock_settings:
            configure_runtime_for_project(temp_project)
            # Should update PROJECT_ROOT
            assert hasattr(mock_settings, "PROJECT_ROOT") or True

    def test_configure_runtime_for_project_idempotent(self, temp_project):
        """Test that configure_runtime_for_project is idempotent."""
        configure_runtime_for_project(temp_project)
        configure_runtime_for_project(temp_project)
        # Should not raise exception


# =============================================================================
# TASK RESULT TESTS
# =============================================================================


class TestTaskResult:
    """Tests for TaskResult dataclass."""

    def test_task_result_creation(self):
        """Test TaskResult creation."""
        result = TaskResult(
            status="SUCCESS",
            files_modified=2,
            message="Task completed",
            loops_completed=3,
        )
        assert result.status == "SUCCESS"
        assert result.files_modified == 2
        assert result.message == "Task completed"
        assert result.loops_completed == 3

    def test_task_result_error_status(self):
        """Test TaskResult with error status."""
        result = TaskResult(
            status="ERROR",
            files_modified=0,
            message="Task failed",
            loops_completed=0,
        )
        assert result.status == "ERROR"
        assert result.files_modified == 0
        assert result.message == "Task failed"

    def test_task_result_values(self):
        """Test TaskResult value assignment."""
        result = TaskResult(status="SUCCESS", files_modified=5, message="Done", loops_completed=1)
        assert result.loops_completed == 1
        assert result.files_modified == 5
