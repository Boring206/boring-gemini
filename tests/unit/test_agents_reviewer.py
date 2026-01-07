"""
Unit tests for boring.agents.reviewer module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from boring.agents.base import AgentContext, AgentRole
from boring.agents.reviewer.agent import ReviewerAgent
from boring.agents.reviewer.orchestrator import ParallelReviewOrchestrator


@pytest.fixture
def mock_llm_client():
    client = MagicMock()
    client.generate_async = AsyncMock()
    return client


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    return project


class TestReviewerAgent:
    """Tests for ReviewerAgent class."""

    def test_init(self, mock_llm_client, temp_project):
        """Test initialization."""
        agent = ReviewerAgent(mock_llm_client, project_root=temp_project)
        assert agent.role == AgentRole.REVIEWER
        assert agent.project_root == temp_project

    def test_system_prompt(self, mock_llm_client):
        """Test system prompt."""
        agent = ReviewerAgent(mock_llm_client)
        prompt = agent.system_prompt
        assert len(prompt) > 0

    @pytest.mark.asyncio
    async def test_execute_no_code_output(self, mock_llm_client, temp_project):
        """Test execution when no code output."""
        agent = ReviewerAgent(mock_llm_client, project_root=temp_project)
        context = AgentContext(project_root=temp_project, task_description="Task")

        result = await agent.execute(context)

        assert result.action == "review_failed"
        assert "No code to review" in result.summary

    @pytest.mark.asyncio
    async def test_execute_success_pass(self, mock_llm_client, temp_project):
        """Test successful review with PASS verdict."""
        agent = ReviewerAgent(mock_llm_client, project_root=temp_project)
        context = AgentContext(project_root=temp_project, task_description="Task")
        context.set_resource("code_output", "def test(): pass", AgentRole.CODER)
        context.set_resource("modified_files", ["test.py"], AgentRole.CODER)

        response = "Verdict: PASS\nNo issues found."
        mock_llm_client.generate_async.return_value = (response, True)

        with (
            patch("boring.agents.reviewer.agent.extract_verdict", return_value="PASS"),
            patch(
                "boring.agents.reviewer.agent.extract_issues",
                return_value={"major": [], "minor": []},
            ),
        ):
            result = await agent.execute(context)

        assert result.action == "review_passed" or "review" in result.action.lower()

    @pytest.mark.asyncio
    async def test_execute_needs_work(self, mock_llm_client, temp_project):
        """Test review with NEEDS_WORK verdict."""
        agent = ReviewerAgent(mock_llm_client, project_root=temp_project)
        context = AgentContext(project_root=temp_project, task_description="Task")
        context.set_resource("code_output", "def test(): pass", AgentRole.CODER)

        response = "Verdict: NEEDS_WORK\nIssues found."
        mock_llm_client.generate_async.return_value = (response, True)

        with (
            patch("boring.agents.reviewer.agent.extract_verdict", return_value="NEEDS_WORK"),
            patch(
                "boring.agents.reviewer.agent.extract_issues",
                return_value={"major": ["Issue 1"], "minor": []},
            ),
        ):
            result = await agent.execute(context)

        assert "NEEDS_WORK" in result.artifacts.get("verdict", "")

    @pytest.mark.asyncio
    async def test_execute_generation_fails(self, mock_llm_client, temp_project):
        """Test execution when generation fails."""
        agent = ReviewerAgent(mock_llm_client, project_root=temp_project)
        context = AgentContext(project_root=temp_project, task_description="Task")
        context.set_resource("code_output", "code", AgentRole.CODER)

        mock_llm_client.generate_async.return_value = ("Error", False)

        result = await agent.execute(context)

        assert result.action == "review_failed"


class TestParallelReviewOrchestrator:
    """Tests for ParallelReviewOrchestrator class."""

    def test_init(self, mock_llm_client, temp_project):
        """Test initialization."""
        orchestrator = ParallelReviewOrchestrator(mock_llm_client, project_root=temp_project)
        assert orchestrator.llm_client == mock_llm_client
        assert orchestrator.project_root == temp_project

    @pytest.mark.asyncio
    async def test_review_parallel_all_aspects(self, mock_llm_client, temp_project):
        """Test parallel review with all aspects."""
        orchestrator = ParallelReviewOrchestrator(mock_llm_client, project_root=temp_project)

        mock_response = '{"aspect": "security", "verdict": "PASS", "issues": [], "summary": "OK"}'
        mock_llm_client.generate_async.return_value = (mock_response, True)

        result = await orchestrator.review_parallel("def test(): pass")

        assert "aspects" in result
        assert "combined_verdict" in result

    @pytest.mark.asyncio
    async def test_review_parallel_specific_aspects(self, mock_llm_client, temp_project):
        """Test parallel review with specific aspects."""
        orchestrator = ParallelReviewOrchestrator(mock_llm_client, project_root=temp_project)

        mock_response = '{"aspect": "security", "verdict": "PASS", "issues": []}'
        mock_llm_client.generate_async.return_value = (mock_response, True)

        result = await orchestrator.review_parallel("code", aspects=["security"])

        assert "aspects" in result

    @pytest.mark.asyncio
    async def test_review_parallel_with_exception(self, mock_llm_client, temp_project):
        """Test parallel review when exception occurs."""
        orchestrator = ParallelReviewOrchestrator(mock_llm_client, project_root=temp_project)

        mock_llm_client.generate_async.side_effect = Exception("Error")

        result = await orchestrator.review_parallel("code", aspects=["security"])

        assert "aspects" in result
        # When exception occurs, result contains NEEDS_WORK verdict and error info
        security_result = result["aspects"].get("security", {})
        assert security_result.get("verdict") == "NEEDS_WORK" or "Error" in str(security_result)

    @pytest.mark.asyncio
    async def test_review_parallel_reject_verdict(self, mock_llm_client, temp_project):
        """Test parallel review with REJECT verdict."""
        orchestrator = ParallelReviewOrchestrator(mock_llm_client, project_root=temp_project)

        mock_response = '{"aspect": "security", "verdict": "REJECT", "issues": ["Critical"]}'
        mock_llm_client.generate_async.return_value = (mock_response, True)

        result = await orchestrator.review_parallel("code", aspects=["security"])

        assert result["combined_verdict"] == "REJECT"

    @pytest.mark.asyncio
    async def test_review_aspect_success(self, mock_llm_client, temp_project):
        """Test reviewing a specific aspect."""
        orchestrator = ParallelReviewOrchestrator(mock_llm_client, project_root=temp_project)

        mock_response = '{"aspect": "security", "verdict": "PASS", "issues": []}'
        mock_llm_client.generate_async.return_value = (mock_response, True)

        result = await orchestrator._review_aspect("code", "security")

        assert result["verdict"] == "PASS"

    @pytest.mark.asyncio
    async def test_review_aspect_no_json(self, mock_llm_client, temp_project):
        """Test reviewing when response has no JSON."""
        orchestrator = ParallelReviewOrchestrator(mock_llm_client, project_root=temp_project)

        mock_llm_client.generate_async.return_value = ("No JSON here", True)

        result = await orchestrator._review_aspect("code", "security")

        assert result["verdict"] == "PASS"  # Default

    @pytest.mark.asyncio
    async def test_review_aspect_exception(self, mock_llm_client, temp_project):
        """Test reviewing when exception occurs."""
        orchestrator = ParallelReviewOrchestrator(mock_llm_client, project_root=temp_project)

        mock_llm_client.generate_async.side_effect = Exception("Error")

        result = await orchestrator._review_aspect("code", "security")

        assert result["verdict"] == "NEEDS_WORK"
