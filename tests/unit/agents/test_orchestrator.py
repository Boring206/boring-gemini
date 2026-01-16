"""Tests for boring.agents.orchestrator module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from boring.agents.orchestrator import (
    ArchitectAgent,
    BaseAgent,
    CoderAgent,
    MultiAgentOrchestrator,
    ReviewerAgent,
)
from boring.agents.protocol import AgentResponse, ChatMessage


class TestBaseAgent:
    """Tests for BaseAgent class."""

    @pytest.mark.asyncio
    async def test_run(self, tmp_path):
        with patch("boring.agents.orchestrator.AsyncAgentRunner"):
            mock_runner = MagicMock()
            mock_runner.execute_task = AsyncMock(
                return_value=AgentResponse(
                    messages=[
                        ChatMessage(role="user", content="test"),
                        ChatMessage(role="assistant", content="response"),
                    ]
                )
            )

            agent = BaseAgent(name="test_agent", runner=mock_runner)
            response = await agent.run("Do something")

            assert response is not None
            mock_runner.execute_task.assert_called_once()


class TestArchitectAgent:
    """Tests for ArchitectAgent class."""

    @pytest.mark.asyncio
    async def test_decompose_goal(self, tmp_path):
        mock_runner = MagicMock()
        mock_runner.execute_task = AsyncMock(
            return_value=AgentResponse(
                messages=[
                    ChatMessage(role="user", content="decompose"),
                    ChatMessage(
                        role="assistant",
                        content="- Task 1\n- Task 2\n- Task 3",
                    ),
                ]
            )
        )

        agent = ArchitectAgent(runner=mock_runner)
        tasks = await agent.decompose_goal("Build a login page")

        assert len(tasks) == 3
        assert "Task 1" in tasks[0]

    @pytest.mark.asyncio
    async def test_decompose_empty_response(self, tmp_path):
        mock_runner = MagicMock()
        mock_runner.execute_task = AsyncMock(
            return_value=AgentResponse(
                messages=[
                    ChatMessage(role="user", content="decompose"),
                    ChatMessage(role="assistant", content=""),
                ]
            )
        )

        agent = ArchitectAgent(runner=mock_runner)
        tasks = await agent.decompose_goal("Build something")

        assert tasks == []


class TestCoderAgent:
    """Tests for CoderAgent class."""

    def test_initialization(self):
        mock_runner = MagicMock()
        agent = CoderAgent(runner=mock_runner)
        assert agent.name == "coder"


class TestReviewerAgent:
    """Tests for ReviewerAgent class."""

    @pytest.mark.asyncio
    async def test_review_approved(self, tmp_path):
        mock_runner = MagicMock()
        mock_runner.execute_task = AsyncMock(
            return_value=AgentResponse(
                messages=[
                    ChatMessage(role="user", content="review"),
                    ChatMessage(role="assistant", content="APPROVED - looks good"),
                ]
            )
        )

        agent = ReviewerAgent(runner=mock_runner)
        is_approved = await agent.review_changes("Added new function")

        assert is_approved is True

    @pytest.mark.asyncio
    async def test_review_rejected(self, tmp_path):
        mock_runner = MagicMock()
        mock_runner.execute_task = AsyncMock(
            return_value=AgentResponse(
                messages=[
                    ChatMessage(role="user", content="review"),
                    ChatMessage(role="assistant", content="REQUEST_CHANGES - needs refactoring"),
                ]
            )
        )

        agent = ReviewerAgent(runner=mock_runner)
        is_approved = await agent.review_changes("Added new function")

        assert is_approved is False


class TestMultiAgentOrchestrator:
    """Tests for MultiAgentOrchestrator class."""

    def test_initialization(self, tmp_path):
        with patch("boring.agents.orchestrator.AsyncAgentRunner"):
            orch = MultiAgentOrchestrator(project_root=tmp_path)
            assert orch.root == tmp_path
            assert orch.architect is not None
            assert orch.coder is not None
            assert orch.reviewer is not None

    @pytest.mark.asyncio
    async def test_execute_goal_success(self, tmp_path):
        with patch("boring.agents.orchestrator.AsyncAgentRunner") as MockRunnerClass:
            mock_runner = MockRunnerClass.return_value

            # Architect returns tasks
            async def mock_execute(task):
                if task.agent_name == "architect":
                    return AgentResponse(
                        messages=[
                            ChatMessage(role="user", content="plan"),
                            ChatMessage(role="assistant", content="- Task A\n- Task B"),
                        ]
                    )
                elif task.agent_name == "coder":
                    return AgentResponse(
                        messages=[
                            ChatMessage(role="user", content="code"),
                            ChatMessage(role="assistant", content="Code done"),
                        ]
                    )
                elif task.agent_name == "reviewer":
                    return AgentResponse(
                        messages=[
                            ChatMessage(role="user", content="review"),
                            ChatMessage(role="assistant", content="APPROVED"),
                        ]
                    )

            mock_runner.execute_task = AsyncMock(side_effect=mock_execute)

            orch = MultiAgentOrchestrator(project_root=tmp_path)
            # Ensure the orchestrator is using our mock runner
            orch.runner = mock_runner

            # Update agents to use the same mock runner since they might have been initialized with a different one
            orch.architect.runner = mock_runner
            orch.coder.runner = mock_runner
            orch.reviewer.runner = mock_runner

            results = await orch.execute_goal("Build a feature")

            assert results is not None
            assert len(results) == 2  # Two tasks from architect

    @pytest.mark.asyncio
    async def test_execute_goal_no_tasks(self, tmp_path):
        with patch("boring.agents.orchestrator.AsyncAgentRunner") as MockRunnerClass:
            mock_runner = MockRunnerClass.return_value

            # Architect returns empty
            mock_runner.execute_task = AsyncMock(
                return_value=AgentResponse(
                    messages=[
                        ChatMessage(role="user", content="plan"),
                        ChatMessage(role="assistant", content=""),
                    ]
                )
            )

            orch = MultiAgentOrchestrator(project_root=tmp_path)
            # Ensure the orchestrator is using our mock runner
            orch.runner = mock_runner

            # Update agents to use the same mock runner
            orch.architect.runner = mock_runner
            orch.coder.runner = mock_runner
            orch.reviewer.runner = mock_runner

            results = await orch.execute_goal("Build something")

            # Should return None when no tasks
            assert results is None
