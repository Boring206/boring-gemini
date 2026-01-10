"""
Comprehensive tests for verification.test_runners module.
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from boring.models import VerificationResult
from boring.verification.test_runners import (
    run_tests_go,
    run_tests_node,
    run_tests_python,
    run_tests_rust,
)
from boring.verification.tools import ToolManager


@pytest.fixture
def mock_tools():
    """Create mock ToolManager."""
    tools = MagicMock(spec=ToolManager)
    tools.is_available.return_value = True
    return tools


@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project directory."""
    return tmp_path


class TestRunTestsPython:
    """Test Python test runner."""

    def test_pytest_not_available(self, temp_project):
        """Test when pytest is not available."""
        tools = MagicMock(spec=ToolManager)
        tools.is_available.return_value = False

        result = run_tests_python(temp_project, tools)

        assert result.passed is True
        assert "Skipped" in result.message
        assert "pytest not found" in result.message

    def test_no_tests_directory(self, temp_project, mock_tools):
        """Test when tests directory doesn't exist."""
        result = run_tests_python(temp_project, mock_tools)

        assert result.passed is True
        assert "No tests found" in result.message

    def test_tests_pass(self, temp_project, mock_tools):
        """Test when pytest tests pass."""
        # Create tests directory
        tests_dir = temp_project / "tests"
        tests_dir.mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "10 passed in 0.5s\n"

        with patch("subprocess.run", return_value=mock_result):
            result = run_tests_python(temp_project, mock_tools)

            assert result.passed is True
            assert "passed" in result.message.lower()

    def test_tests_fail(self, temp_project, mock_tools):
        """Test when pytest tests fail."""
        tests_dir = temp_project / "tests"
        tests_dir.mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "FAILED test.py::test_something\n5 failed, 10 passed"

        with patch("subprocess.run", return_value=mock_result):
            result = run_tests_python(temp_project, mock_tools)

            assert result.passed is False
            assert "failed" in result.message.lower()
            assert len(result.details) > 0
            assert "Fix tests" in result.suggestions

    def test_custom_test_path(self, temp_project, mock_tools):
        """Test with custom test path."""
        custom_tests = temp_project / "custom_tests"
        custom_tests.mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "All tests passed"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = run_tests_python(temp_project, mock_tools, custom_tests)

            assert result.passed is True
            # Verify custom path was used
            call_args = mock_run.call_args[0][0]
            assert str(custom_tests) in call_args

    def test_subprocess_timeout(self, temp_project, mock_tools):
        """Test handling of subprocess timeout."""
        tests_dir = temp_project / "tests"
        tests_dir.mkdir()

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pytest", 120)):
            result = run_tests_python(temp_project, mock_tools)

            assert result.passed is True  # Errors default to passed
            assert "error" in result.message.lower()

    def test_subprocess_exception(self, temp_project, mock_tools):
        """Test handling of subprocess exceptions."""
        tests_dir = temp_project / "tests"
        tests_dir.mkdir()

        with patch("subprocess.run", side_effect=Exception("Test error")):
            result = run_tests_python(temp_project, mock_tools)

            assert result.passed is True
            assert "error" in result.message.lower()


class TestRunTestsNode:
    """Test Node.js test runner."""

    def test_npm_not_available(self, temp_project):
        """Test when npm is not available."""
        tools = MagicMock(spec=ToolManager)
        tools.is_available.return_value = False

        result = run_tests_node(temp_project, tools)

        assert result.passed is True
        assert "npm not found" in result.message

    def test_npm_test_passes(self, temp_project, mock_tools):
        """Test when npm test passes."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "All tests passed"

        with patch("subprocess.run", return_value=mock_result):
            result = run_tests_node(temp_project, mock_tools)

            assert result.passed is True
            assert "OK" in result.message

    def test_npm_test_fails(self, temp_project, mock_tools):
        """Test when npm test fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Test suite failed\n5 tests failed"

        with patch("subprocess.run", return_value=mock_result):
            result = run_tests_node(temp_project, mock_tools)

            assert result.passed is False
            assert "failed" in result.message.lower()
            assert len(result.details) > 0

    def test_npm_test_exception(self, temp_project, mock_tools):
        """Test handling of npm test exceptions."""
        with patch("subprocess.run", side_effect=Exception("NPM error")):
            result = run_tests_node(temp_project, mock_tools)

            assert result.passed is True
            assert "error" in result.message.lower()


class TestRunTestsGo:
    """Test Go test runner."""

    def test_go_not_available(self, temp_project):
        """Test when Go is not available."""
        tools = MagicMock(spec=ToolManager)
        tools.is_available.return_value = False

        result = run_tests_go(temp_project, tools)

        assert result.passed is True
        assert "Go not found" in result.message

    def test_go_test_passes(self, temp_project, mock_tools):
        """Test when go test passes."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok\t./... 0.5s"

        with patch("subprocess.run", return_value=mock_result):
            result = run_tests_go(temp_project, mock_tools)

            assert result.passed is True
            assert "OK" in result.message

    def test_go_test_fails(self, temp_project, mock_tools):
        """Test when go test fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "FAIL\t./pkg 0.1s"

        with patch("subprocess.run", return_value=mock_result):
            result = run_tests_go(temp_project, mock_tools)

            assert result.passed is False
            assert "failed" in result.message.lower()

    def test_go_test_exception(self, temp_project, mock_tools):
        """Test handling of go test exceptions."""
        with patch("subprocess.run", side_effect=Exception("Go error")):
            result = run_tests_go(temp_project, mock_tools)

            assert result.passed is True
            assert "error" in result.message.lower()


class TestRunTestsRust:
    """Test Rust test runner."""

    def test_cargo_not_available(self, temp_project):
        """Test when cargo is not available."""
        tools = MagicMock(spec=ToolManager)
        tools.is_available.return_value = False

        result = run_tests_rust(temp_project, tools)

        assert result.passed is True
        assert "cargo not found" in result.message

    def test_cargo_test_passes(self, temp_project, mock_tools):
        """Test when cargo test passes."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test result: ok. 10 passed"

        with patch("subprocess.run", return_value=mock_result):
            result = run_tests_rust(temp_project, mock_tools)

            assert result.passed is True
            assert "OK" in result.message

    def test_cargo_test_fails(self, temp_project, mock_tools):
        """Test when cargo test fails."""
        mock_result = MagicMock()
        mock_result.returncode = 101
        mock_result.stdout = "test result: FAILED. 5 passed; 2 failed"

        with patch("subprocess.run", return_value=mock_result):
            result = run_tests_rust(temp_project, mock_tools)

            assert result.passed is False
            assert "failed" in result.message.lower()

    def test_cargo_test_exception(self, temp_project, mock_tools):
        """Test handling of cargo test exceptions."""
        with patch("subprocess.run", side_effect=Exception("Cargo error")):
            result = run_tests_rust(temp_project, mock_tools)

            assert result.passed is True
            assert "error" in result.message.lower()


class TestTestRunnersIntegration:
    """Integration tests for test runners."""

    def test_all_runners_have_consistent_interface(self, temp_project, mock_tools):
        """Test that all runners follow the same interface."""
        runners = [
            run_tests_python,
            run_tests_node,
            run_tests_go,
            run_tests_rust,
        ]

        for runner in runners:
            # Should accept project_root, tools, and optional test_path
            result = runner(temp_project, mock_tools, None)

            # Should return VerificationResult
            assert isinstance(result, VerificationResult)
            assert hasattr(result, "passed")
            assert hasattr(result, "check_type")
            assert hasattr(result, "message")
            assert result.check_type == "test"

    def test_graceful_degradation(self, temp_project):
        """Test that all runners gracefully handle tool unavailability."""
        tools = MagicMock(spec=ToolManager)
        tools.is_available.return_value = False

        runners = [
            run_tests_python,
            run_tests_node,
            run_tests_go,
            run_tests_rust,
        ]

        for runner in runners:
            result = runner(temp_project, tools)

            # Should not raise exception
            assert result.passed is True
            assert "Skipped" in result.message or "not found" in result.message
