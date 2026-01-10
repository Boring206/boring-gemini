"""
Tests for AgentOrchestrator.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from boring.agents.orchestrator import AgentOrchestrator


@pytest.fixture
def mock_llm():
    """Create a mock LLM client."""
    llm = MagicMock()
    llm.generate_text = AsyncMock(return_value="Generated response")
    return llm


@pytest.fixture
def orchestrator(mock_llm, tmp_path):
    """Create an AgentOrchestrator instance."""
    return AgentOrchestrator(
        llm_client=mock_llm, project_root=tmp_path, auto_approve_plans=True
    )


def test_orchestrator_init(mock_llm, tmp_path):
    """Test AgentOrchestrator initialization."""
    orch = AgentOrchestrator(llm_client=mock_llm, project_root=tmp_path)

    assert orch.project_root == tmp_path
    assert orch.architect is not None
    assert orch.coder is not None
    assert orch.reviewer is not None


def test_orchestrator_with_callback(mock_llm, tmp_path):
    """Test orchestrator with human approval callback."""
    callback = AsyncMock()
    orch = AgentOrchestrator(
        llm_client=mock_llm, project_root=tmp_path, human_callback=callback
    )

    assert orch.human_callback is callback


def test_orchestrator_auto_approve(mock_llm, tmp_path):
    """Test orchestrator with auto-approve enabled."""
    orch = AgentOrchestrator(
        llm_client=mock_llm, project_root=tmp_path, auto_approve_plans=True
    )

    assert orch.auto_approve_plans is True


def test_orchestrator_with_shadow_guard(mock_llm, tmp_path):
    """Test orchestrator with shadow guard."""
    shadow_guard = MagicMock()
    orch = AgentOrchestrator(
        llm_client=mock_llm, project_root=tmp_path, shadow_guard=shadow_guard
    )

    assert orch.shadow_guard is shadow_guard
    assert orch.coder.shadow_guard is shadow_guard


def test_orchestrator_max_iterations(orchestrator):
    """Test MAX_ITERATIONS constant."""
    assert AgentOrchestrator.MAX_ITERATIONS == 5


def test_orchestrator_agents_lookup(orchestrator):
    """Test that agents are accessible by role."""
    from boring.agents.base import AgentRole

    assert orchestrator._agents[AgentRole.ARCHITECT] is orchestrator.architect
    assert orchestrator._agents[AgentRole.CODER] is orchestrator.coder
    assert orchestrator._agents[AgentRole.REVIEWER] is orchestrator.reviewer


@pytest.mark.asyncio
async def test_orchestrator_execute_basic(orchestrator, mock_llm):
    """Test basic orchestrator execution."""
    # Mock the agents' execute methods
    orchestrator.architect.execute = AsyncMock()
    orchestrator.coder.execute = AsyncMock()
    orchestrator.reviewer.execute = AsyncMock()

    # Mock return values
    from boring.agents.base import AgentMessage, AgentRole

    orchestrator.architect.execute.return_value = AgentMessage(
        sender=AgentRole.ARCHITECT,
        receiver=AgentRole.CODER,
        action="plan_ready",
        summary="Plan created",
        artifacts={"plan": "Test plan"},
        requires_approval=False,
    )

    orchestrator.coder.execute.return_value = AgentMessage(
        sender=AgentRole.CODER,
        receiver=AgentRole.REVIEWER,
        action="code_ready",
        summary="Code written",
        artifacts={"files": ["test.py"]},
        requires_approval=False,
    )

    orchestrator.reviewer.execute.return_value = AgentMessage(
        sender=AgentRole.REVIEWER,
        receiver=AgentRole.ORCHESTRATOR,
        action="review_approve",
        summary="Looks good",
        artifacts={},
        requires_approval=False,
    )

    result = await orchestrator.execute("Create a test function")

    # Should have called the agents
    assert orchestrator.architect.execute.called
