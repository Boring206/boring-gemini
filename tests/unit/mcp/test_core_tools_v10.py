# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for core_tools.py and speckit_tools.py.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.core_tools import register_core_tools


@pytest.fixture
def mcp_mock():
    mcp = MagicMock()

    # Mock the @mcp.tool decorator
    def tool_decorator(**kwargs):
        def wrapper(func):
            return func

        return wrapper

    mcp.tool = tool_decorator
    mcp.resource = tool_decorator
    return mcp


@pytest.fixture
def helpers_mock():
    return {
        "detect_project_root": MagicMock(return_value=Path("/tmp")),
        "get_project_root_or_error": MagicMock(return_value=(Path("/tmp"), None)),
        "configure_runtime": MagicMock(),
        "check_rate_limit": MagicMock(return_value=(True, None)),
        "check_project_root": MagicMock(return_value=True),
    }


def test_register_core_tools(mcp_mock, helpers_mock):
    tools = register_core_tools(mcp_mock, lambda x: x, helpers_mock)
    assert "boring_quickstart" in tools
    assert "boring_health_check" in tools
    assert "boring_status" in tools
    assert "boring_skills_browse" in tools


def test_boring_quickstart(mcp_mock, helpers_mock):
    tools = register_core_tools(mcp_mock, lambda x: x, helpers_mock)
    result = tools["boring_quickstart"]()
    assert result["welcome"] == "Welcome to Boring for Gemini!"
    assert result["project_detected"] is True


def test_boring_health_check(mcp_mock, helpers_mock):
    # Mock the health check directly in the module it's imported from
    with patch("boring.health.run_health_check") as mock_health:
        mock_report = MagicMock()
        mock_report.is_healthy = True
        mock_report.passed = 1
        mock_report.failed = 0
        mock_report.warnings = 0

        # Create a mock check that has a status with a value attribute
        mock_check = MagicMock()
        mock_check.name = "Test Check"
        mock_check.status.value = "passed"
        mock_check.message = "OK"
        mock_check.suggestion = "None"

        mock_report.checks = [mock_check]
        mock_health.return_value = mock_report

        tools = register_core_tools(mcp_mock, lambda x: x, helpers_mock)
        result = tools["boring_health_check"]()
        assert result["healthy"] is True
        assert len(result["checks"]) == 1
        assert result["checks"][0]["status"] == "passed"


def test_boring_status(mcp_mock, helpers_mock):
    # Mock the underlying module
    with patch("boring.intelligence.MemoryManager") as mock_memory:
        mock_memory.return_value.get_project_state.return_value = {
            "loop_count": 5,
            "files_modified": 2,
            "failed_loops": 0,
        }

        tools = register_core_tools(mcp_mock, lambda x: x, helpers_mock)
        result = tools["boring_status"]()
        assert result["status"] == "SUCCESS"
        assert result["loop_count"] == 5


def test_boring_skills_browse(mcp_mock, helpers_mock):
    # Mock the underlying module
    with patch("boring.skills_catalog.search_skills") as mock_search:
        skill = MagicMock()
        skill.name = "test-skill"
        skill.platform = "gemini"
        skill.repo_url = "http://test"
        skill.description_zh = "測試"
        skill.install_command = "pip install test"
        mock_search.return_value = [skill]

        tools = register_core_tools(mcp_mock, lambda x: x, helpers_mock)
        result = tools["boring_skills_browse"]("test")
        assert result["status"] == "SUCCESS"
        assert len(result["results"]) == 1
        assert result["results"][0]["name"] == "test-skill"
