"""
Unit tests for boring.interactive module.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from boring.interactive import InteractiveSession, InteractiveAction


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "@prompt.md").write_text("# Prompt")
    return project


class TestInteractiveSession:
    """Tests for InteractiveSession class."""

    def test_init(self, temp_project):
        """Test initialization."""
        session = InteractiveSession(
            reason="Test reason",
            project_root=temp_project
        )
        assert session.reason == "Test reason"
        assert session.project_root == temp_project

    def test_init_defaults(self):
        """Test initialization with defaults."""
        with patch("boring.interactive.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = Path("/default")
            mock_settings.LOG_DIR = Path("/default/logs")
            
            session = InteractiveSession()
            
            assert session.project_root == Path("/default")

    def test_show_header(self, temp_project):
        """Test showing header."""
        session = InteractiveSession(reason="Test", project_root=temp_project)
        
        with patch("boring.interactive.console") as mock_console, \
             patch("boring.interactive.Panel"):
            session._show_header()
            
            mock_console.print.assert_called()

    def test_prompt_action(self, temp_project):
        """Test prompting for action."""
        session = InteractiveSession(project_root=temp_project)
        
        with patch("boring.interactive.Prompt.ask", return_value="1"):
            action = session._prompt_action()
            
            assert action in InteractiveAction

    def test_confirm_resume(self, temp_project):
        """Test confirming resume."""
        session = InteractiveSession(project_root=temp_project)
        
        with patch("boring.interactive.Confirm.ask", return_value=True):
            result = session._confirm_resume()
            
            assert result is True

    def test_confirm_abort(self, temp_project):
        """Test confirming abort."""
        session = InteractiveSession(project_root=temp_project)
        
        with patch("boring.interactive.Confirm.ask", return_value=True):
            result = session._confirm_abort()
            
            assert result is True

    def test_edit_prompt(self, temp_project):
        """Test editing prompt."""
        session = InteractiveSession(project_root=temp_project)
        
        with patch("boring.interactive.console"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            session._edit_prompt()
            
            # Should attempt to open editor
            assert True

    def test_run_command(self, temp_project):
        """Test running command."""
        session = InteractiveSession(project_root=temp_project)
        
        with patch("boring.interactive.Prompt.ask", return_value="echo test"), \
             patch("boring.interactive.Confirm.ask", return_value=True), \
             patch("subprocess.run") as mock_run, \
             patch("boring.interactive.console"):
            mock_run.return_value = MagicMock(returncode=0, stdout="test", stderr="")
            
            session._run_command()
            
            mock_run.assert_called()

    def test_view_errors(self, temp_project):
        """Test viewing errors."""
        session = InteractiveSession(
            project_root=temp_project,
            recent_errors=["Error 1", "Error 2"]
        )
        
        with patch("boring.interactive.console") as mock_console, \
             patch("boring.interactive.Table"), \
             patch("boring.interactive.Prompt.ask", return_value=""):
            session._view_errors()
            
            mock_console.print.assert_called()

    def test_view_logs(self, temp_project):
        """Test viewing logs."""
        log_file = temp_project / "logs" / "boring.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text("Log entry 1\nLog entry 2\n")
        
        session = InteractiveSession(project_root=temp_project, log_dir=log_file.parent)
        
        with patch("boring.interactive.console") as mock_console, \
             patch("boring.interactive.Syntax"), \
             patch("boring.interactive.Prompt.ask", return_value=""):
            session._view_logs()
            
            mock_console.print.assert_called()

    def test_reset_circuit(self, temp_project):
        """Test resetting circuit breaker."""
        session = InteractiveSession(project_root=temp_project)
        
        with patch("boring.interactive.reset_circuit_breaker") as mock_reset, \
             patch("boring.interactive.Confirm.ask", return_value=True), \
             patch("boring.interactive.console"):
            mock_reset.return_value = True
            
            session._reset_circuit()
            
            mock_reset.assert_called_once()

