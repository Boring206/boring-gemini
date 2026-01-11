
import json
from unittest.mock import patch

import pytest

from boring.cli.wizard import WizardManager


class TestWizardManager:

    @pytest.fixture
    def mock_platform(self):
        with patch("platform.system") as mock:
            yield mock

    @pytest.fixture
    def mock_env(self, tmp_path):
        with patch.dict("os.environ", {"APPDATA": str(tmp_path / "AppData")}):
            yield


    def test_path_detection_linux(self, mock_platform, tmp_path):
        mock_platform.return_value = "Linux"

        home = tmp_path / "home" / "user"
        config = home / ".config"

        # Setup env
        with patch.dict("os.environ", {"XDG_CONFIG_HOME": str(config)}), \
             patch("pathlib.Path.home", return_value=home):

            # Setup paths
            claude = config / "Claude" / "claude_desktop_config.json"
            claude.parent.mkdir(parents=True, exist_ok=True)

            manager = WizardManager()
            assert manager.editors["Claude Desktop"] == claude


    def test_install_with_profile(self, tmp_path):
        manager = WizardManager()
        target_file = tmp_path / "config.json"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text("{}", encoding="utf-8")

        with patch("rich.console.Console.print"), patch("sys.executable", "fake_python"):
            manager.install("Test Editor", target_file, profile="Lite")

        data = json.loads(target_file.read_text())
        assert data["mcpServers"]["boring-boring"]["env"]["BORING_MCP_PROFILE"] == "lite"

    def test_install_with_custom_env(self, tmp_path):
        manager = WizardManager()
        target_file = tmp_path / "config.json"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text("{}", encoding="utf-8")

        extra = {"BORING_LOG_LEVEL": "DEBUG", "BORING_EXPERIMENTAL_VIBE": "true"}

        with patch("rich.console.Console.print"), patch("sys.executable", "fake_python"):
            manager.install("Test Editor", target_file, profile="Full", extra_env=extra)

        data = json.loads(target_file.read_text())
        env = data["mcpServers"]["boring-boring"]["env"]
        assert env["BORING_MCP_PROFILE"] == "full"
        assert env["BORING_LOG_LEVEL"] == "DEBUG"
        assert env["BORING_EXPERIMENTAL_VIBE"] == "true"

    def test_install_update_existing(self, tmp_path):
        manager = WizardManager()
        target_file = tmp_path / "config.json"
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Pre-existing
        initial = {
            "mcpServers": {
                "boring-boring": {"command": "old", "args": []}
            }
        }
        target_file.write_text(json.dumps(initial), encoding="utf-8")

        # Patch Confirm to say YES
        with patch("rich.prompt.Confirm.ask", return_value=True), \
             patch("sys.executable", "new_python"), \
             patch("rich.console.Console.print"):
            manager.install("Test Editor", target_file)

        data = json.loads(target_file.read_text())
        assert data["mcpServers"]["boring-boring"]["command"] == "new_python"

