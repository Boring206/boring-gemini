"""Tests for flow nodes builder module."""

from unittest.mock import MagicMock, patch

import pytest

from boring.flow.nodes.base import FlowContext, NodeResultStatus
from boring.flow.nodes.builder import BuilderNode


class TestBuilderNode:
    """Tests for BuilderNode."""

    @pytest.fixture
    def builder(self):
        return BuilderNode()

    @pytest.fixture
    def context(self, tmp_path):
        return FlowContext(
            project_root=tmp_path,
            user_goal="Build a feature",
        )

    def test_node_name(self, builder):
        assert builder.name == "Builder"

    @pytest.mark.asyncio
    async def test_process_tasks_incomplete(self, builder, context):
        """Test process when tasks remain incomplete."""
        # Create task file with pending tasks
        task_file = context.project_root / "task.md"
        task_file.write_text("- [ ] Task 1\n- [ ] Task 2\n", encoding="utf-8")

        # Mock AgentLoop to avoid actual execution
        with patch("boring.loop.AgentLoop") as MockLoop:
            mock_loop = MagicMock()
            MockLoop.return_value = mock_loop

            result = await builder.process(context)

        # Should fail because tasks incomplete
        assert result.status == NodeResultStatus.FAILURE
        assert result.next_node == "Healer"

    @pytest.mark.asyncio
    async def test_process_tasks_complete(self, builder, context):
        """Test process when all tasks are complete."""
        # Create task file with completed tasks
        task_file = context.project_root / "task.md"
        task_file.write_text("- [x] Task 1\n- [x] Task 2\n", encoding="utf-8")

        with patch("boring.loop.AgentLoop") as MockLoop:
            mock_loop = MagicMock()
            MockLoop.return_value = mock_loop

            result = await builder.process(context)

        assert result.status == NodeResultStatus.SUCCESS
        assert result.next_node == "Polish"

    @pytest.mark.asyncio
    async def test_process_handles_loop_exception(self, builder, context):
        """Test process handles AgentLoop exceptions."""
        # Create dummy task file to pass initial contract check
        (context.project_root / "task.md").write_text("- [ ] Task 1", encoding="utf-8")

        with patch("boring.loop.AgentLoop") as MockLoop:
            MockLoop.side_effect = Exception("Loop crashed")

            result = await builder.process(context)

        assert result.status == NodeResultStatus.FAILURE
        assert "crashed" in result.message.lower()
        assert result.next_node == "Healer"
        assert len(context.errors) > 0
