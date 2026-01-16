"""Tests for flow nodes architect module."""

from unittest.mock import patch

import pytest

from boring.flow.nodes.architect import ArchitectNode
from boring.flow.nodes.base import FlowContext, NodeResultStatus


class TestArchitectNode:
    """Tests for ArchitectNode."""

    @pytest.fixture
    def architect(self):
        return ArchitectNode()

    @pytest.fixture
    def context(self, tmp_path):
        return FlowContext(
            project_root=tmp_path,
            user_goal="Build a login page",
        )

    def test_node_name(self, architect):
        assert architect.name == "Architect"

    def test_fallback_plan_creates_task_file(self, architect, context):
        """Test that fallback plan creates a task file."""
        result = architect._fallback_plan(context)

        task_file = context.project_root / "task.md"
        assert task_file.exists()
        assert context.user_goal in task_file.read_text(encoding="utf-8")
        assert result.status == NodeResultStatus.SUCCESS
        assert result.next_node == "Builder"

    def test_process_with_missing_tools(self, architect, context):
        """Test process when speckit tools are not available."""
        # Mock the import to fail
        with patch.dict("sys.modules", {"boring.mcp.speckit_tools": None}):
            architect.process(context)

        # Should use fallback
        task_file = context.project_root / "task.md"
        assert task_file.exists()

    def test_sync_knowledge_silent_failure(self, architect):
        """Test that _sync_knowledge handles failures gracefully."""
        # Should not raise even if brain_manager fails
        architect._sync_knowledge()
