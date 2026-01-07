# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.models module.
"""

from datetime import datetime

from boring.models import (
    CircuitBreakerHistoryEntry,
    CircuitBreakerState,
    CircuitBreakerStateEnum,
    ExitSignals,
    LoopInfo,
    LoopStatus,
    VerificationResult,
    Workflow,
    WorkflowStep,
)

# =============================================================================
# ENUM TESTS
# =============================================================================


class TestCircuitBreakerStateEnum:
    """Tests for CircuitBreakerStateEnum."""

    def test_circuit_breaker_state_enum_values(self):
        """Test enum values."""
        assert CircuitBreakerStateEnum.CLOSED == "CLOSED"
        assert CircuitBreakerStateEnum.OPEN == "OPEN"
        assert CircuitBreakerStateEnum.HALF_OPEN == "HALF_OPEN"


# =============================================================================
# LOOP INFO TESTS
# =============================================================================


class TestLoopInfo:
    """Tests for LoopInfo model."""

    def test_loop_info_defaults(self):
        """Test LoopInfo with default values."""
        info = LoopInfo()
        assert info.loop == 0
        assert info.files_changed == 0
        assert info.has_errors is False
        assert info.output_length == 0

    def test_loop_info_custom_values(self):
        """Test LoopInfo with custom values."""
        info = LoopInfo(loop=5, files_changed=3, has_errors=True, output_length=100)
        assert info.loop == 5
        assert info.files_changed == 3
        assert info.has_errors is True
        assert info.output_length == 100


# =============================================================================
# CIRCUIT BREAKER STATE TESTS
# =============================================================================


class TestCircuitBreakerState:
    """Tests for CircuitBreakerState model."""

    def test_circuit_breaker_state_defaults(self):
        """Test CircuitBreakerState with default values."""
        state = CircuitBreakerState()
        assert state.state == CircuitBreakerStateEnum.CLOSED
        assert state.failures == 0
        assert state.last_failure_time == 0
        assert isinstance(state.last_loop_info, LoopInfo)

    def test_circuit_breaker_state_custom(self):
        """Test CircuitBreakerState with custom values."""
        state = CircuitBreakerState(
            state=CircuitBreakerStateEnum.OPEN,
            failures=5,
            last_failure_time=1234567890,
        )
        assert state.state == CircuitBreakerStateEnum.OPEN
        assert state.failures == 5
        assert state.last_failure_time == 1234567890


# =============================================================================
# EXIT SIGNALS TESTS
# =============================================================================


class TestExitSignals:
    """Tests for ExitSignals model."""

    def test_exit_signals_defaults(self):
        """Test ExitSignals with default values."""
        signals = ExitSignals()
        assert signals.test_only_loops == []
        assert signals.done_signals == []
        assert signals.completion_indicators == []

    def test_exit_signals_custom(self):
        """Test ExitSignals with custom values."""
        signals = ExitSignals(
            test_only_loops=[1, 2],
            done_signals=[3],
            completion_indicators=["Done", "Complete"],
        )
        assert len(signals.test_only_loops) == 2
        assert len(signals.done_signals) == 1
        assert len(signals.completion_indicators) == 2


# =============================================================================
# LOOP STATUS TESTS
# =============================================================================


class TestLoopStatus:
    """Tests for LoopStatus model."""

    def test_loop_status_defaults(self):
        """Test LoopStatus with default values."""
        status = LoopStatus()
        assert isinstance(status.timestamp, datetime)
        assert status.loop_count == 0
        assert status.calls_made_this_hour == 0
        assert status.max_calls_per_hour == 100
        assert status.last_action == ""
        assert status.status == "idle"
        assert status.exit_reason == ""
        assert status.next_reset is None

    def test_loop_status_custom(self):
        """Test LoopStatus with custom values."""
        status = LoopStatus(
            loop_count=5,
            calls_made_this_hour=10,
            max_calls_per_hour=50,
            last_action="test",
            status="running",
            exit_reason="complete",
        )
        assert status.loop_count == 5
        assert status.calls_made_this_hour == 10
        assert status.status == "running"


# =============================================================================
# CIRCUIT BREAKER HISTORY ENTRY TESTS
# =============================================================================


class TestCircuitBreakerHistoryEntry:
    """Tests for CircuitBreakerHistoryEntry model."""

    def test_circuit_breaker_history_entry(self):
        """Test CircuitBreakerHistoryEntry creation."""
        entry = CircuitBreakerHistoryEntry(
            state="OPEN",
            reason="Too many failures",
        )
        assert isinstance(entry.timestamp, datetime)
        assert entry.state == "OPEN"
        assert entry.reason == "Too many failures"


# =============================================================================
# WORKFLOW TESTS
# =============================================================================


class TestWorkflowStep:
    """Tests for WorkflowStep model."""

    def test_workflow_step(self):
        """Test WorkflowStep creation."""
        step = WorkflowStep(index=1, content="Step content")
        assert step.index == 1
        assert step.content == "Step content"


class TestWorkflow:
    """Tests for Workflow model."""

    def test_workflow_creation(self):
        """Test Workflow creation."""
        workflow = Workflow(
            name="test_workflow",
            description="Test workflow",
            raw_content="# Test\n\nStep 1",
        )
        assert workflow.name == "test_workflow"
        assert workflow.description == "Test workflow"
        assert workflow.raw_content == "# Test\n\nStep 1"
        assert workflow.steps == []
        assert workflow.version is None

    def test_workflow_with_steps(self):
        """Test Workflow with steps."""
        steps = [WorkflowStep(index=1, content="Step 1"), WorkflowStep(index=2, content="Step 2")]
        workflow = Workflow(
            name="test",
            description="Test",
            raw_content="# Test",
            steps=steps,
            version="1.0",
        )
        assert len(workflow.steps) == 2
        assert workflow.version == "1.0"


# =============================================================================
# VERIFICATION RESULT TESTS
# =============================================================================


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_verification_result_creation(self):
        """Test VerificationResult creation."""
        result = VerificationResult(
            passed=True,
            check_type="syntax",
            message="OK",
            details=[],
            suggestions=[],
        )
        assert result.passed is True
        assert result.check_type == "syntax"
        assert result.message == "OK"

    def test_verification_result_with_details(self):
        """Test VerificationResult with details and suggestions."""
        result = VerificationResult(
            passed=False,
            check_type="lint",
            message="Issues found",
            details=["Issue 1", "Issue 2"],
            suggestions=["Fix 1", "Fix 2"],
        )
        assert result.passed is False
        assert len(result.details) == 2
        assert len(result.suggestions) == 2
