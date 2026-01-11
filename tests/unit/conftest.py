from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def helpers():
    """Mock helpers used in tool registration."""

    def get_project_root_or_error(project_path=None):
        if project_path:
            return Path(project_path), None
        return Path("."), None

    return {
        "get_project_root_or_error": get_project_root_or_error,
        "run_in_thread": lambda func, *args, **kwargs: func(*args, **kwargs),
        "AsyncTaskRunner": MagicMock(),
    }


@pytest.fixture
def mock_mcp():
    """Mock the MCP instance."""
    mock = MagicMock()
    mock.tool = lambda description, **kwargs: lambda func: func
    mock.resource = lambda uri, **kwargs: lambda func: func
    return mock
