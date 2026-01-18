"""
Tests for Progress Feedback and Cost Warnings (Phase 1).
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.flow.graph import FlowGraph
from boring.flow.nodes.base import BaseNode, FlowContext, NodeResult, NodeResultStatus


class MockNode(BaseNode):
    def __init__(self, name: str, next_node: str | None = None):
        super().__init__(name)
        self.next_node = next_node

    async def process(self, context: FlowContext) -> NodeResult:
        return NodeResult(status=NodeResultStatus.SUCCESS, next_node=self.next_node, message="Done")


@pytest.mark.asyncio
async def test_cost_warning_trigger(tmp_path):
    """Verify that cost warning is printed at the threshold."""
    context = FlowContext(project_root=tmp_path, user_goal="Cost Test", auto_mode=True)
    graph = FlowGraph(context)

    # Create a chain of 26 nodes to trigger the warning at step 25
    nodes = []
    for i in range(27):
        name = f"Node{i}"
        next_name = f"Node{i + 1}" if i < 26 else None
        node = MockNode(name, next_name)
        graph.add_node(node, is_start=(i == 0))
        nodes.append(node)

    # Patch console to verify output
    with patch("boring.flow.graph.console") as mock_console:
        # We also need to patch the status context manager because it's called
        mock_status = MagicMock()
        mock_console.status.return_value.__enter__.return_value = mock_status

        await graph.run()

        # Check if warning was printed
        warning_calls = [
            args[0]
            for name, args, kwargs in mock_console.print.mock_calls
            if isinstance(args[0], str) and "API 成本" in args[0]
        ]

        assert len(warning_calls) == 1
        assert "25 步" in warning_calls[0]


@pytest.mark.asyncio
async def test_progress_spinner_update(tmp_path):
    """Verify that status.update is called with step info."""
    context = FlowContext(project_root=tmp_path, user_goal="Spinner Test")
    graph = FlowGraph(context)

    node1 = MockNode("Node1", None)
    graph.add_node(node1, is_start=True)

    with patch("boring.flow.graph.console") as mock_console:
        mock_status = MagicMock()
        mock_console.status.return_value.__enter__.return_value = mock_status

        await graph.run()

        # Check if status was created
        mock_console.status.assert_called()

        # Check if update was called
        update_calls = [args[0] for name, args, kwargs in mock_status.update.mock_calls]
        assert any("Step 1/50" in call for call in update_calls)


@pytest.mark.asyncio
async def test_interruption_at_checkpoint(tmp_path):
    """Phase 3.1: Verify user interruption at checkpoint."""
    context = FlowContext(project_root=tmp_path, user_goal="Interrupt Test", auto_mode=False)
    graph = FlowGraph(context)

    # Create chain of 11 nodes (Checkpoint is at 10)
    nodes = []
    for i in range(12):
        name = f"Node{i}"
        next_name = f"Node{i + 1}" if i < 11 else None
        node = MockNode(name, next_name)
        graph.add_node(node, is_start=(i == 0))
        nodes.append(node)

    with patch("boring.flow.graph.console") as mock_console:
        mock_status = MagicMock()
        mock_console.status.return_value.__enter__.return_value = mock_status

        # Mock Confirm.ask to return False (Interrupt)
        with patch("rich.prompt.Confirm.ask", return_value=False) as mock_confirm:
            result = await graph.run()

            assert result.success is False
            assert "User interrupted" in result.message
            mock_confirm.assert_called_once()
