from unittest.mock import AsyncMock, patch

import pytest

from boring.agents.protocol import AgentTask
from boring.agents.runner import AsyncAgentRunner


@pytest.mark.asyncio
async def test_runner_execution(tmp_path):
    runner = AsyncAgentRunner(project_root=tmp_path)

    task = AgentTask(agent_name="tester", instructions="Say hello")

    # Mock subprocess
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"Hello World", b"")
    mock_process.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
        response = await runner.execute_task(task)

        assert response.finish_reason == "stop"
        assert response.messages[1].content == "Hello World"
        assert response.latency_ms >= 0

        # Verify args
        args = mock_exec.call_args[0]
        assert "boring.main" in args
        assert "run" in args


@pytest.mark.asyncio
async def test_runner_parallel(tmp_path):
    runner = AsyncAgentRunner(project_root=tmp_path, max_concurrency=2)

    tasks = [
        AgentTask(agent_name="a1", instructions="Task 1"),
        AgentTask(agent_name="a2", instructions="Task 2"),
        AgentTask(agent_name="a3", instructions="Task 3"),
    ]

    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"Done", b"")
    mock_process.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        results = await runner.execute_parallel(tasks)
        assert len(results) == 3
        assert results[0].finish_reason == "stop"
