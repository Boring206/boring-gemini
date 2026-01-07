"""
Unit tests for boring.loop.agent module.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.loop.agent import StatefulAgentLoop


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "@prompt.md").write_text("# Prompt")
    return project


class TestStatefulAgentLoop:
    """Tests for StatefulAgentLoop class."""

    def test_init(self, temp_project):
        """Test initialization."""
        with (
            patch("boring.loop.agent.settings") as mock_settings,
            patch("boring.loop.agent.init_directories"),
            patch("boring.loop.agent.create_gemini_client", return_value=MagicMock()),
            patch("boring.loop.agent.MemoryManager"),
            patch("boring.loop.agent.CodeVerifier"),
            patch("boring.loop.agent.ExtensionsManager"),
            patch("boring.loop.agent.create_storage", return_value=None),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            loop = StatefulAgentLoop()

            assert loop.context is not None
            assert loop._current_state is None

    def test_init_cli_mode(self, temp_project):
        """Test initialization in CLI mode."""
        with (
            patch("boring.loop.agent.settings") as mock_settings,
            patch("boring.loop.agent.init_directories"),
            patch("shutil.which", return_value="/usr/bin/gemini"),
            patch("boring.loop.agent.MemoryManager"),
            patch("boring.loop.agent.CodeVerifier"),
            patch("boring.loop.agent.ExtensionsManager"),
            patch("boring.loop.agent.create_storage", return_value=None),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            loop = StatefulAgentLoop(use_cli=True)

            assert loop.context.use_cli is True

    def test_init_cli_not_available(self, temp_project):
        """Test initialization when CLI not available."""
        with (
            patch("boring.loop.agent.settings") as mock_settings,
            patch("boring.loop.agent.init_directories"),
            patch("shutil.which", return_value=None),
            patch("boring.loop.agent.MemoryManager"),
            patch("boring.loop.agent.CodeVerifier"),
            patch("boring.loop.agent.ExtensionsManager"),
            patch("boring.loop.agent.create_storage", return_value=None),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            with pytest.raises(RuntimeError, match="Gemini CLI not found"):
                StatefulAgentLoop(use_cli=True)

    def test_init_sdk_failed(self, temp_project):
        """Test initialization when SDK client creation fails."""
        with (
            patch("boring.loop.agent.settings") as mock_settings,
            patch("boring.loop.agent.init_directories"),
            patch("boring.loop.agent.create_gemini_client", return_value=None),
            patch("boring.loop.agent.MemoryManager"),
            patch("boring.loop.agent.CodeVerifier"),
            patch("boring.loop.agent.ExtensionsManager"),
            patch("boring.loop.agent.create_storage", return_value=None),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            with pytest.raises(RuntimeError, match="Failed to initialize"):
                StatefulAgentLoop(use_cli=False)

    def test_init_subsystems(self, temp_project):
        """Test subsystem initialization."""
        with (
            patch("boring.loop.agent.settings") as mock_settings,
            patch("boring.loop.agent.init_directories"),
            patch("boring.loop.agent.create_gemini_client", return_value=MagicMock()),
            patch("boring.loop.agent.MemoryManager"),
            patch("boring.loop.agent.CodeVerifier"),
            patch("boring.loop.agent.ExtensionsManager"),
            patch("boring.loop.agent.create_storage", return_value=None),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            loop = StatefulAgentLoop()

            assert loop.context.memory is not None
            assert loop.context.verifier is not None
            assert loop.context.extensions is not None

    def test_init_storage_failure(self, temp_project):
        """Test initialization when storage creation fails."""
        with (
            patch("boring.loop.agent.settings") as mock_settings,
            patch("boring.loop.agent.init_directories"),
            patch("boring.loop.agent.create_gemini_client", return_value=MagicMock()),
            patch("boring.loop.agent.MemoryManager"),
            patch("boring.loop.agent.CodeVerifier"),
            patch("boring.loop.agent.ExtensionsManager"),
            patch("boring.loop.agent.create_storage", side_effect=Exception("Error")),
            patch("boring.loop.agent.log_status"),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            loop = StatefulAgentLoop()

            # Should continue despite storage failure
            assert loop.context is not None
