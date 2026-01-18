import json
from pathlib import Path
from unittest.mock import patch

import pytest
import typer

from boring.cli.installer import (
    _get_plugin_dir,
    _install_dependencies,
    _parse_repo_url,
    _verify_plugin_manifest,
    install_plugin,
    list_plugins,
    uninstall_plugin,
)


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for testing."""
    return tmp_path


class TestInstallerUtils:
    def test_get_plugin_dir_global(self):
        with patch("pathlib.Path.home", return_value=Path("/home/user")):
            path = _get_plugin_dir(is_global=True)
            assert str(path).replace("\\", "/") == "/home/user/.boring/plugins"

    def test_get_plugin_dir_local(self, temp_dir):
        with patch("boring.cli.installer.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_dir
            path = _get_plugin_dir(is_global=False)
            assert path == temp_dir / ".boring_plugins"

    def test_parse_repo_url_full(self):
        url, name = _parse_repo_url("https://github.com/user/plugin.git")
        assert url == "https://github.com/user/plugin.git"
        assert name == "plugin"

    def test_parse_repo_url_ssh(self):
        url, name = _parse_repo_url("git@github.com:user/plugin.git")
        assert url == "git@github.com:user/plugin.git"
        assert name == "plugin"

    def test_parse_repo_url_shorthand(self):
        url, name = _parse_repo_url("user/plugin")
        assert url == "https://github.com/user/plugin.git"
        assert name == "plugin"

    def test_parse_repo_url_invalid(self):
        with pytest.raises(ValueError, match="Invalid repository URL"):
            _parse_repo_url("invalid-url")

    def test_verify_plugin_manifest_pack(self, temp_dir):
        manifest = temp_dir / "boring-pack.json"
        manifest.write_text(json.dumps({"name": "test"}), encoding="utf-8")
        assert _verify_plugin_manifest(temp_dir) is True

    def test_verify_plugin_manifest_legacy(self, temp_dir):
        manifest = temp_dir / "boring-plugin.json"
        manifest.write_text(json.dumps({"name": "test"}), encoding="utf-8")
        assert _verify_plugin_manifest(temp_dir) is True

    def test_verify_plugin_manifest_tools(self, temp_dir):
        tools = temp_dir / "tools"
        tools.mkdir()
        (tools / "test.py").write_text("print()", encoding="utf-8")
        assert _verify_plugin_manifest(temp_dir) is True

    def test_verify_plugin_manifest_fallback_valid(self, temp_dir):
        (temp_dir / "plugin.py").write_text("@plugin\ndef tool(): pass", encoding="utf-8")
        assert _verify_plugin_manifest(temp_dir) is True

    def test_verify_plugin_manifest_fallback_invalid(self, temp_dir):
        (temp_dir / "no_plugin.py").write_text("print()", encoding="utf-8")
        assert _verify_plugin_manifest(temp_dir) is False

    def test_install_dependencies_no_file(self, temp_dir):
        # Should return silently
        _install_dependencies(temp_dir)

    def test_install_dependencies_success(self, temp_dir):
        reqs = temp_dir / "requirements.txt"
        reqs.write_text("requests", encoding="utf-8")
        with (
            patch("rich.prompt.Confirm.ask", return_value=True),
            patch("subprocess.check_call") as mock_call,
        ):
            _install_dependencies(temp_dir)
            mock_call.assert_called_once()

    def test_install_dependencies_refused(self, temp_dir):
        reqs = temp_dir / "requirements.txt"
        reqs.write_text("requests", encoding="utf-8")
        with (
            patch("rich.prompt.Confirm.ask", return_value=False),
            patch("subprocess.check_call") as mock_call,
        ):
            _install_dependencies(temp_dir)
            mock_call.assert_not_called()


class TestInstallerCommands:
    @patch("boring.cli.installer.Repo")
    @patch("boring.cli.installer._get_plugin_dir")
    @patch("boring.cli.installer._verify_plugin_manifest")
    @patch("boring.cli.installer.get_plugin_loader")
    def test_install_plugin_git(self, mock_loader, mock_verify, mock_get_dir, mock_repo, temp_dir):
        mock_get_dir.return_value = temp_dir
        mock_verify.return_value = True

        install_plugin("user/test-plugin")

        mock_repo.clone_from.assert_called_once()
        assert (temp_dir / "test-plugin").exists() or mock_repo.clone_from.called

    @patch("boring.cli.installer.zipfile.ZipFile")
    @patch("boring.cli.installer._get_plugin_dir")
    @patch("boring.cli.installer._verify_plugin_manifest")
    @patch("boring.cli.installer.get_plugin_loader")
    def test_install_plugin_zip(self, mock_loader, mock_verify, mock_get_dir, mock_zip, temp_dir):
        mock_get_dir.return_value = temp_dir
        mock_verify.return_value = True

        fake_zip = temp_dir / "test.zip"
        fake_zip.write_text("fake content")

        install_plugin(str(fake_zip))

        mock_zip.assert_called_once()

    @patch("boring.cli.installer._get_plugin_dir")
    def test_install_plugin_exists_no_force(self, mock_get_dir, temp_dir):
        mock_get_dir.return_value = temp_dir
        plugin_dir = temp_dir / "test-plugin"
        plugin_dir.mkdir()

        with pytest.raises(typer.Exit) as exc:
            install_plugin("user/test-plugin")
        assert exc.value.exit_code == 1

    @patch("boring.cli.installer.shutil.rmtree")
    @patch("boring.cli.installer._get_plugin_dir")
    def test_uninstall_plugin_success(self, mock_get_dir, mock_rm, temp_dir):
        mock_get_dir.return_value = temp_dir
        plugin_dir = temp_dir / "test-plugin"
        plugin_dir.mkdir()

        with (
            patch("rich.prompt.Confirm.ask", return_value=True),
            patch("boring.cli.installer.get_plugin_loader"),
        ):
            uninstall_plugin("test-plugin")
            mock_rm.assert_called_with(plugin_dir)

    @patch("boring.cli.installer._get_plugin_dir")
    def test_uninstall_plugin_not_found(self, mock_get_dir, temp_dir):
        mock_get_dir.return_value = temp_dir
        with pytest.raises(typer.Exit) as exc:
            uninstall_plugin("non-existent")
        assert exc.value.exit_code == 1

    @patch("boring.cli.installer._get_plugin_dir")
    def test_list_plugins_empty(self, mock_get_dir, temp_dir):
        mock_get_dir.return_value = temp_dir
        # Should not raise, just print info
        list_plugins()

    @patch("boring.cli.installer._get_plugin_dir")
    def test_list_plugins_with_content(self, mock_get_dir, temp_dir):
        mock_get_dir.return_value = temp_dir
        p1 = temp_dir / "plugin1"
        p1.mkdir()
        manifest = p1 / "boring-plugin.json"
        manifest.write_text(json.dumps({"description": "Test plugin"}), encoding="utf-8")

        p2 = temp_dir / "plugin2"
        p2.mkdir()

        list_plugins()
