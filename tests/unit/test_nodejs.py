import os
from unittest.mock import MagicMock, patch

import pytest

from boring.services.nodejs import NodeManager


@pytest.fixture
def mock_node_manager(tmp_path):
    """Fixture for NodeManager with a temporary directory."""
    with patch("boring.config.settings.PROJECT_ROOT", tmp_path):
        nm = NodeManager(project_root=tmp_path)
        # Mock home to avoid personal file access
        nm.node_dir = tmp_path / ".boring" / "node"
        if os.name == "nt":
            nm.node_exe = nm.node_dir / "node.exe"
            nm.npm_exe = nm.node_dir / "npm.cmd"
        else:
            nm.node_bin_dir = nm.node_dir / "bin"
            nm.node_exe = nm.node_bin_dir / "node"
            nm.npm_exe = nm.node_bin_dir / "npm"
        return nm


def test_node_manager_system_priority(mock_node_manager):
    """Test that system node is prioritized."""
    with patch("shutil.which", return_value="/usr/bin/node"):
        assert mock_node_manager.get_node_path() == "/usr/bin/node"


def test_node_manager_portable_fallback(mock_node_manager):
    """Test that portable node is used if system node is missing."""
    with patch("shutil.which", return_value=None):
        # Create dummy portable node
        mock_node_manager.node_exe.parent.mkdir(parents=True, exist_ok=True)
        mock_node_manager.node_exe.touch()

        path = mock_node_manager.get_node_path()
        assert path == str(mock_node_manager.node_exe)


def test_node_manager_not_found(mock_node_manager):
    """Test when no node is found."""
    with patch("shutil.which", return_value=None):
        assert mock_node_manager.get_node_path() is None
        assert mock_node_manager.is_node_available() is False


def test_node_manager_gemini_path_resolution(mock_node_manager):
    """Test gemini CLI path resolution."""
    # 1. System gemini
    with patch("shutil.which", return_value="/usr/local/bin/gemini"):
        assert mock_node_manager.get_gemini_path() == "/usr/local/bin/gemini"

    # 2. Portable gemini
    with patch("shutil.which", return_value=None):
        if os.name == "nt":
            gemini_path = mock_node_manager.node_dir / "gemini.cmd"
        else:
            gemini_path = mock_node_manager.node_bin_dir / "gemini"

        gemini_path.parent.mkdir(parents=True, exist_ok=True)
        gemini_path.touch()

        assert mock_node_manager.get_gemini_path() == str(gemini_path)


@patch("requests.get")
def test_download_node_mock(mock_get, mock_node_manager):
    """Test download_node logic with mocks."""
    # Mock response
    mock_response = MagicMock()
    mock_response.headers = {"content-length": "100"}
    mock_response.iter_content.return_value = [b"data"]
    mock_get.return_value = mock_response

    # Mock extraction based on OS
    with (
        patch("zipfile.ZipFile"),
        patch("tarfile.open"),
        patch.object(NodeManager, "_reorganize_node_dir"),
        patch("pathlib.Path.unlink"),
    ):
        assert mock_node_manager.download_node() is True
        mock_get.assert_called_once()
