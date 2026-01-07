# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.workflow_evolver module.
"""

import json

import pytest

from boring.workflow_evolver import (
    WorkflowEvolution,
    WorkflowEvolver,
    create_workflow_evolver,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "project"
    project.mkdir()
    return project


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestWorkflowEvolution:
    """Tests for WorkflowEvolution dataclass."""

    def test_workflow_evolution_creation(self):
        """Test WorkflowEvolution creation."""
        evolution = WorkflowEvolution(
            workflow_name="test_workflow",
            original_hash="abc123",
            new_hash="def456",
            reason="Test evolution",
            timestamp="2024-01-01",
            changes_summary="Changed logic",
        )
        assert evolution.workflow_name == "test_workflow"
        assert evolution.original_hash == "abc123"
        assert evolution.new_hash == "def456"


# =============================================================================
# WORKFLOW EVOLVER TESTS
# =============================================================================


class TestWorkflowEvolver:
    """Tests for WorkflowEvolver class."""

    def test_workflow_evolver_init(self, temp_project):
        """Test WorkflowEvolver initialization."""
        evolver = WorkflowEvolver(temp_project)
        assert evolver.project_root == temp_project
        assert evolver.workflows_dir == temp_project / ".agent" / "workflows"

    def test_workflow_evolver_init_with_log_dir(self, temp_project):
        """Test WorkflowEvolver with custom log directory."""
        log_dir = temp_project / "custom_logs"
        evolver = WorkflowEvolver(temp_project, log_dir=log_dir)
        assert evolver.log_dir == log_dir

    def test_workflow_evolver_compute_hash(self, temp_project):
        """Test WorkflowEvolver._compute_hash method."""
        evolver = WorkflowEvolver(temp_project)

        hash1 = evolver._compute_hash("test content")
        hash2 = evolver._compute_hash("test content")

        assert hash1 == hash2
        assert len(hash1) == 16

    def test_workflow_evolver_load_evolution_log(self, temp_project):
        """Test WorkflowEvolver._load_evolution_log method."""
        evolver = WorkflowEvolver(temp_project)

        log = evolver._load_evolution_log()
        assert isinstance(log, list)

    def test_workflow_evolver_load_evolution_log_existing(self, temp_project):
        """Test WorkflowEvolver._load_evolution_log with existing file."""
        evolver = WorkflowEvolver(temp_project)
        evolver.evolution_log_path.write_text(json.dumps([{"test": "data"}]))

        log = evolver._load_evolution_log()
        assert len(log) == 1

    def test_workflow_evolver_save_evolution_log(self, temp_project):
        """Test WorkflowEvolver._save_evolution_log method."""
        evolver = WorkflowEvolver(temp_project)

        log = [{"test": "data"}]
        evolver._save_evolution_log(log)

        assert evolver.evolution_log_path.exists()
        loaded = json.loads(evolver.evolution_log_path.read_text())
        assert len(loaded) == 1

    def test_workflow_evolver_ensure_base_backup(self, temp_project):
        """Test WorkflowEvolver.ensure_base_backup method."""
        evolver = WorkflowEvolver(temp_project)

        workflows_dir = temp_project / ".agent" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        workflow_file = workflows_dir / "speckit-plan.md"
        workflow_file.write_text("# Original workflow")

        result = evolver.ensure_base_backup("speckit-plan")
        assert isinstance(result, bool)

    def test_workflow_evolver_backup_all_workflows(self, temp_project):
        """Test WorkflowEvolver.backup_all_workflows method."""
        evolver = WorkflowEvolver(temp_project)

        workflows_dir = temp_project / ".agent" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        (workflows_dir / "speckit-plan.md").write_text("# Plan")

        result = evolver.backup_all_workflows()
        assert isinstance(result, dict)

    def test_workflow_evolver_evolve_workflow(self, temp_project):
        """Test WorkflowEvolver.evolve_workflow method."""
        evolver = WorkflowEvolver(temp_project)

        workflows_dir = temp_project / ".agent" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        workflow_file = workflows_dir / "speckit-plan.md"
        workflow_file.write_text("# Original")

        result = evolver.evolve_workflow(
            "speckit-plan",
            new_content="# Evolved workflow",
            reason="Test evolution",
        )
        assert isinstance(result, dict)

    def test_workflow_evolver_reset_workflow(self, temp_project):
        """Test WorkflowEvolver.reset_workflow method."""
        evolver = WorkflowEvolver(temp_project)

        workflows_dir = temp_project / ".agent" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        base_dir = workflows_dir / "_base"
        base_dir.mkdir(exist_ok=True)
        (base_dir / "speckit-plan.md").write_text("# Base workflow")
        (workflows_dir / "speckit-plan.md").write_text("# Modified")

        result = evolver.reset_workflow("speckit-plan")
        assert isinstance(result, dict)

    def test_workflow_evolver_get_workflow_status(self, temp_project):
        """Test WorkflowEvolver.get_workflow_status method."""
        evolver = WorkflowEvolver(temp_project)

        workflows_dir = temp_project / ".agent" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        (workflows_dir / "speckit-plan.md").write_text("# Workflow")

        status = evolver.get_workflow_status("speckit-plan")
        assert isinstance(status, dict)

    def test_workflow_evolver_get_evolution_history(self, temp_project):
        """Test WorkflowEvolver.get_evolution_history method."""
        evolver = WorkflowEvolver(temp_project)

        history = evolver.get_evolution_history()
        assert isinstance(history, list)

    def test_workflow_evolver_get_evolution_history_filtered(self, temp_project):
        """Test WorkflowEvolver.get_evolution_history with workflow filter."""
        evolver = WorkflowEvolver(temp_project)

        history = evolver.get_evolution_history(workflow_name="speckit-plan")
        assert isinstance(history, list)


# =============================================================================
# MODULE FUNCTIONS TESTS
# =============================================================================


class TestCreateWorkflowEvolver:
    """Tests for create_workflow_evolver function."""

    def test_create_workflow_evolver(self, temp_project):
        """Test create_workflow_evolver function."""
        evolver = create_workflow_evolver(temp_project)
        assert isinstance(evolver, WorkflowEvolver)
        assert evolver.project_root == temp_project

    def test_create_workflow_evolver_with_log_dir(self, temp_project):
        """Test create_workflow_evolver with log directory."""
        log_dir = temp_project / "logs"
        evolver = create_workflow_evolver(temp_project, log_dir=log_dir)
        assert evolver.log_dir == log_dir
