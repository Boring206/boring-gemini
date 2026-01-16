"""Tests for flow graph module."""

import pytest

from boring.flow.graph import FlowGraph
from boring.flow.nodes.base import (
    BaseNode,
    FlowContext,
    NodeResult,
    NodeResultStatus,
)


class MockNode(BaseNode):
    """Mock node for testing."""

    def __init__(self, name: str, result: NodeResult):
        super().__init__(name)
        self.result = result
        self.process_called = False

    def process(self, context: FlowContext) -> NodeResult:
        self.process_called = True
        return self.result


class TestFlowContext:
    """Tests for FlowContext."""

    def test_context_creation(self, tmp_path):
        ctx = FlowContext(project_root=tmp_path, user_goal="Build app")
        assert ctx.project_root == tmp_path
        assert ctx.user_goal == "Build app"
        assert ctx.memory == {}
        assert ctx.errors == []

    def test_context_memory(self, tmp_path):
        ctx = FlowContext(project_root=tmp_path, user_goal="Test")
        ctx.set_memory("key1", "value1")
        assert ctx.get_memory("key1") == "value1"
        assert ctx.get_memory("nonexistent", "default") == "default"


class TestNodeResult:
    """Tests for NodeResult."""

    def test_result_creation(self):
        result = NodeResult(
            status=NodeResultStatus.SUCCESS,
            next_node="NextNode",
            message="Done",
        )
        assert result.status == NodeResultStatus.SUCCESS
        assert result.next_node == "NextNode"
        assert result.message == "Done"

    def test_result_defaults(self):
        result = NodeResult(status=NodeResultStatus.FAILURE)
        assert result.next_node is None
        assert result.output is None
        assert result.message == ""


class TestFlowGraph:
    """Tests for FlowGraph."""

    @pytest.fixture
    def context(self, tmp_path):
        return FlowContext(project_root=tmp_path, user_goal="Test goal")

    def test_graph_creation(self, context):
        graph = FlowGraph(context)
        assert graph.context == context
        assert graph.nodes == {}
        assert graph.start_node is None

    def test_add_node(self, context):
        graph = FlowGraph(context)
        node = MockNode(
            "TestNode",
            NodeResult(status=NodeResultStatus.SUCCESS, next_node=None),
        )
        graph.add_node(node, is_start=True)

        assert "TestNode" in graph.nodes
        assert graph.start_node == "TestNode"

    def test_run_no_start_node(self, context):
        graph = FlowGraph(context)
        with pytest.raises(ValueError, match="No start node"):
            graph.run()

    def test_run_single_node(self, context):
        graph = FlowGraph(context)
        node = MockNode(
            "OnlyNode",
            NodeResult(status=NodeResultStatus.SUCCESS, next_node=None),
        )
        graph.add_node(node, is_start=True)

        result = graph.run()

        assert node.process_called
        assert "successfully" in result

    def test_run_node_chain(self, context):
        graph = FlowGraph(context)

        node1 = MockNode(
            "Node1",
            NodeResult(status=NodeResultStatus.SUCCESS, next_node="Node2"),
        )
        node2 = MockNode(
            "Node2",
            NodeResult(status=NodeResultStatus.SUCCESS, next_node=None),
        )

        graph.add_node(node1, is_start=True)
        graph.add_node(node2)

        result = graph.run()

        assert node1.process_called
        assert node2.process_called
        assert "successfully" in result

    def test_run_node_failure(self, context):
        graph = FlowGraph(context)
        node = MockNode(
            "FailNode",
            NodeResult(status=NodeResultStatus.FAILURE, message="Something failed"),
        )
        graph.add_node(node, is_start=True)

        result = graph.run()

        assert "failed" in result.lower()
        assert "Something failed" in result

    def test_run_missing_next_node(self, context):
        graph = FlowGraph(context)
        node = MockNode(
            "BadNode",
            NodeResult(status=NodeResultStatus.SUCCESS, next_node="NonExistent"),
        )
        graph.add_node(node, is_start=True)

        result = graph.run()

        assert "not found" in result

    def test_run_max_steps_limit(self, context):
        """Test that graph doesn't run forever."""
        graph = FlowGraph(context)

        # Create a cycle
        node1 = MockNode(
            "Node1",
            NodeResult(status=NodeResultStatus.SUCCESS, next_node="Node2"),
        )
        node2 = MockNode(
            "Node2",
            NodeResult(status=NodeResultStatus.SUCCESS, next_node="Node1"),
        )

        graph.add_node(node1, is_start=True)
        graph.add_node(node2)

        result = graph.run()

        assert "Max steps" in result or "Loop" in result
