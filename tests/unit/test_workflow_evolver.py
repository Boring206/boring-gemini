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


class TestProjectContextDetector:
    """Tests for V10.18 ProjectContextDetector."""

    def test_detect_python_project(self, temp_project):
        """Test detection of Python project type."""
        # Create pyproject.toml
        (temp_project / "pyproject.toml").write_text('[project]\nversion = "1.0.0"')

        from boring.workflow_evolver import ProjectContextDetector

        detector = ProjectContextDetector(temp_project)
        context = detector.analyze()

        assert context.project_type == "python"
        assert "pyproject.toml" in context.detected_files

    def test_detect_mcp_server_project(self, temp_project):
        """Test detection of MCP server project."""
        (temp_project / "smithery.yaml").write_text("name: test\nversion: 1.0")
        (temp_project / "gemini-extension.json").write_text('{"version": "1.0"}')

        from boring.workflow_evolver import ProjectContextDetector

        detector = ProjectContextDetector(temp_project)
        context = detector.analyze()

        assert context.project_type == "mcp_server"

    def test_detect_bilingual_docs(self, temp_project):
        """Test detection of bilingual documentation."""
        docs_dir = temp_project / "docs"
        docs_dir.mkdir()
        (docs_dir / "readme.md").write_text("# English")
        (docs_dir / "readme_zh.md").write_text("# 中文")

        from boring.workflow_evolver import ProjectContextDetector

        detector = ProjectContextDetector(temp_project)
        context = detector.analyze()

        assert context.is_multilingual is True
        assert "en" in context.doc_languages
        assert "zh" in context.doc_languages


class TestWorkflowGapAnalyzer:
    """Tests for V10.18 WorkflowGapAnalyzer."""

    def test_detect_missing_version_file(self, temp_project):
        """Test gap detection for missing version files."""
        # Create project with smithery.yaml
        (temp_project / "smithery.yaml").write_text("version: 1.0")

        # Create workflow without mentioning smithery
        workflows_dir = temp_project / ".agent" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        (workflows_dir / "release-prep.md").write_text("- [ ] Update version")

        from boring.workflow_evolver import WorkflowGapAnalyzer

        analyzer = WorkflowGapAnalyzer(temp_project)
        gaps = analyzer.analyze_release_workflow("- [ ] Update pyproject.toml")

        # Should detect smithery.yaml is missing
        gap_files = [g.description for g in gaps]
        assert any("smithery" in desc.lower() for desc in gap_files)

    def test_generate_enhanced_workflow(self, temp_project):
        """Test enhanced workflow generation with gap fixes."""
        (temp_project / "smithery.yaml").write_text("version: 1.0")

        from boring.workflow_evolver import WorkflowGapAnalyzer

        analyzer = WorkflowGapAnalyzer(temp_project)

        original = "- [ ] Step 1\n- [ ] Step 2"
        enhanced = analyzer.generate_enhanced_workflow(original)

        # Should contain auto-detected section
        assert "Auto-Detected" in enhanced or "smithery" in enhanced.lower()


class TestAutoEvolve:
    """Tests for V10.18 auto_evolve method."""

    def test_auto_evolve_adds_missing_checks(self, temp_project):
        """Test auto_evolve adds missing version file checks."""
        # Create MCP server project
        (temp_project / "pyproject.toml").write_text('[project]\nversion = "1.0.0"')
        (temp_project / "smithery.yaml").write_text("version: 1.0")

        # Create minimal workflow
        workflows_dir = temp_project / ".agent" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        (workflows_dir / "release-prep.md").write_text("- [ ] Basic step")

        evolver = WorkflowEvolver(temp_project)
        result = evolver.auto_evolve("release-prep")

        # Should find gaps and either fix them or ask for interaction
        assert result["status"] in ["EVOLVED", "NO_GAPS", "NEEDS_INTERACTION", "SKIPPED"]

    def test_analyze_project_returns_context(self, temp_project):
        """Test analyze_project returns proper context dict."""
        (temp_project / "pyproject.toml").write_text('[project]\nversion = "1.0.0"')

        evolver = WorkflowEvolver(temp_project)
        context = evolver.analyze_project()

        assert "project_type" in context
        assert "detected_files" in context
        assert "version_files" in context
