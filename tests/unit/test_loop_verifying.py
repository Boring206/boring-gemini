"""
Unit tests for boring.loop.states.verifying module.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from boring.loop.states.verifying import VerifyingState
from boring.loop.context import LoopContext
from boring.loop.base import StateResult


@pytest.fixture
def mock_context(tmp_path):
    """Create a mock LoopContext."""
    context = MagicMock(spec=LoopContext)
    context.project_root = tmp_path
    context.log_dir = tmp_path / "logs"
    context.log_dir.mkdir(parents=True, exist_ok=True)
    context.verification_level = "STANDARD"
    context.loop_count = 1
    context.files_modified = ["file1.py"]
    context.files_created = ["file2.py"]
    context.tasks_completed = ["task1"]
    context.output_content = "Some output"
    context.errors_this_loop = []
    context.verification_passed = False
    context.verification_error = None
    context.should_exit = False
    context.memory = MagicMock()
    context.storage = MagicMock()
    return context


@pytest.fixture
def verifying_state():
    return VerifyingState()


class TestVerifyingState:
    """Tests for VerifyingState class."""

    def test_name(self, verifying_state):
        """Test state name."""
        assert verifying_state.name == "Verifying"

    def test_on_enter(self, verifying_state, mock_context):
        """Test state entry."""
        with patch("boring.loop.states.verifying.log_status") as mock_log, \
             patch("boring.loop.states.verifying.console") as mock_console:
            verifying_state.on_enter(mock_context)
            
            mock_context.start_state.assert_called_once()
            mock_log.assert_called()
            mock_console.print.assert_called()

    def test_handle_no_verifier(self, verifying_state, mock_context):
        """Test handling when no verifier is configured."""
        mock_context.verifier = None
        
        result = verifying_state.handle(mock_context)
        
        assert result == StateResult.SUCCESS
        assert mock_context.verification_passed is True

    def test_handle_verification_passes(self, verifying_state, mock_context):
        """Test handling when verification passes."""
        mock_verifier = MagicMock()
        mock_verifier.verify_project.return_value = (True, "")
        mock_context.verifier = mock_verifier
        
        with patch("boring.loop.states.verifying.log_status") as mock_log, \
             patch("boring.loop.states.verifying.console") as mock_console:
            result = verifying_state.handle(mock_context)
        
        assert result == StateResult.SUCCESS
        assert mock_context.verification_passed is True
        mock_log.assert_called()
        mock_console.print.assert_called()

    def test_handle_verification_fails(self, verifying_state, mock_context):
        """Test handling when verification fails."""
        mock_verifier = MagicMock()
        mock_verifier.verify_project.return_value = (False, "Syntax error")
        mock_context.verifier = mock_verifier
        
        with patch("boring.loop.states.verifying.log_status") as mock_log, \
             patch("boring.loop.states.verifying.console") as mock_console:
            result = verifying_state.handle(mock_context)
        
        assert result == StateResult.FAILURE
        assert mock_context.verification_passed is False
        assert "Syntax error" in mock_context.verification_error
        assert len(mock_context.errors_this_loop) > 0

    def test_handle_records_error_pattern(self, verifying_state, mock_context):
        """Test that error pattern is recorded to memory."""
        mock_verifier = MagicMock()
        mock_verifier.verify_project.return_value = (False, "Error message")
        mock_context.verifier = mock_verifier
        mock_context.memory = MagicMock()
        
        with patch("boring.loop.states.verifying.log_status"), \
             patch("boring.loop.states.verifying.console"):
            verifying_state.handle(mock_context)
        
        mock_context.memory.record_error_pattern.assert_called_once()

    def test_next_state_failure(self, verifying_state, mock_context):
        """Test next state when verification fails."""
        with patch("boring.loop.states.verifying.increment_call_counter"), \
             patch("boring.loop.states.verifying.record_loop_result"), \
             patch("boring.loop.states.recovery.RecoveryState") as mock_recovery:
            mock_recovery.return_value = MagicMock()
            
            next_state = verifying_state.next_state(mock_context, StateResult.FAILURE)
            
            assert next_state is not None
            mock_recovery.assert_called_once()

    def test_next_state_success_should_exit(self, verifying_state, mock_context):
        """Test next state when should exit."""
        mock_context.should_exit = True
        
        with patch("boring.loop.states.verifying.increment_call_counter"), \
             patch("boring.loop.states.verifying.record_loop_result"):
            next_state = verifying_state.next_state(mock_context, StateResult.SUCCESS)
            
            assert next_state is None

    def test_next_state_success_plan_complete(self, verifying_state, mock_context):
        """Test next state when plan is complete."""
        mock_context.should_exit = False
        def side_effect(reason):
            mock_context.should_exit = True
        mock_context.mark_exit.side_effect = side_effect
        
        with patch("boring.loop.states.verifying.increment_call_counter"), \
             patch("boring.loop.states.verifying.record_loop_result"), \
             patch.object(verifying_state, "_check_plan_complete", return_value=True), \
             patch("boring.loop.states.verifying.console") as mock_console:
            next_state = verifying_state.next_state(mock_context, StateResult.SUCCESS)
            
            assert next_state is None
            assert mock_context.should_exit is True
            mock_console.print.assert_called()

    def test_next_state_success_continue(self, verifying_state, mock_context):
        """Test next state when continuing loop."""
        mock_context.should_exit = False
        
        with patch("boring.loop.states.verifying.increment_call_counter"), \
             patch("boring.loop.states.verifying.record_loop_result"), \
             patch.object(verifying_state, "_check_plan_complete", return_value=False), \
             patch("boring.loop.states.verifying.log_status") as mock_log:
            next_state = verifying_state.next_state(mock_context, StateResult.SUCCESS)
            
            assert next_state is None  # Will trigger next iteration
            mock_log.assert_called()

    def test_record_success(self, verifying_state, mock_context):
        """Test recording successful loop to memory."""
        with patch("boring.loop.states.verifying.LoopMemory") as mock_loop_memory, \
             patch("boring.loop.states.verifying.log_status"):
            mock_context.get_loop_duration.return_value = 1.5
            
            verifying_state._record_success(mock_context)
            
            mock_context.memory.record_loop.assert_called_once()

    def test_record_success_no_memory(self, verifying_state, mock_context):
        """Test recording when no memory manager."""
        mock_context.memory = None
        
        # Should not raise exception
        verifying_state._record_success(mock_context)

    def test_record_success_exception(self, verifying_state, mock_context):
        """Test recording when exception occurs."""
        mock_context.memory.record_loop.side_effect = Exception("Error")
        
        with patch("boring.loop.states.verifying.log_status") as mock_log:
            verifying_state._record_success(mock_context)
            
            # Should log warning
            mock_log.assert_called()

    def test_check_plan_complete_no_file(self, verifying_state, mock_context):
        """Test checking plan when task file doesn't exist."""
        task_file = mock_context.project_root / "@fix_plan.md"
        if task_file.exists():
            task_file.unlink()
        
        result = verifying_state._check_plan_complete(mock_context)
        
        assert result is False

    def test_check_plan_complete_all_checked(self, verifying_state, mock_context):
        """Test checking plan when all items are checked."""
        task_file = mock_context.project_root / "@fix_plan.md"
        task_file.write_text("- [x] Task 1\n- [x] Task 2")
        
        result = verifying_state._check_plan_complete(mock_context)
        
        assert result is True

    def test_check_plan_complete_has_unchecked(self, verifying_state, mock_context):
        """Test checking plan when unchecked items exist."""
        task_file = mock_context.project_root / "@fix_plan.md"
        task_file.write_text("- [x] Task 1\n- [ ] Task 2")
        
        result = verifying_state._check_plan_complete(mock_context)
        
        assert result is False

    def test_check_plan_complete_exception(self, verifying_state, mock_context):
        """Test checking plan when exception occurs."""
        with patch("pathlib.Path.read_text", side_effect=Exception("Error")):
            result = verifying_state._check_plan_complete(mock_context)
            
            assert result is False

    def test_record_metrics(self, verifying_state, mock_context):
        """Test recording metrics to storage."""
        mock_context.get_state_duration.return_value = 0.5
        
        verifying_state._record_metrics(mock_context, StateResult.SUCCESS)
        
        mock_context.storage.record_metric.assert_called_once()
        call_args = mock_context.storage.record_metric.call_args
        assert call_args[1]["name"] == "state_verifying"
        assert call_args[1]["value"] == 0.5

    def test_record_metrics_no_storage(self, verifying_state, mock_context):
        """Test recording metrics when no storage."""
        mock_context.storage = None
        
        # Should not raise exception
        verifying_state._record_metrics(mock_context, StateResult.SUCCESS)

    def test_record_metrics_exception(self, verifying_state, mock_context):
        """Test recording metrics when exception occurs."""
        mock_context.storage.record_metric.side_effect = Exception("Error")
        
        # Should not raise exception
        verifying_state._record_metrics(mock_context, StateResult.SUCCESS)

