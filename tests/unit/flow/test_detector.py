"""
Tests for flow detector.
"""

from pathlib import Path

import pytest

from boring.flow.detector import FlowDetector
from boring.flow.states import FlowStage


class TestFlowDetector:
    """Tests for FlowDetector."""

    @pytest.fixture
    def detector(self, tmp_path):
        return FlowDetector(tmp_path)

    def test_detect_setup_stage(self, detector):
        """Test detecting setup stage (no constitution)."""
        state = detector.detect()
        assert state.stage == FlowStage.SETUP
        assert "constitution.md" in state.missing_artifacts

    def test_detect_design_stage(self, detector, tmp_path):
        """Test detecting design stage (no plan)."""
        (tmp_path / "constitution.md").write_text("# Constitution\n", encoding="utf-8")
        state = detector.detect()
        assert state.stage == FlowStage.DESIGN
        assert "implementation_plan.md" in state.missing_artifacts

    def test_detect_build_stage(self, detector, tmp_path):
        """Test detecting build stage (has tasks)."""
        (tmp_path / "constitution.md").write_text("# Constitution\n", encoding="utf-8")
        (tmp_path / "implementation_plan.md").write_text("# Plan\n", encoding="utf-8")
        (tmp_path / "task.md").write_text("- [ ] Task 1\n- [ ] Task 2\n", encoding="utf-8")

        state = detector.detect()
        assert state.stage == FlowStage.BUILD
        assert state.pending_tasks == 2

    def test_detect_polish_stage(self, detector, tmp_path):
        """Test detecting polish stage (all tasks done)."""
        (tmp_path / "constitution.md").write_text("# Constitution\n", encoding="utf-8")
        (tmp_path / "implementation_plan.md").write_text("# Plan\n", encoding="utf-8")
        (tmp_path / "task.md").write_text("- [x] Task 1\n- [x] Task 2\n", encoding="utf-8")

        state = detector.detect()
        assert state.stage == FlowStage.POLISH

    def test_count_pending_tasks(self, detector, tmp_path):
        """Test counting pending tasks."""
        task_file = tmp_path / "task.md"
        task_file.write_text("- [ ] Task 1\n- [ ] Task 2\n- [x] Task 3\n", encoding="utf-8")

        count = detector._count_pending_tasks(task_file)
        assert count == 2

    def test_count_pending_tasks_nonexistent(self, detector):
        """Test counting tasks from non-existent file."""
        count = detector._count_pending_tasks(Path("nonexistent.md"))
        assert count == 0
