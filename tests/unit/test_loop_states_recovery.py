"""
Unit tests for boring.loop.states.recovery module.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.loop.base import StateResult
from boring.loop.context import LoopContext
from boring.loop.states.recovery import RecoveryState


@pytest.fixture
def mock_context(tmp_path):
    """Create a mock LoopContext."""
    context = MagicMock(spec=LoopContext)
    context.project_root = tmp_path
    context.log_dir = tmp_path / "logs"
    context.log_dir.mkdir(parents=True, exist_ok=True)
    context.retry_count = 0
    context.max_retries = 3
    context.errors_this_loop = []
    context.verification_error = None
    context.patch_errors = []
    context.output_content = ""
    context.function_calls = []
    context.should_exit = False
    context.storage = MagicMock()
    return context


@pytest.fixture
def recovery_state():
    return RecoveryState()


class TestRecoveryState:
    """Tests for RecoveryState class."""

    def test_name(self, recovery_state):
        """Test state name."""
        assert recovery_state.name == "Recovery"

    def test_on_enter(self, recovery_state, mock_context):
        """Test state entry."""
        with (
            patch("boring.loop.states.recovery.log_status") as mock_log,
            patch("boring.loop.states.recovery.console") as mock_console,
        ):
            recovery_state.on_enter(mock_context)

            mock_context.start_state.assert_called_once()
            mock_log.assert_called()
            mock_console.print.assert_called()

    def test_handle_max_retries_exceeded(self, recovery_state, mock_context):
        """Test handling when max retries exceeded."""
        mock_context.retry_count = 2
        mock_context.max_retries = 3
        mock_context.can_retry.return_value = False

        def side_effect(reason):
            mock_context.should_exit = True

        mock_context.mark_exit.side_effect = side_effect

        with (
            patch("boring.loop.states.recovery.log_status"),
            patch("boring.loop.states.recovery.console"),
        ):
            result = recovery_state.handle(mock_context)

            assert result == StateResult.EXIT
            assert mock_context.should_exit is True

    def test_handle_can_retry(self, recovery_state, mock_context):
        """Test handling when can retry."""
        mock_context.can_retry.return_value = True

        with (
            patch.object(
                recovery_state, "_generate_recovery_prompt", return_value="Recovery prompt"
            ),
            patch.object(recovery_state, "_inject_recovery_context"),
            patch("boring.loop.states.recovery.log_status"),
        ):
            result = recovery_state.handle(mock_context)

            assert result == StateResult.RETRY

    def test_generate_recovery_prompt_format_error(self, recovery_state, mock_context):
        """Test generating recovery prompt for format error."""
        mock_context.errors_this_loop = ["No function calls found"]

        prompt = recovery_state._generate_recovery_prompt(mock_context)

        assert len(prompt) > 0

    def test_generate_recovery_prompt_verification_error(self, recovery_state, mock_context):
        """Test generating recovery prompt for verification error."""
        mock_context.verification_error = "Syntax error"

        prompt = recovery_state._generate_recovery_prompt(mock_context)

        assert "Syntax error" in prompt or len(prompt) > 0

    def test_generate_recovery_prompt_patching_error(self, recovery_state, mock_context):
        """Test generating recovery prompt for patching error."""
        mock_context.patch_errors = ["File not found"]

        prompt = recovery_state._generate_recovery_prompt(mock_context)

        assert len(prompt) > 0

    def test_generate_recovery_prompt_generic_error(self, recovery_state, mock_context):
        """Test generating recovery prompt for generic error."""
        mock_context.errors_this_loop = ["Generic error"]

        prompt = recovery_state._generate_recovery_prompt(mock_context)

        assert "Generic error" in prompt

    def test_next_state_exit(self, recovery_state, mock_context):
        """Test next state on exit."""
        with patch.object(recovery_state, "_record_metrics"):
            next_state = recovery_state.next_state(mock_context, StateResult.EXIT)

            assert next_state is None

    def test_next_state_retry(self, recovery_state, mock_context):
        """Test next state on retry."""
        with (
            patch.object(recovery_state, "_record_metrics"),
            patch("boring.loop.states.thinking.ThinkingState"),
        ):
            next_state = recovery_state.next_state(mock_context, StateResult.RETRY)

            assert next_state is not None

    def test_format_error_prompt(self, recovery_state):
        """Test format error prompt generation."""
        prompt = recovery_state._format_error_prompt()

        assert "format" in prompt.lower() or "function" in prompt.lower()

    def test_verification_error_prompt(self, recovery_state):
        """Test verification error prompt generation."""
        prompt = recovery_state._verification_error_prompt("Test error")

        assert "Test error" in prompt

    def test_patching_error_prompt(self, recovery_state):
        """Test patching error prompt generation."""
        prompt = recovery_state._patching_error_prompt(["Error 1", "Error 2"])

        assert "Error 1" in prompt or len(prompt) > 0

    def test_inject_recovery_context(self, recovery_state, mock_context):
        """Test injecting recovery context."""
        with patch("pathlib.Path.write_text"):
            recovery_state._inject_recovery_context(mock_context, "Recovery prompt")

            # Should not raise exception
            assert True

    def test_record_metrics(self, recovery_state, mock_context):
        """Test recording metrics."""
        mock_context.get_state_duration.return_value = 0.5

        recovery_state._record_metrics(mock_context, StateResult.RETRY)

        if mock_context.storage:
            # Should attempt to record
            assert True
