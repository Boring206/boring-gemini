# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.workflow_manager module.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boring.workflow_manager import (
    WorkflowManager,
    WorkflowMetadata,
    WorkflowPackage,
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


class TestWorkflowMetadata:
    """Tests for WorkflowMetadata dataclass."""

    def test_workflow_metadata_creation(self):
        """Test WorkflowMetadata creation."""
        metadata = WorkflowMetadata(
            name="test_workflow",
            version="1.0.0",
            description="Test description",
            author="Test Author",
            tags=["test", "demo"],
        )
        assert metadata.name == "test_workflow"
        assert metadata.version == "1.0.0"
        assert metadata.author == "Test Author"
        assert len(metadata.tags) == 2

    def test_workflow_metadata_post_init(self):
        """Test WorkflowMetadata.__post_init__ method."""
        metadata = WorkflowMetadata(
            name="test",
            version="1.0.0",
            description="Test",
        )
        assert metadata.tags == []
        assert metadata.created_at > 0


class TestWorkflowPackage:
    """Tests for WorkflowPackage dataclass."""

    def test_workflow_package_creation(self):
        """Test WorkflowPackage creation."""
        metadata = WorkflowMetadata(
            name="test",
            version="1.0.0",
            description="Test",
        )
        package = WorkflowPackage(
            metadata=metadata,
            content="# Test workflow",
            config={"key": "value"},
        )
        assert package.metadata == metadata
        assert package.content == "# Test workflow"
        assert package.config == {"key": "value"}

    def test_workflow_package_to_json(self):
        """Test WorkflowPackage.to_json method."""
        metadata = WorkflowMetadata(
            name="test",
            version="1.0.0",
            description="Test",
        )
        package = WorkflowPackage(metadata=metadata, content="# Test")

        json_str = package.to_json()
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["metadata"]["name"] == "test"

    def test_workflow_package_from_json(self):
        """Test WorkflowPackage.from_json method."""
        json_str = json.dumps(
            {
                "metadata": {
                    "name": "test",
                    "version": "1.0.0",
                    "description": "Test",
                },
                "content": "# Test workflow",
            }
        )

        package = WorkflowPackage.from_json(json_str)
        assert package.metadata.name == "test"
        assert package.content == "# Test workflow"

    def test_workflow_package_from_json_invalid(self):
        """Test WorkflowPackage.from_json with invalid JSON."""
        with pytest.raises(ValueError):
            WorkflowPackage.from_json("invalid json")

    def test_workflow_package_from_json_missing_fields(self):
        """Test WorkflowPackage.from_json with missing fields."""
        json_str = json.dumps({"metadata": {}})

        with pytest.raises(ValueError):
            WorkflowPackage.from_json(json_str)


# =============================================================================
# WORKFLOW MANAGER TESTS
# =============================================================================


class TestWorkflowManager:
    """Tests for WorkflowManager class."""

    def test_workflow_manager_init(self, temp_project):
        """Test WorkflowManager initialization."""
        with patch("boring.workflow_manager.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = WorkflowManager(temp_project)
            assert manager.project_root == temp_project

    def test_workflow_manager_init_default_root(self):
        """Test WorkflowManager with default project root."""
        with patch("boring.workflow_manager.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = Path("/default")
            manager = WorkflowManager()
            assert manager.project_root == Path("/default")

    def test_workflow_manager_list_local_workflows(self, temp_project):
        """Test WorkflowManager.list_local_workflows method."""
        workflows_dir = temp_project / ".agent" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "workflow1.md").write_text("# Workflow 1")
        (workflows_dir / "workflow2.md").write_text("# Workflow 2")

        with patch("boring.workflow_manager.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = WorkflowManager(temp_project)

            workflows = manager.list_local_workflows()
            assert isinstance(workflows, list)
            assert len(workflows) >= 2

    def test_workflow_manager_export_workflow(self, temp_project):
        """Test WorkflowManager.export_workflow method."""
        workflows_dir = temp_project / ".agent" / "workflows"
        workflows_dir.mkdir(parents=True)
        workflow_file = workflows_dir / "test_workflow.md"
        workflow_file.write_text("# Test Workflow")

        with patch("boring.workflow_manager.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = WorkflowManager(temp_project)

            path, message = manager.export_workflow("test_workflow", author="Test Author")
            assert isinstance(path, Path) or path is None
            assert isinstance(message, str)

    def test_workflow_manager_install_workflow_from_file(self, temp_project):
        """Test WorkflowManager.install_workflow from file."""
        metadata = WorkflowMetadata(
            name="test",
            version="1.0.0",
            description="Test",
        )
        package = WorkflowPackage(metadata=metadata, content="# Test")
        package_file = temp_project / "test.bwf.json"
        package_file.write_text(package.to_json())

        with patch("boring.workflow_manager.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = WorkflowManager(temp_project)

            success, message = manager.install_workflow(str(package_file))
            assert isinstance(success, bool)
            assert isinstance(message, str)

    def test_workflow_manager_install_workflow_from_url(self, temp_project):
        """Test WorkflowManager.install_workflow from URL."""
        with patch("boring.workflow_manager.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = WorkflowManager(temp_project)

            with patch.object(
                manager,
                "_fetch_url",
                return_value='{"metadata": {"name": "test", "version": "1.0.0", "description": "Test"}, "content": "# Test"}',
            ):
                success, message = manager.install_workflow("http://example.com/workflow.bwf.json")
                assert isinstance(success, bool)

    def test_workflow_manager_parse_frontmatter(self, temp_project):
        """Test WorkflowManager._parse_frontmatter method."""
        with patch("boring.workflow_manager.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = WorkflowManager(temp_project)

            content = "---\nname: test\nversion: 1.0.0\n---\n# Content"
            frontmatter = manager._parse_frontmatter(content)
            assert isinstance(frontmatter, dict)

    def test_workflow_manager_fetch_url(self, temp_project):
        """Test WorkflowManager._fetch_url method."""
        with patch("boring.workflow_manager.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            manager = WorkflowManager(temp_project)

            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = b"test content"
                mock_response.__enter__.return_value = mock_response
                mock_urlopen.return_value = mock_response

                content = manager._fetch_url("http://example.com/test")
                assert content == "test content"
