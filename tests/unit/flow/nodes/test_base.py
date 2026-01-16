"""Tests for flow nodes base module."""

import pytest

from boring.flow.nodes.base import (
    BaseNode,
    FlowContext,
    NodeResult,
    NodeResultStatus,
)


class ConcreteNode(BaseNode):
    """Concrete implementation for testing."""

    def process(self, context: FlowContext) -> NodeResult:
        return NodeResult(
            status=NodeResultStatus.SUCCESS,
            message="Processed",
        )


class TestNodeResultStatus:
    """Tests for NodeResultStatus enum."""

    def test_status_values(self):
        assert NodeResultStatus.SUCCESS.value == "SUCCESS"
        assert NodeResultStatus.FAILURE.value == "FAILURE"
        assert NodeResultStatus.NEEDS_RETRY.value == "NEEDS_RETRY"
        assert NodeResultStatus.SKIPPED.value == "SKIPPED"


class TestFlowContext:
    """Tests for FlowContext dataclass."""

    def test_creation(self, tmp_path):
        ctx = FlowContext(
            project_root=tmp_path,
            user_goal="Build something",
        )
        assert ctx.project_root == tmp_path
        assert ctx.user_goal == "Build something"

    def test_default_values(self, tmp_path):
        ctx = FlowContext(project_root=tmp_path, user_goal="Test")
        assert ctx.memory == {}
        assert ctx.generated_artifacts == {}
        assert ctx.errors == []
        assert ctx.stats == {}

    def test_memory_operations(self, tmp_path):
        ctx = FlowContext(project_root=tmp_path, user_goal="Test")

        # Set and get
        ctx.set_memory("key", "value")
        assert ctx.get_memory("key") == "value"

        # Get with default
        assert ctx.get_memory("missing", "default") == "default"

        # Get missing without default
        assert ctx.get_memory("missing") is None

    def test_errors_list(self, tmp_path):
        ctx = FlowContext(project_root=tmp_path, user_goal="Test")
        ctx.errors.append("Error 1")
        ctx.errors.append("Error 2")
        assert len(ctx.errors) == 2


class TestNodeResult:
    """Tests for NodeResult dataclass."""

    def test_success_result(self):
        result = NodeResult(
            status=NodeResultStatus.SUCCESS,
            next_node="NextNode",
            message="Done",
        )
        assert result.status == NodeResultStatus.SUCCESS
        assert result.next_node == "NextNode"
        assert result.message == "Done"

    def test_failure_result(self):
        result = NodeResult(
            status=NodeResultStatus.FAILURE,
            message="Something went wrong",
        )
        assert result.status == NodeResultStatus.FAILURE
        assert result.next_node is None

    def test_result_with_output(self):
        result = NodeResult(
            status=NodeResultStatus.SUCCESS,
            output={"key": "value"},
        )
        assert result.output == {"key": "value"}


class TestBaseNode:
    """Tests for BaseNode abstract class."""

    def test_node_creation(self):
        node = ConcreteNode("TestNode")
        assert node.name == "TestNode"

    def test_node_process(self, tmp_path):
        node = ConcreteNode("TestNode")
        ctx = FlowContext(project_root=tmp_path, user_goal="Test")

        result = node.process(ctx)

        assert result.status == NodeResultStatus.SUCCESS
        assert result.message == "Processed"

    def test_get_description(self):
        node = ConcreteNode("TestNode")
        desc = node.get_description()
        # Should return docstring or name
        assert desc is not None
        assert len(desc) > 0

    def test_abstract_process_required(self):
        """Test that BaseNode cannot be instantiated without process."""
        with pytest.raises(TypeError):
            BaseNode("AbstractNode")
