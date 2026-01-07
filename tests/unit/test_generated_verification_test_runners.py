# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.verification.test_runners module.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.verification.test_runners import (
    run_tests_go,
    run_tests_gradle,
    run_tests_maven,
    run_tests_node,
    run_tests_python,
    run_tests_rust,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "tests").mkdir()
    return project


@pytest.fixture
def mock_tool_manager():
    """Create a mock ToolManager."""
    manager = MagicMock()
    return manager


# =============================================================================
# PYTHON TEST RUNNER TESTS
# =============================================================================


class TestRunTestsPython:
    """Tests for run_tests_python function."""

    def test_run_tests_python_pytest_not_available(self, temp_project, mock_tool_manager):
        """Test run_tests_python when pytest is not available."""
        mock_tool_manager.is_available.return_value = False

        result = run_tests_python(temp_project, mock_tool_manager)
        assert result.passed is True
        assert "Skipped" in result.message

    def test_run_tests_python_no_tests(self, temp_project, mock_tool_manager):
        """Test run_tests_python when no tests directory exists."""
        mock_tool_manager.is_available.return_value = True
        (temp_project / "tests").rmdir()

        result = run_tests_python(temp_project, mock_tool_manager)
        assert result.passed is True
        assert "No tests found" in result.message

    @patch("subprocess.run")
    def test_run_tests_python_success(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_python with successful test run."""
        mock_tool_manager.is_available.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test output\n5 passed"
        mock_run.return_value = mock_result

        result = run_tests_python(temp_project, mock_tool_manager)
        assert result.passed is True
        assert "passed" in result.message.lower()

    @patch("subprocess.run")
    def test_run_tests_python_failure(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_python with failed tests."""
        mock_tool_manager.is_available.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "test failures"
        mock_run.return_value = mock_result

        result = run_tests_python(temp_project, mock_tool_manager)
        assert result.passed is False
        assert "failed" in result.message.lower()

    @patch("subprocess.run")
    def test_run_tests_python_exception(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_python with exception."""
        mock_tool_manager.is_available.return_value = True
        mock_run.side_effect = Exception("Test error")

        result = run_tests_python(temp_project, mock_tool_manager)
        assert result.passed is True
        assert "error" in result.message.lower()

    @patch("subprocess.run")
    def test_run_tests_python_custom_test_path(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_python with custom test path."""
        mock_tool_manager.is_available.return_value = True
        custom_path = temp_project / "custom_tests"
        custom_path.mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "passed"
        mock_run.return_value = mock_result

        result = run_tests_python(temp_project, mock_tool_manager, test_path=custom_path)
        assert result.passed is True


# =============================================================================
# NODE TEST RUNNER TESTS
# =============================================================================


class TestRunTestsNode:
    """Tests for run_tests_node function."""

    def test_run_tests_node_npm_not_available(self, temp_project, mock_tool_manager):
        """Test run_tests_node when npm is not available."""
        mock_tool_manager.is_available.return_value = False

        result = run_tests_node(temp_project, mock_tool_manager)
        assert result.passed is True
        assert "Skipped" in result.message

    @patch("subprocess.run")
    def test_run_tests_node_success(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_node with successful test run."""
        mock_tool_manager.is_available.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "tests passed"
        mock_run.return_value = mock_result

        result = run_tests_node(temp_project, mock_tool_manager)
        assert result.passed is True
        assert "OK" in result.message

    @patch("subprocess.run")
    def test_run_tests_node_failure(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_node with failed tests."""
        mock_tool_manager.is_available.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "test failures"
        mock_run.return_value = mock_result

        result = run_tests_node(temp_project, mock_tool_manager)
        assert result.passed is False

    @patch("subprocess.run")
    def test_run_tests_node_exception(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_node with exception."""
        mock_tool_manager.is_available.return_value = True
        mock_run.side_effect = Exception("npm error")

        result = run_tests_node(temp_project, mock_tool_manager)
        assert result.passed is True


# =============================================================================
# GO TEST RUNNER TESTS
# =============================================================================


class TestRunTestsGo:
    """Tests for run_tests_go function."""

    def test_run_tests_go_not_available(self, temp_project, mock_tool_manager):
        """Test run_tests_go when Go is not available."""
        mock_tool_manager.is_available.return_value = False

        result = run_tests_go(temp_project, mock_tool_manager)
        assert result.passed is True
        assert "Skipped" in result.message

    @patch("subprocess.run")
    def test_run_tests_go_success(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_go with successful test run."""
        mock_tool_manager.is_available.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_run.return_value = mock_result

        result = run_tests_go(temp_project, mock_tool_manager)
        assert result.passed is True

    @patch("subprocess.run")
    def test_run_tests_go_failure(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_go with failed tests."""
        mock_tool_manager.is_available.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "failures"
        mock_run.return_value = mock_result

        result = run_tests_go(temp_project, mock_tool_manager)
        assert result.passed is False

    @patch("subprocess.run")
    def test_run_tests_go_exception(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_go with exception."""
        mock_tool_manager.is_available.return_value = True
        mock_run.side_effect = Exception("go error")

        result = run_tests_go(temp_project, mock_tool_manager)
        assert result.passed is True


# =============================================================================
# RUST TEST RUNNER TESTS
# =============================================================================


class TestRunTestsRust:
    """Tests for run_tests_rust function."""

    def test_run_tests_rust_cargo_not_available(self, temp_project, mock_tool_manager):
        """Test run_tests_rust when cargo is not available."""
        mock_tool_manager.is_available.return_value = False

        result = run_tests_rust(temp_project, mock_tool_manager)
        assert result.passed is True
        assert "Skipped" in result.message

    @patch("subprocess.run")
    def test_run_tests_rust_success(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_rust with successful test run."""
        mock_tool_manager.is_available.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test result: ok"
        mock_run.return_value = mock_result

        result = run_tests_rust(temp_project, mock_tool_manager)
        assert result.passed is True

    @patch("subprocess.run")
    def test_run_tests_rust_failure(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_rust with failed tests."""
        mock_tool_manager.is_available.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "test failures"
        mock_run.return_value = mock_result

        result = run_tests_rust(temp_project, mock_tool_manager)
        assert result.passed is False

    @patch("subprocess.run")
    def test_run_tests_rust_exception(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_rust with exception."""
        mock_tool_manager.is_available.return_value = True
        mock_run.side_effect = Exception("cargo error")

        result = run_tests_rust(temp_project, mock_tool_manager)
        assert result.passed is True


# =============================================================================
# MAVEN TEST RUNNER TESTS
# =============================================================================


class TestRunTestsMaven:
    """Tests for run_tests_maven function."""

    def test_run_tests_maven_not_available(self, temp_project, mock_tool_manager):
        """Test run_tests_maven when Maven is not available."""
        mock_tool_manager.is_available.return_value = False

        result = run_tests_maven(temp_project, mock_tool_manager)
        assert result.passed is True
        assert "Skipped" in result.message

    @patch("subprocess.run")
    def test_run_tests_maven_success(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_maven with successful test run."""
        mock_tool_manager.is_available.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "BUILD SUCCESS"
        mock_run.return_value = mock_result

        result = run_tests_maven(temp_project, mock_tool_manager)
        assert result.passed is True

    @patch("subprocess.run")
    def test_run_tests_maven_failure(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_maven with failed tests."""
        mock_tool_manager.is_available.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "BUILD FAILURE"
        mock_run.return_value = mock_result

        result = run_tests_maven(temp_project, mock_tool_manager)
        assert result.passed is False

    @patch("subprocess.run")
    def test_run_tests_maven_exception(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_maven with exception."""
        mock_tool_manager.is_available.return_value = True
        mock_run.side_effect = Exception("mvn error")

        result = run_tests_maven(temp_project, mock_tool_manager)
        assert result.passed is True


# =============================================================================
# GRADLE TEST RUNNER TESTS
# =============================================================================


class TestRunTestsGradle:
    """Tests for run_tests_gradle function."""

    def test_run_tests_gradle_not_available(self, temp_project, mock_tool_manager):
        """Test run_tests_gradle when Gradle is not available."""
        mock_tool_manager.is_available.return_value = False

        result = run_tests_gradle(temp_project, mock_tool_manager)
        assert result.passed is True
        assert "Skipped" in result.message

    @patch("subprocess.run")
    def test_run_tests_gradle_success(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_gradle with successful test run."""
        mock_tool_manager.is_available.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "BUILD SUCCESSFUL"
        mock_run.return_value = mock_result

        result = run_tests_gradle(temp_project, mock_tool_manager)
        assert result.passed is True

    @patch("subprocess.run")
    def test_run_tests_gradle_failure(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_gradle with failed tests."""
        mock_tool_manager.is_available.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "BUILD FAILED"
        mock_run.return_value = mock_result

        result = run_tests_gradle(temp_project, mock_tool_manager)
        assert result.passed is False

    @patch("subprocess.run")
    def test_run_tests_gradle_exception(self, mock_run, temp_project, mock_tool_manager):
        """Test run_tests_gradle with exception."""
        mock_tool_manager.is_available.return_value = True
        mock_run.side_effect = Exception("gradle error")

        result = run_tests_gradle(temp_project, mock_tool_manager)
        assert result.passed is True
