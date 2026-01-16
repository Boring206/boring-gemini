"""Tests for flow nodes evolver module."""

from unittest.mock import patch

import pytest

from boring.flow.nodes.base import FlowContext, NodeResultStatus
from boring.flow.nodes.evolver import EvolverNode


class TestEvolverNode:
    """Tests for EvolverNode."""

    @pytest.fixture
    def evolver(self):
        return EvolverNode()

    @pytest.fixture
    def context(self, tmp_path):
        return FlowContext(
            project_root=tmp_path,
            user_goal="Evolve and learn",
        )

    def test_node_name(self, evolver):
        assert evolver.name == "Evolver"

    def test_process_success(self, evolver, context):
        """Test process completes successfully."""
        result = evolver.process(context)

        assert result.status == NodeResultStatus.SUCCESS
        assert result.next_node is None  # End of flow
        assert "Evolution complete" in result.message

    def test_process_with_module_errors(self, evolver, context):
        """Test process handles ModuleNotFoundError in history."""
        context.errors.append("ModuleNotFoundError: No module named 'xyz'")

        # Create PROMPT.md for guideline addition
        prompt_file = context.project_root / "PROMPT.md"
        prompt_file.write_text("# Instructions\n", encoding="utf-8")

        result = evolver.process(context)

        assert result.status == NodeResultStatus.SUCCESS
        # Should have added guideline
        content = prompt_file.read_text(encoding="utf-8")
        assert "pip install" in content or "System 2 Guidelines" in content

    def test_add_guideline_creates_section(self, evolver, context):
        """Test that _add_guideline creates section if missing."""
        prompt_file = context.project_root / "PROMPT.md"
        prompt_file.write_text("# Instructions\n", encoding="utf-8")

        evolver._add_guideline(context.project_root, "Test rule")

        content = prompt_file.read_text(encoding="utf-8")
        assert "Test rule" in content
        assert "System 2 Guidelines" in content

    def test_add_guideline_no_duplicates(self, evolver, context):
        """Test that _add_guideline doesn't duplicate rules."""
        prompt_file = context.project_root / "PROMPT.md"
        prompt_file.write_text("# Instructions\n- Test rule\n", encoding="utf-8")

        evolver._add_guideline(context.project_root, "Test rule")

        content = prompt_file.read_text(encoding="utf-8")
        assert content.count("Test rule") == 1

    def test_add_guideline_missing_file(self, evolver, context):
        """Test that _add_guideline handles missing file."""
        # Should not raise
        evolver._add_guideline(context.project_root, "Test rule")

    def test_sync_swarm_handles_errors(self, evolver, context):
        """Test that _sync_swarm handles errors gracefully."""
        # Should not raise even if brain_manager fails
        evolver._sync_swarm(context.project_root)

    def test_synthesize_skills_handles_errors(self, evolver, context):
        """Test that _synthesize_skills handles errors gracefully."""
        # Should not raise
        evolver._synthesize_skills(context.project_root)

    def test_process_no_errors_triggers_synthesis(self, evolver, context):
        """Test that process with no errors triggers skill synthesis."""
        assert len(context.errors) == 0

        with patch.object(evolver, "_synthesize_skills") as mock_synth:
            evolver.process(context)
            mock_synth.assert_called_once_with(context.project_root)
