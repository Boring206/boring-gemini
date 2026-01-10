"""
Tests for CoderAgent.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from boring.agents.base import AgentContext, AgentRole
from boring.agents.coder import CoderAgent


@pytest.fixture
def mock_llm():
    """Create a mock LLM client."""
    llm = MagicMock()
    # Make generate_text return an AsyncMock for async compatibility
    llm.generate_text = AsyncMock(return_value="Generated code")
    return llm


@pytest.fixture
def coder_agent(mock_llm, tmp_path):
    """Create a CoderAgent instance."""
    return CoderAgent(mock_llm, project_root=tmp_path)


def test_coder_agent_init(mock_llm, tmp_path):
    """Test CoderAgent initialization."""
    agent = CoderAgent(mock_llm, project_root=tmp_path)
    assert agent.role == AgentRole.CODER
    assert agent.project_root == tmp_path


def test_coder_agent_system_prompt(coder_agent):
    """Test that system prompt is defined."""
    prompt = coder_agent.system_prompt
    assert isinstance(prompt, str)
    assert "CODER" in prompt
    assert "implementation" in prompt.lower()


@pytest.mark.asyncio
async def test_coder_execute_no_plan(coder_agent, tmp_path):
    """Test coder execution when no plan is available."""
    context = AgentContext(project_root=tmp_path, task_description="Test task")

    message = await coder_agent.execute(context)

    assert message.sender == AgentRole.CODER
    assert message.action == "code_failed"
    assert "plan" in message.summary.lower()


@pytest.mark.asyncio
async def test_coder_execute_with_plan(coder_agent, mock_llm, tmp_path):
    """Test coder execution with a valid plan."""
    context = AgentContext(project_root=tmp_path, task_description="Test task")
    context.set_resource("implementation_plan", "Create a new file test.py", AgentRole.ARCHITECT)

    # Mock the _generate method directly
    coder_agent._generate = AsyncMock(
        return_value=(
            """
### File: `test.py`
```python
def hello():
    return "world"
```
""",
            True,
        )
    )

    message = await coder_agent.execute(context)

    assert message.sender == AgentRole.CODER
    # Should have called _generate
    assert coder_agent._generate.call_count > 0


def test_coder_with_shadow_guard(mock_llm, tmp_path):
    """Test CoderAgent with shadow guard."""
    shadow_guard = MagicMock()
    agent = CoderAgent(mock_llm, project_root=tmp_path, shadow_guard=shadow_guard)

    assert agent.shadow_guard is shadow_guard


def test_coder_default_project_root(mock_llm):
    """Test CoderAgent with default project root."""
    agent = CoderAgent(mock_llm)
    assert agent.project_root == Path.cwd()
