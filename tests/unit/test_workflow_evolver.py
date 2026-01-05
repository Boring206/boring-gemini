"""
Unit tests for WorkflowEvolver module.
"""

import tempfile
from pathlib import Path

import pytest

from boring.workflow_evolver import WorkflowEvolver


@pytest.fixture
def temp_project():
    """Create a temporary project with workflow files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create workflow directory
        workflows_dir = project_root / ".agent" / "workflows"
        workflows_dir.mkdir(parents=True)

        # Create a sample workflow
        sample_workflow = """---
description: Test workflow
---

# Test Workflow

## Steps
1. Step one
2. Step two
"""
        (workflows_dir / "speckit-plan.md").write_text(sample_workflow)
        (workflows_dir / "speckit-tasks.md").write_text(sample_workflow)

        yield project_root


class TestWorkflowEvolver:
    """Tests for WorkflowEvolver class."""

    def test_init_creates_base_dir(self, temp_project):
        """Test that initialization creates _base directory."""
        evolver = WorkflowEvolver(temp_project)
        assert evolver.base_dir.exists()

    def test_ensure_base_backup(self, temp_project):
        """Test backup creation."""
        evolver = WorkflowEvolver(temp_project)
        result = evolver.ensure_base_backup("speckit-plan")

        assert result is True
        base_path = evolver.base_dir / "speckit-plan.base.md"
        assert base_path.exists()

    def test_ensure_base_backup_invalid_workflow(self, temp_project):
        """Test backup fails for invalid workflow name."""
        evolver = WorkflowEvolver(temp_project)
        result = evolver.ensure_base_backup("invalid-workflow")

        assert result is False

    def test_evolve_workflow(self, temp_project):
        """Test workflow evolution."""
        evolver = WorkflowEvolver(temp_project)

        new_content = """---
description: Evolved workflow
---

# Evolved Workflow

## New Steps
1. New step one
"""
        result = evolver.evolve_workflow("speckit-plan", new_content, "Testing evolution")

        assert result["status"] == "SUCCESS"
        assert "old_hash" in result
        assert "new_hash" in result

        # Verify file was updated
        workflow_path = temp_project / ".agent" / "workflows" / "speckit-plan.md"
        assert workflow_path.read_text() == new_content

    def test_evolve_workflow_creates_backup(self, temp_project):
        """Test that evolution creates backup."""
        evolver = WorkflowEvolver(temp_project)

        evolver.evolve_workflow("speckit-plan", "New content", "Test")

        base_path = evolver.base_dir / "speckit-plan.base.md"
        assert base_path.exists()

    def test_evolve_workflow_no_change(self, temp_project):
        """Test evolution with same content."""
        evolver = WorkflowEvolver(temp_project)

        workflow_path = temp_project / ".agent" / "workflows" / "speckit-plan.md"
        current_content = workflow_path.read_text()

        result = evolver.evolve_workflow("speckit-plan", current_content, "Same content")

        assert result["status"] == "NO_CHANGE"

    def test_reset_workflow(self, temp_project):
        """Test workflow reset to base."""
        evolver = WorkflowEvolver(temp_project)

        # First evolve
        original_content = (temp_project / ".agent" / "workflows" / "speckit-plan.md").read_text()
        evolver.evolve_workflow("speckit-plan", "Evolved content", "Test")

        # Then reset
        result = evolver.reset_workflow("speckit-plan")

        assert result["status"] == "SUCCESS"

        # Verify content restored
        current_content = (temp_project / ".agent" / "workflows" / "speckit-plan.md").read_text()
        assert current_content == original_content

    def test_get_workflow_status(self, temp_project):
        """Test workflow status check."""
        evolver = WorkflowEvolver(temp_project)
        evolver.ensure_base_backup("speckit-plan")

        status = evolver.get_workflow_status("speckit-plan")

        assert status["workflow"] == "speckit-plan"
        assert status["has_base"] is True
        assert status["is_evolvable"] is True
        assert "current_hash" in status

    def test_evolution_log(self, temp_project):
        """Test evolution history logging."""
        evolver = WorkflowEvolver(temp_project)

        evolver.evolve_workflow("speckit-plan", "Content 1", "First evolution")
        evolver.evolve_workflow("speckit-plan", "Content 2", "Second evolution")

        history = evolver.get_evolution_history("speckit-plan")

        assert len(history) == 2
        assert history[0]["reason"] == "First evolution"
        assert history[1]["reason"] == "Second evolution"

    def test_backup_all_workflows(self, temp_project):
        """Test backing up all workflows."""
        evolver = WorkflowEvolver(temp_project)
        results = evolver.backup_all_workflows()

        # speckit-plan and speckit-tasks exist, others don't
        assert results["speckit-plan"] is True
        assert results["speckit-tasks"] is True
        assert results["speckit-constitution"] is False  # Doesn't exist
