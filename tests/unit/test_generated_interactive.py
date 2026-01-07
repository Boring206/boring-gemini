# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.interactive module.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from boring.interactive import (
    InteractiveAction,
    InteractiveSession,
    MainMenu,
    enter_interactive_mode,
    run_interactive_menu,
)

# =============================================================================
# ENUM TESTS
# =============================================================================


class TestInteractiveAction:
    """Tests for InteractiveAction enum."""

    def test_interactive_action_values(self):
        """Test InteractiveAction enum values."""
        assert InteractiveAction.RESUME.value == "resume"
        assert InteractiveAction.ABORT.value == "abort"
        assert InteractiveAction.EDIT_PROMPT.value == "edit_prompt"
        assert InteractiveAction.RUN_COMMAND.value == "run_command"
        assert InteractiveAction.VIEW_ERRORS.value == "view_errors"
        assert InteractiveAction.VIEW_LOGS.value == "view_logs"
        assert InteractiveAction.RESET_CIRCUIT.value == "reset_circuit"


# =============================================================================
# INTERACTIVE SESSION TESTS
# =============================================================================


class TestInteractiveSession:
    """Tests for InteractiveSession class."""

    def test_interactive_session_init(self, tmp_path):
        """Test InteractiveSession initialization."""
        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            mock_settings.LOG_DIR = tmp_path / "logs"
            session = InteractiveSession(reason="Test reason", project_root=tmp_path)
            assert session.reason == "Test reason"
            assert session.project_root == tmp_path
            assert session._running is True

    def test_interactive_session_init_defaults(self):
        """Test InteractiveSession with default values."""
        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = Path("/default")
            mock_settings.LOG_DIR = Path("/default/logs")
            session = InteractiveSession()
            assert session.reason == "Manual intervention requested"
            assert session.recent_errors == []

    def test_interactive_session_show_header(self, tmp_path):
        """Test InteractiveSession._show_header method."""
        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            mock_settings.LOG_DIR = tmp_path / "logs"
            session = InteractiveSession(project_root=tmp_path)

            with patch("boring.interactive.console.print"):
                session._show_header()
                # Should not raise exception

    def test_interactive_session_prompt_action(self, tmp_path):
        """Test InteractiveSession._prompt_action method."""
        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            mock_settings.LOG_DIR = tmp_path / "logs"
            session = InteractiveSession(project_root=tmp_path)

            with patch("boring.interactive.Prompt.ask", return_value="1"):
                action = session._prompt_action()
                assert isinstance(action, InteractiveAction)

    def test_interactive_session_confirm_resume(self, tmp_path):
        """Test InteractiveSession._confirm_resume method."""
        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            mock_settings.LOG_DIR = tmp_path / "logs"
            session = InteractiveSession(project_root=tmp_path)

            with patch("boring.interactive.Confirm.ask", return_value=True):
                result = session._confirm_resume()
                assert isinstance(result, bool)

    def test_interactive_session_confirm_abort(self, tmp_path):
        """Test InteractiveSession._confirm_abort method."""
        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            mock_settings.LOG_DIR = tmp_path / "logs"
            session = InteractiveSession(project_root=tmp_path)

            with patch("boring.interactive.Confirm.ask", return_value=True):
                result = session._confirm_abort()
                assert isinstance(result, bool)

    def test_interactive_session_edit_prompt(self, tmp_path):
        """Test InteractiveSession._edit_prompt method."""
        prompt_file = tmp_path / "PROMPT.md"
        prompt_file.write_text("# Original prompt")

        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            mock_settings.LOG_DIR = tmp_path / "logs"
            session = InteractiveSession(project_root=tmp_path)

            with patch("boring.interactive.console.print"):
                with patch("subprocess.run"):
                    session._edit_prompt()
                    # Should not raise exception

    def test_interactive_session_run_command(self, tmp_path):
        """Test InteractiveSession._run_command method."""
        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            mock_settings.LOG_DIR = tmp_path / "logs"
            session = InteractiveSession(project_root=tmp_path)

            with patch("boring.interactive.Prompt.ask", return_value="echo test"):
                with patch("boring.interactive.subprocess.run") as mock_run:
                    mock_result = MagicMock()
                    mock_result.returncode = 0
                    mock_result.stdout = "test"
                    mock_run.return_value = mock_result

                    with patch("boring.interactive.Confirm.ask", return_value=False):
                        session._run_command()
                    # Should not raise exception

    def test_interactive_session_view_errors(self, tmp_path):
        """Test InteractiveSession._view_errors method."""
        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            mock_settings.LOG_DIR = tmp_path / "logs"
            session = InteractiveSession(
                project_root=tmp_path,
                recent_errors=[{"error": "Test error"}],
            )

            with patch("boring.interactive.console.print"):
                session._view_errors()
                # Should not raise exception

    def test_interactive_session_view_logs(self, tmp_path):
        """Test InteractiveSession._view_logs method."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        log_file = log_dir / "boring.log"
        log_file.write_text("Log entry")

        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            mock_settings.LOG_DIR = log_dir
            session = InteractiveSession(project_root=tmp_path, log_dir=log_dir)

            with patch("boring.interactive.console.print"):
                session._view_logs()
                # Should not raise exception

    def test_interactive_session_reset_circuit(self, tmp_path):
        """Test InteractiveSession._reset_circuit method."""
        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            mock_settings.LOG_DIR = tmp_path / "logs"
            session = InteractiveSession(project_root=tmp_path)

            with patch("boring.interactive.reset_circuit_breaker"):
                with patch("boring.interactive.console.print"):
                    with patch("boring.interactive.Confirm.ask", return_value=True):
                        session._reset_circuit()
                    # Should not raise exception

    def test_interactive_session_run_resume(self, tmp_path):
        """Test InteractiveSession.run with RESUME action."""
        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            mock_settings.LOG_DIR = tmp_path / "logs"
            session = InteractiveSession(project_root=tmp_path)

            with patch.object(session, "_show_header"):
                with patch.object(session, "_prompt_action", return_value=InteractiveAction.RESUME):
                    with patch.object(session, "_confirm_resume", return_value=True):
                        action = session.run()
                        assert action == InteractiveAction.RESUME

    def test_interactive_session_run_abort(self, tmp_path):
        """Test InteractiveSession.run with ABORT action."""
        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            mock_settings.LOG_DIR = tmp_path / "logs"
            session = InteractiveSession(project_root=tmp_path)

            with patch.object(session, "_show_header"):
                with patch.object(session, "_prompt_action", return_value=InteractiveAction.ABORT):
                    with patch.object(session, "_confirm_abort", return_value=True):
                        action = session.run()
                        assert action == InteractiveAction.ABORT


# =============================================================================
# MAIN MENU TESTS
# =============================================================================


class TestMainMenu:
    """Tests for MainMenu class."""

    def test_main_menu_init(self, tmp_path):
        """Test MainMenu initialization."""
        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            menu = MainMenu(tmp_path)
            assert menu.project_root == tmp_path

    def test_main_menu_show(self, tmp_path):
        """Test MainMenu.show method."""
        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            menu = MainMenu(tmp_path)

            with patch.object(menu, "_display_menu"):
                with patch.object(menu, "_get_choice", return_value="q"):
                    menu.show()
                    # Should not raise exception


# =============================================================================
# MODULE FUNCTIONS TESTS
# =============================================================================


class TestEnterInteractiveMode:
    """Tests for enter_interactive_mode function."""

    def test_enter_interactive_mode(self, tmp_path):
        """Test enter_interactive_mode function."""
        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            mock_settings.LOG_DIR = tmp_path / "logs"

            with patch("boring.interactive.InteractiveSession") as mock_session:
                mock_instance = MagicMock()
                mock_instance.run.return_value = InteractiveAction.RESUME
                mock_session.return_value = mock_instance

                result = enter_interactive_mode(reason="Test", project_root=tmp_path)
                assert isinstance(result, bool)
                assert result is True


class TestRunInteractiveMenu:
    """Tests for run_interactive_menu function."""

    def test_run_interactive_menu(self):
        """Test run_interactive_menu function."""
        with patch("boring.interactive.MainMenu") as mock_menu:
            mock_instance = MagicMock()
            mock_menu.return_value = mock_instance

            run_interactive_menu()
            # Should not raise exception
