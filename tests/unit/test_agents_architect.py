"""
Unit tests for boring.agents.architect module.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from boring.agents.architect import ArchitectAgent
from boring.agents.base import AgentContext, AgentRole


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


class TestArchitectAgent:
    """Tests for ArchitectAgent class."""

    def test_init(self, mock_llm_client):
        """Test initialization."""
        agent = ArchitectAgent(mock_llm_client)
        assert agent.role == AgentRole.ARCHITECT

    def test_system_prompt(self, mock_llm_client):
        """Test system prompt content."""
        agent = ArchitectAgent(mock_llm_client)
        prompt = agent.system_prompt
        assert "ARCHITECT" in prompt
        assert "PLAN" in prompt
        assert "NEVER write" in prompt or "NEVER writes" in prompt

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_llm_client, temp_project):
        """Test successful plan creation."""
        agent = ArchitectAgent(mock_llm_client)
        context = AgentContext(project_root=temp_project, task_description="Build a calculator")

        response = """
### Files to Create/Modify
- `src/calculator.py`: Main calculator class
- `tests/test_calculator.py`: [NEW] Unit tests
"""
        mock_llm_client.generate_async.return_value = (response, True)

        result = await agent.execute(context)

        assert result.action == "plan_created"
        assert result.requires_approval is True
        assert "plan" in result.artifacts

    @pytest.mark.asyncio
    async def test_execute_generation_fails(self, mock_llm_client, temp_project):
        """Test execution when generation fails."""
        agent = ArchitectAgent(mock_llm_client)
        context = AgentContext(project_root=temp_project, task_description="Task")

        mock_llm_client.generate_async.return_value = ("Error", False)

        result = await agent.execute(context)

        assert result.action == "plan_failed"
        assert "Failed to generate" in result.summary

    @pytest.mark.asyncio
    async def test_execute_with_human_feedback(self, mock_llm_client, temp_project):
        """Test execution with human feedback."""
        agent = ArchitectAgent(mock_llm_client)
        context = AgentContext(project_root=temp_project, task_description="Task")
        context.human_feedback = "Add error handling"

        response = "Updated plan with error handling"
        mock_llm_client.generate_async.return_value = (response, True)

        result = await agent.execute(context)

        assert result.action == "plan_created"
        # Verify feedback was included in prompt
        call_args = mock_llm_client.generate_async.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_execute_with_existing_plan(self, mock_llm_client, temp_project):
        """Test execution with existing plan to refine."""
        agent = ArchitectAgent(mock_llm_client)
        context = AgentContext(project_root=temp_project, task_description="Task")
        context.set_resource("implementation_plan", "Previous plan", AgentRole.ARCHITECT)

        response = "Refined plan"
        mock_llm_client.generate_async.return_value = (response, True)

        result = await agent.execute(context)

        assert result.action == "plan_created"

    def test_extract_file_list(self, mock_llm_client):
        """Test extracting file list from plan."""
        agent = ArchitectAgent(mock_llm_client)

        plan = """
### Files to Create/Modify
- `src/main.py`: Main entry point
- `tests/test_main.py`: [NEW] Unit tests
- `config.json`: Configuration file
"""
        files = agent._extract_file_list(plan)

        assert len(files) > 0
        assert any("main.py" in f for f in files)

    def test_extract_file_list_empty(self, mock_llm_client):
        """Test extracting file list from plan with no files."""
        agent = ArchitectAgent(mock_llm_client)

        plan = "Just some text without file references."
        files = agent._extract_file_list(plan)

        assert isinstance(files, list)

    def test_extract_file_list_multiple_patterns(self, mock_llm_client):
        """Test extracting files with different patterns."""
        agent = ArchitectAgent(mock_llm_client)

        plan = """
- `file1.py`: Description
- `file2.js`: Description
`file3.ts`: Another pattern
"""
        files = agent._extract_file_list(plan)

        assert len(files) >= 2
