"""
Unit tests for boring.loop.legacy module.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boring.loop.legacy import AgentLoop


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "@prompt.md").write_text("# Prompt")
    (project / "@context.md").write_text("# Context")
    return project


@pytest.fixture
def mock_gemini_client():
    client = MagicMock()
    client.generate_with_retry = MagicMock(return_value=("Response", True))
    return client


class TestAgentLoop:
    """Tests for AgentLoop class."""

    def test_init_sdk_mode(self, temp_project, mock_gemini_client):
        """Test initialization in SDK mode."""
        with (
            patch("boring.loop.legacy.settings") as mock_settings,
            patch("boring.loop.legacy.init_directories"),
            patch("boring.loop.legacy.create_gemini_client", return_value=mock_gemini_client),
            patch("boring.loop.legacy.MemoryManager"),
            patch("boring.loop.legacy.CodeVerifier"),
            patch("boring.loop.legacy.ExtensionsManager"),
            patch("boring.loop.legacy.console"),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.CONTEXT_FILE = "@context.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            loop = AgentLoop(use_cli=False)

            assert loop.use_cli is False
            assert loop.gemini_client == mock_gemini_client
            assert loop.gemini_cli_cmd is None

    def test_init_cli_mode(self, temp_project):
        """Test initialization in CLI mode."""
        with (
            patch("boring.loop.legacy.settings") as mock_settings,
            patch("boring.loop.legacy.init_directories"),
            patch("shutil.which", return_value="/usr/bin/gemini"),
            patch("boring.loop.legacy.MemoryManager"),
            patch("boring.loop.legacy.CodeVerifier"),
            patch("boring.loop.legacy.ExtensionsManager"),
            patch("boring.loop.legacy.console"),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.CONTEXT_FILE = "@context.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            loop = AgentLoop(use_cli=True)

            assert loop.use_cli is True
            assert loop.gemini_cli_cmd == "/usr/bin/gemini"
            assert loop.gemini_client is None

    def test_init_cli_mode_not_found(self, temp_project):
        """Test initialization when CLI not found."""
        with (
            patch("boring.loop.legacy.settings") as mock_settings,
            patch("boring.loop.legacy.init_directories"),
            patch("shutil.which", return_value=None),
            patch("boring.loop.legacy.MemoryManager"),
            patch("boring.loop.legacy.CodeVerifier"),
            patch("boring.loop.legacy.ExtensionsManager"),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.CONTEXT_FILE = "@context.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            with pytest.raises(RuntimeError, match="Gemini CLI not found"):
                AgentLoop(use_cli=True)

    def test_init_sdk_mode_failed(self, temp_project):
        """Test initialization when SDK client creation fails."""
        with (
            patch("boring.loop.legacy.settings") as mock_settings,
            patch("boring.loop.legacy.init_directories"),
            patch("boring.loop.legacy.create_gemini_client", return_value=None),
            patch("boring.loop.legacy.MemoryManager"),
            patch("boring.loop.legacy.CodeVerifier"),
            patch("boring.loop.legacy.ExtensionsManager"),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.CONTEXT_FILE = "@context.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            with pytest.raises(RuntimeError, match="Failed to initialize"):
                AgentLoop(use_cli=False)

    def test_init_with_custom_files(self, temp_project, mock_gemini_client):
        """Test initialization with custom prompt and context files."""
        prompt_file = temp_project / "custom_prompt.md"
        context_file = temp_project / "custom_context.md"
        prompt_file.write_text("Custom prompt")
        context_file.write_text("Custom context")

        with (
            patch("boring.loop.legacy.settings") as mock_settings,
            patch("boring.loop.legacy.init_directories"),
            patch("boring.loop.legacy.create_gemini_client", return_value=mock_gemini_client),
            patch("boring.loop.legacy.MemoryManager"),
            patch("boring.loop.legacy.CodeVerifier"),
            patch("boring.loop.legacy.ExtensionsManager"),
            patch("boring.loop.legacy.console"),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.CONTEXT_FILE = "@context.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            loop = AgentLoop(prompt_file=prompt_file, context_file=context_file)

            assert loop.prompt_file == prompt_file
            assert loop.context_file == context_file

    def test_init_verbose_mode(self, temp_project, mock_gemini_client):
        """Test initialization with verbose mode."""
        with (
            patch("boring.loop.legacy.settings") as mock_settings,
            patch("boring.loop.legacy.init_directories"),
            patch("boring.loop.legacy.create_gemini_client", return_value=mock_gemini_client),
            patch("boring.loop.legacy.MemoryManager") as mock_memory,
            patch("boring.loop.legacy.CodeVerifier") as mock_verifier,
            patch("boring.loop.legacy.ExtensionsManager") as mock_ext,
            patch("boring.loop.legacy.console") as mock_console,
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.CONTEXT_FILE = "@context.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            mock_memory_instance = MagicMock()
            mock_memory_instance.memory_dir = temp_project / ".memory"
            mock_memory.return_value = mock_memory_instance

            mock_verifier_instance = MagicMock()
            mock_verifier_instance.has_ruff = True
            mock_verifier_instance.has_pytest = True
            mock_verifier.return_value = mock_verifier_instance

            mock_ext_instance = MagicMock()
            mock_ext_instance.create_extensions_report.return_value = "Extensions report"
            mock_ext.return_value = mock_ext_instance

            AgentLoop(verbose=True)

            # Should print verbose information
            assert mock_console.print.called

    def test_run_circuit_breaker_open(self, temp_project, mock_gemini_client):
        """Test run when circuit breaker is open."""
        with (
            patch("boring.loop.legacy.settings") as mock_settings,
            patch("boring.loop.legacy.init_directories"),
            patch("boring.loop.legacy.create_gemini_client", return_value=mock_gemini_client),
            patch("boring.loop.legacy.should_halt_execution", return_value=True),
            patch("boring.loop.legacy.log_status"),
            patch("boring.loop.legacy.console") as mock_console,
            patch("boring.loop.legacy.MemoryManager"),
            patch("boring.loop.legacy.CodeVerifier"),
            patch("boring.loop.legacy.ExtensionsManager"),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.CONTEXT_FILE = "@context.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            loop = AgentLoop()

            with patch("boring.interactive.enter_interactive_mode", return_value=False):
                loop.run()

            # Should print circuit breaker message
            assert any("Circuit Breaker" in str(call) for call in mock_console.print.call_args_list)

    def test_run_circuit_breaker_resume(self, temp_project, mock_gemini_client):
        """Test run when circuit breaker is open but user resumes."""
        with (
            patch("boring.loop.legacy.settings") as mock_settings,
            patch("boring.loop.legacy.init_directories"),
            patch("boring.loop.legacy.create_gemini_client", return_value=mock_gemini_client),
            patch("boring.loop.legacy.should_halt_execution", return_value=True),
            patch("boring.circuit.should_halt_execution", return_value=True),
            patch("boring.core.circuit.should_halt_execution", return_value=True),
            patch("boring.loop.legacy.record_loop_result"),
            patch("boring.loop.legacy.log_status"),
            patch("boring.loop.legacy.console") as mock_console,
            patch("boring.loop.legacy.MemoryManager"),
            patch("boring.loop.legacy.CodeVerifier"),
            patch("boring.loop.legacy.ExtensionsManager"),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.CONTEXT_FILE = "@context.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"
            mock_settings.MAX_LOOPS = 1

            loop = AgentLoop()

            with (
                patch("boring.interactive.enter_interactive_mode", return_value=True),
                patch("boring.loop.legacy.init_call_tracking"),
                patch("boring.loop.legacy.can_make_call", return_value=True),
                patch("boring.loop.legacy.increment_call_counter"),
            ):
                # Manually set the return value to avoid self-referential mock issues
                with patch.object(
                    loop, "_generate_step", return_value=(False, "Test content", Path("test.py"))
                ):
                    loop.run()

            # Should print resume message
            assert any("Resuming" in str(call) for call in mock_console.print.call_args_list)

    def test_generate_step_sdk(self, temp_project, mock_gemini_client):
        """Test _generate_step in SDK mode."""
        with (
            patch("boring.loop.legacy.settings") as mock_settings,
            patch("boring.loop.legacy.init_directories"),
            patch("boring.loop.legacy.create_gemini_client", return_value=mock_gemini_client),
            patch("boring.loop.legacy.MemoryManager"),
            patch("boring.loop.legacy.CodeVerifier"),
            patch("boring.loop.legacy.ExtensionsManager"),
            patch("boring.loop.legacy.console"),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.CONTEXT_FILE = "@context.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"
            mock_settings.TIMEOUT_MINUTES = 5

            loop = AgentLoop(use_cli=False)

            with (
                patch("boring.loop.legacy.time.strftime", return_value="2024-01-01_00-00-00"),
                patch("boring.loop.legacy.Live"),
                patch("boring.loop.legacy.Progress"),
            ):
                success, content, output_file = loop._generate_step(1)

                assert isinstance(success, bool)
                assert isinstance(content, str)
                assert isinstance(output_file, Path)

    def test_generate_step_cli(self, temp_project):
        """Test _generate_step in CLI mode."""
        with (
            patch("boring.loop.legacy.settings") as mock_settings,
            patch("boring.loop.legacy.init_directories"),
            patch("shutil.which", return_value="/usr/bin/gemini"),
            patch("boring.loop.legacy.MemoryManager"),
            patch("boring.loop.legacy.CodeVerifier"),
            patch("boring.loop.legacy.ExtensionsManager"),
            patch("boring.loop.legacy.console"),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.CONTEXT_FILE = "@context.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"
            mock_settings.TIMEOUT_MINUTES = 5
            mock_settings.TASK_FILE = "@fix_plan.md"

            loop = AgentLoop(use_cli=True)

            mock_adapter = MagicMock()
            mock_adapter.generate_with_tools.return_value = MagicMock(text="Response", success=True)

            with (
                patch("boring.loop.legacy.time.strftime", return_value="2024-01-01_00-00-00"),
                patch("boring.loop.legacy.Live"),
                patch("boring.loop.legacy.Progress"),
                patch("boring.cli_client.GeminiCLIAdapter", return_value=mock_adapter),
                patch("boring.context_selector.create_context_selector"),
            ):
                success, content, output_file = loop._generate_step(1)

                assert isinstance(success, bool)
                assert isinstance(content, str)

    def test_verify_project_syntax(self, temp_project, mock_gemini_client):
        """Test _verify_project_syntax method."""
        with (
            patch("boring.loop.legacy.settings") as mock_settings,
            patch("boring.loop.legacy.init_directories"),
            patch("boring.loop.legacy.create_gemini_client", return_value=mock_gemini_client),
            patch("boring.loop.legacy.MemoryManager"),
            patch("boring.loop.legacy.CodeVerifier"),
            patch("boring.loop.legacy.ExtensionsManager"),
            patch("boring.loop.legacy.console"),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.CONTEXT_FILE = "@context.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            loop = AgentLoop()
            loop._files_modified_this_loop = []

            # Test with no modified files
            result, error = loop._verify_project_syntax()
            assert result is True

            # Test with valid Python file
            test_file = temp_project / "test.py"
            test_file.write_text("def test(): pass\n")
            loop._files_modified_this_loop = ["test.py"]

            with patch("boring.loop.legacy.check_syntax", return_value=(True, "")):
                result, error = loop._verify_project_syntax()
                assert result is True

    def test_full_syntax_check(self, temp_project, mock_gemini_client):
        """Test _full_syntax_check method."""
        with (
            patch("boring.loop.legacy.settings") as mock_settings,
            patch("boring.loop.legacy.init_directories"),
            patch("boring.loop.legacy.create_gemini_client", return_value=mock_gemini_client),
            patch("boring.loop.legacy.MemoryManager"),
            patch("boring.loop.legacy.CodeVerifier"),
            patch("boring.loop.legacy.ExtensionsManager"),
            patch("boring.loop.legacy.console"),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.CONTEXT_FILE = "@context.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            loop = AgentLoop()

            # Create src directory with Python file
            src_dir = temp_project / "src"
            src_dir.mkdir()
            test_file = src_dir / "test.py"
            test_file.write_text("def test(): pass\n")

            with patch("boring.loop.legacy.check_syntax", return_value=(True, "")):
                result, error = loop._full_syntax_check()
                assert result is True

    def test_self_correct(self, temp_project, mock_gemini_client):
        """Test _self_correct method."""
        with (
            patch("boring.loop.legacy.settings") as mock_settings,
            patch("boring.loop.legacy.init_directories"),
            patch("boring.loop.legacy.create_gemini_client", return_value=mock_gemini_client),
            patch("boring.loop.legacy.MemoryManager"),
            patch("boring.loop.legacy.CodeVerifier"),
            patch("boring.loop.legacy.ExtensionsManager"),
            patch("boring.loop.legacy.console"),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.CONTEXT_FILE = "@context.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            loop = AgentLoop()

            with (
                patch("boring.loop.legacy.time.strftime", return_value="2024-01-01_00-00-00"),
                patch("boring.loop.legacy.process_gemini_output", return_value=1),
            ):
                loop._self_correct("Error message", 1)

                # Should attempt correction
                assert mock_gemini_client.generate_with_retry.called

    def test_create_format_feedback(self, temp_project, mock_gemini_client):
        """Test _create_format_feedback method."""
        with (
            patch("boring.loop.legacy.settings") as mock_settings,
            patch("boring.loop.legacy.init_directories"),
            patch("boring.loop.legacy.create_gemini_client", return_value=mock_gemini_client),
            patch("boring.loop.legacy.MemoryManager"),
            patch("boring.loop.legacy.CodeVerifier"),
            patch("boring.loop.legacy.ExtensionsManager"),
            patch("boring.loop.legacy.console"),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.CONTEXT_FILE = "@context.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            loop = AgentLoop()

            feedback = loop._create_format_feedback()

            assert "REQUIRED FORMAT" in feedback
            assert "<file path" in feedback

    def test_save_loop_summary(self, temp_project, mock_gemini_client):
        """Test _save_loop_summary method."""
        with (
            patch("boring.loop.legacy.settings") as mock_settings,
            patch("boring.loop.legacy.init_directories"),
            patch("boring.loop.legacy.create_gemini_client", return_value=mock_gemini_client),
            patch("boring.loop.legacy.MemoryManager"),
            patch("boring.loop.legacy.CodeVerifier"),
            patch("boring.loop.legacy.ExtensionsManager"),
            patch("boring.loop.legacy.console"),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.CONTEXT_FILE = "@context.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"

            loop = AgentLoop()

            with patch("boring.loop.legacy.time.strftime", return_value="2024-01-01 00:00:00"):
                loop._save_loop_summary(1, "SUCCESS", "Test message")

                summary_file = temp_project / ".last_loop_summary"
                assert summary_file.exists()
                content = summary_file.read_text()
                assert "Loop #1" in content
                assert "SUCCESS" in content

    def test_check_plan_completion(self, temp_project, mock_gemini_client):
        """Test _check_plan_completion method."""
        with (
            patch("boring.loop.legacy.settings") as mock_settings,
            patch("boring.loop.legacy.init_directories"),
            patch("boring.loop.legacy.create_gemini_client", return_value=mock_gemini_client),
            patch("boring.loop.legacy.MemoryManager"),
            patch("boring.loop.legacy.CodeVerifier"),
            patch("boring.loop.legacy.ExtensionsManager"),
            patch("boring.loop.legacy.console"),
        ):
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.LOG_DIR = temp_project / "logs"
            mock_settings.PROMPT_FILE = "@prompt.md"
            mock_settings.CONTEXT_FILE = "@context.md"
            mock_settings.DEFAULT_MODEL = "gemini-2.0-flash"
            mock_settings.TASK_FILE = "@fix_plan.md"

            loop = AgentLoop()

            # Test with all checked
            plan_file = temp_project / "@fix_plan.md"
            plan_file.write_text("- [x] Task 1\n- [x] Task 2")

            result = loop._check_plan_completion()
            assert result is True

            # Test with unchecked items
            plan_file.write_text("- [x] Task 1\n- [ ] Task 2")
            result = loop._check_plan_completion()
            assert result is False

            # Test with no file
            plan_file.unlink()
            result = loop._check_plan_completion()
            assert result is True  # No plan = allow exit
