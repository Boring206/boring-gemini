import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

@pytest.fixture
def mock_mcp():
    """Mock the MCP instance to avoid actual server startup."""
    with patch("boring.mcp.instance.mcp") as mock:
        # Mock decorators
        mock.tool.return_value = lambda x: x
        mock.resource.return_value = lambda x: x
        yield mock

@pytest.fixture
def mock_project_root(tmp_path):
    """Create a temporary project root with necessary structure."""
    root = tmp_path / "test_project"
    root.mkdir()
    (root / "PROMPT.md").write_text("# Test Project")
    (root / ".agent" / "workflows").mkdir(parents=True)
    return root

@pytest.fixture
def mock_settings():
    """Mock global settings."""
    with patch("boring.config.settings") as mock:
        mock.LOG_DIR = Path("logs")
        mock.PROJECT_ROOT = Path(".")
        mock.DEFAULT_MODEL = "gemini-1.5-flash"
        yield mock
