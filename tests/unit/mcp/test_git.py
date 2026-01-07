from unittest.mock import MagicMock, patch

from boring.mcp.tools.git import boring_hooks_install, boring_hooks_status, boring_hooks_uninstall


class TestGitTools:
    @patch("boring.mcp.tools.git.get_project_root_or_error")
    @patch("boring.mcp.tools.git.configure_runtime_for_project")
    @patch("boring.mcp.tools.git.HooksManager")
    def test_boring_hooks_install_success(self, mock_hooks_cls, mock_configure, mock_get_root):
        """Test successful hook installation."""
        mock_get_root.return_value = (MagicMock(), None)

        mock_manager = MagicMock()

        # Mock status return (not installed yet)
        mock_manager.status.return_value = {
            "is_git_repo": True,
            "hooks": {
                "pre-commit": {"installed": False, "is_boring_hook": False},
                "pre-push": {"installed": False, "is_boring_hook": False},
            },
        }
        mock_manager.install_all.return_value = (True, "Installed")
        mock_hooks_cls.return_value = mock_manager

        res = boring_hooks_install()

        assert res["status"] == "SUCCESS"
        mock_manager.install_all.assert_called_once()

    @patch("boring.mcp.tools.git.get_project_root_or_error")
    @patch("boring.mcp.tools.git.configure_runtime_for_project")
    @patch("boring.mcp.tools.git.HooksManager")
    def test_boring_hooks_install_idempotent(self, mock_hooks_cls, mock_configure, mock_get_root):
        """Test idempotency of hook installation."""
        mock_get_root.return_value = (MagicMock(), None)

        mock_manager = MagicMock()
        mock_manager.status.return_value = {
            "is_git_repo": True,
            "hooks": {
                "pre-commit": {"installed": True, "is_boring_hook": True},
                "pre-push": {"installed": True, "is_boring_hook": True},
            },
        }
        mock_hooks_cls.return_value = mock_manager

        res = boring_hooks_install()

        assert res["status"] == "SKIPPED"
        mock_manager.install_all.assert_not_called()

    @patch("boring.mcp.tools.git.get_project_root_or_error")
    @patch("boring.mcp.tools.git.configure_runtime_for_project")
    @patch("boring.mcp.tools.git.HooksManager")
    def test_boring_hooks_uninstall(self, mock_hooks_cls, mock_configure, mock_get_root):
        """Test hook uninstallation."""
        mock_get_root.return_value = (MagicMock(), None)

        mock_manager = MagicMock()
        mock_manager.uninstall_all.return_value = (True, "Uninstalled")
        mock_hooks_cls.return_value = mock_manager

        res = boring_hooks_uninstall()

        assert res["status"] == "SUCCESS"
        mock_manager.uninstall_all.assert_called_once()

    @patch("boring.mcp.tools.git.get_project_root_or_error")
    @patch("boring.mcp.tools.git.configure_runtime_for_project")
    @patch("boring.mcp.tools.git.HooksManager")
    def test_boring_hooks_status(self, mock_hooks_cls, mock_configure, mock_get_root):
        """Test status check."""
        mock_get_root.return_value = (MagicMock(), None)

        mock_manager = MagicMock()
        mock_manager.status.return_value = {"foo": "bar"}
        mock_hooks_cls.return_value = mock_manager

        res = boring_hooks_status()

        assert res == {"foo": "bar"}
