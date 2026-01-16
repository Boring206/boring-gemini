"""Tests for flow nodes polish module."""

from unittest.mock import patch

import pytest

from boring.flow.nodes.base import FlowContext, NodeResultStatus
from boring.flow.nodes.polish import PolishNode


class TestPolishNode:
    """Tests for PolishNode."""

    @pytest.fixture
    def polish(self):
        return PolishNode()

    @pytest.fixture
    def context(self, tmp_path):
        return FlowContext(
            project_root=tmp_path,
            user_goal="Polish the code",
        )

    def test_node_name(self, polish):
        assert polish.name == "Polish"

    def test_process_first_attempt(self, polish, context):
        """Test process on first attempt."""
        # Mock vibe check to be unavailable
        with patch.dict("sys.modules", {"boring.mcp.tools.vibe": None}):
            with patch("shutil.which", return_value=None):
                result = polish.process(context)

        # Should proceed to Evolver without issues
        assert result.next_node == "Evolver"

    def test_process_max_attempts(self, polish, context):
        """Test process when max attempts reached."""
        context.stats["polish_attempts"] = 2

        result = polish.process(context)

        assert result.status == NodeResultStatus.SUCCESS
        assert result.next_node == "Evolver"
        assert "Max retries" in result.message

    def test_process_increments_attempts(self, polish, context):
        """Test that process increments attempt counter."""
        assert context.stats.get("polish_attempts", 0) == 0

        with patch.dict("sys.modules", {"boring.mcp.tools.vibe": None}):
            with patch("shutil.which", return_value=None):
                polish.process(context)

        assert context.stats["polish_attempts"] == 1

    def test_process_with_ruff_available(self, polish, context):
        """Test process with ruff linter available."""
        with patch.dict("sys.modules", {"boring.mcp.tools.vibe": None}):
            with patch("shutil.which", return_value="/usr/bin/ruff"):
                with patch("subprocess.check_call"):
                    result = polish.process(context)

        assert result.next_node == "Evolver"

    def test_process_with_ruff_failure(self, polish, context):
        """Test process when ruff finds issues (first attempt)."""
        import subprocess

        with patch.dict("sys.modules", {"boring.mcp.tools.vibe": None}):
            with patch("shutil.which", return_value="/usr/bin/ruff"):
                with patch(
                    "subprocess.check_call",
                    side_effect=subprocess.CalledProcessError(1, "ruff"),
                ):
                    result = polish.process(context)

        # Should return to Builder on first attempt
        assert result.next_node == "Builder"
