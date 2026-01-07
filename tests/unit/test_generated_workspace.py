# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.workspace module.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from boring.workspace import Project, WorkspaceManager, get_workspace_manager

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / ".boring"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    (project_dir / "src").mkdir()
    return project_dir


# =============================================================================
# PROJECT DATACLASS TESTS
# =============================================================================


class TestProject:
    """Tests for Project dataclass."""

    def test_project_creation(self, temp_project_dir):
        """Test Project creation."""
        project = Project(
            name="test",
            path=temp_project_dir,
            description="Test project",
            tags=["python", "test"],
        )
        assert project.name == "test"
        assert project.path == temp_project_dir
        assert project.description == "Test project"
        assert project.tags == ["python", "test"]
        assert isinstance(project.added_at, datetime)

    def test_project_to_dict(self, temp_project_dir):
        """Test Project.to_dict method."""
        project = Project(
            name="test",
            path=temp_project_dir,
            description="Test",
            tags=["tag1"],
        )
        project.last_accessed = datetime.now()

        data = project.to_dict()
        assert data["name"] == "test"
        assert data["path"] == str(temp_project_dir)
        assert data["description"] == "Test"
        assert data["tags"] == ["tag1"]
        assert "added_at" in data
        assert "last_accessed" in data

    def test_project_from_dict(self, temp_project_dir):
        """Test Project.from_dict classmethod."""
        data = {
            "name": "test",
            "path": str(temp_project_dir),
            "description": "Test",
            "added_at": datetime.now().isoformat(),
            "last_accessed": None,
            "tags": ["tag1"],
        }

        project = Project.from_dict(data)
        assert project.name == "test"
        assert project.path == temp_project_dir
        assert project.description == "Test"
        assert project.tags == ["tag1"]

    def test_project_from_dict_with_last_accessed(self, temp_project_dir):
        """Test Project.from_dict with last_accessed."""
        data = {
            "name": "test",
            "path": str(temp_project_dir),
            "description": "",
            "added_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "tags": [],
        }

        project = Project.from_dict(data)
        assert project.last_accessed is not None
        assert isinstance(project.last_accessed, datetime)


# =============================================================================
# WORKSPACE MANAGER TESTS
# =============================================================================


class TestWorkspaceManager:
    """Tests for WorkspaceManager class."""

    def test_workspace_manager_init(self, temp_config_dir):
        """Test WorkspaceManager initialization."""
        manager = WorkspaceManager(temp_config_dir)
        assert manager.config_dir == temp_config_dir
        assert manager.config_file == temp_config_dir / "workspace.json"
        assert isinstance(manager.projects, dict)
        assert manager.active_project is None

    def test_workspace_manager_init_default_config(self):
        """Test WorkspaceManager with default config directory."""
        with patch("boring.workspace.Path.home") as mock_home:
            mock_home.return_value = Path("/home/user")
            manager = WorkspaceManager()
            assert ".boring" in str(manager.config_dir)

    def test_workspace_manager_load_nonexistent(self, temp_config_dir):
        """Test loading when config file doesn't exist."""
        manager = WorkspaceManager(temp_config_dir)
        assert len(manager.projects) == 0
        assert manager.active_project is None

    def test_workspace_manager_load_existing(self, temp_config_dir, temp_project_dir):
        """Test loading existing workspace config."""
        config_data = {
            "projects": {
                "test": {
                    "name": "test",
                    "path": str(temp_project_dir),
                    "description": "Test project",
                    "added_at": datetime.now().isoformat(),
                    "last_accessed": None,
                    "tags": [],
                }
            },
            "active_project": "test",
        }
        config_file = temp_config_dir / "workspace.json"
        config_file.write_text(json.dumps(config_data))

        manager = WorkspaceManager(temp_config_dir)
        assert "test" in manager.projects
        assert manager.active_project == "test"

    def test_workspace_manager_load_invalid_json(self, temp_config_dir):
        """Test loading with invalid JSON."""
        config_file = temp_config_dir / "workspace.json"
        config_file.write_text("invalid json{")

        manager = WorkspaceManager(temp_config_dir)
        # Should handle gracefully
        assert len(manager.projects) == 0

    def test_workspace_manager_add_project(self, temp_config_dir, temp_project_dir):
        """Test adding a project."""
        manager = WorkspaceManager(temp_config_dir)
        result = manager.add_project("test", str(temp_project_dir), "Test project")

        assert result["status"] == "SUCCESS"
        assert "test" in manager.projects
        assert manager.projects["test"].name == "test"
        assert manager.projects["test"].path == temp_project_dir

    def test_workspace_manager_add_project_nonexistent_path(self, temp_config_dir):
        """Test adding project with nonexistent path."""
        manager = WorkspaceManager(temp_config_dir)
        result = manager.add_project("test", "/nonexistent/path")

        assert result["status"] == "ERROR"
        assert "does not exist" in result["message"]

    def test_workspace_manager_add_project_duplicate(self, temp_config_dir, temp_project_dir):
        """Test adding duplicate project."""
        manager = WorkspaceManager(temp_config_dir)
        manager.add_project("test", str(temp_project_dir))
        result = manager.add_project("test", str(temp_project_dir))

        assert result["status"] == "ERROR"
        assert "already exists" in result["message"]

    def test_workspace_manager_add_project_with_tags(self, temp_config_dir, temp_project_dir):
        """Test adding project with tags."""
        manager = WorkspaceManager(temp_config_dir)
        result = manager.add_project("test", str(temp_project_dir), tags=["python", "test"])

        assert result["status"] == "SUCCESS"
        assert manager.projects["test"].tags == ["python", "test"]

    def test_workspace_manager_remove_project(self, temp_config_dir, temp_project_dir):
        """Test removing a project."""
        manager = WorkspaceManager(temp_config_dir)
        manager.add_project("test", str(temp_project_dir))
        result = manager.remove_project("test")

        assert result["status"] == "SUCCESS"
        assert "test" not in manager.projects

    def test_workspace_manager_remove_nonexistent(self, temp_config_dir):
        """Test removing nonexistent project."""
        manager = WorkspaceManager(temp_config_dir)
        result = manager.remove_project("nonexistent")

        assert result["status"] == "ERROR"
        assert "not found" in result["message"]

    def test_workspace_manager_remove_active_project(self, temp_config_dir, temp_project_dir):
        """Test removing active project."""
        manager = WorkspaceManager(temp_config_dir)
        manager.add_project("test", str(temp_project_dir))
        manager.switch_project("test")
        result = manager.remove_project("test")

        assert result["status"] == "SUCCESS"
        assert manager.active_project is None

    def test_workspace_manager_switch_project(self, temp_config_dir, temp_project_dir):
        """Test switching project."""
        manager = WorkspaceManager(temp_config_dir)
        manager.add_project("test", str(temp_project_dir))
        result = manager.switch_project("test")

        assert result["status"] == "SUCCESS"
        assert manager.active_project == "test"
        assert manager.projects["test"].last_accessed is not None

    def test_workspace_manager_switch_nonexistent(self, temp_config_dir):
        """Test switching to nonexistent project."""
        manager = WorkspaceManager(temp_config_dir)
        result = manager.switch_project("nonexistent")

        assert result["status"] == "ERROR"
        assert "not found" in result["message"]

    def test_workspace_manager_get_active(self, temp_config_dir, temp_project_dir):
        """Test getting active project."""
        manager = WorkspaceManager(temp_config_dir)
        assert manager.get_active() is None

        manager.add_project("test", str(temp_project_dir))
        manager.switch_project("test")

        active = manager.get_active()
        assert active is not None
        assert active.name == "test"

    def test_workspace_manager_list_projects(self, temp_config_dir, temp_project_dir):
        """Test listing projects."""
        manager = WorkspaceManager(temp_config_dir)
        manager.add_project("test1", str(temp_project_dir))
        manager.add_project("test2", str(temp_project_dir))

        projects = manager.list_projects()
        assert len(projects) == 2
        assert all("name" in p for p in projects)

    def test_workspace_manager_list_projects_by_tag(self, temp_config_dir, temp_project_dir):
        """Test listing projects filtered by tag."""
        manager = WorkspaceManager(temp_config_dir)
        manager.add_project("test1", str(temp_project_dir), tags=["python"])
        manager.add_project("test2", str(temp_project_dir), tags=["javascript"])

        projects = manager.list_projects(tag="python")
        assert len(projects) == 1
        assert projects[0]["name"] == "test1"

    def test_workspace_manager_get_project_path(self, temp_config_dir, temp_project_dir):
        """Test getting project path."""
        manager = WorkspaceManager(temp_config_dir)
        manager.add_project("test", str(temp_project_dir))

        path = manager.get_project_path("test")
        assert path == temp_project_dir

        path = manager.get_project_path()
        assert path is None  # No active project

    def test_workspace_manager_get_project_path_active(self, temp_config_dir, temp_project_dir):
        """Test getting active project path."""
        manager = WorkspaceManager(temp_config_dir)
        manager.add_project("test", str(temp_project_dir))
        manager.switch_project("test")

        path = manager.get_project_path()
        assert path == temp_project_dir

    def test_workspace_manager_save(self, temp_config_dir, temp_project_dir):
        """Test saving workspace config."""
        manager = WorkspaceManager(temp_config_dir)
        manager.add_project("test", str(temp_project_dir))

        assert manager.config_file.exists()
        data = json.loads(manager.config_file.read_text())
        assert "test" in data["projects"]


# =============================================================================
# GET WORKSPACE MANAGER TESTS
# =============================================================================


class TestGetWorkspaceManager:
    """Tests for get_workspace_manager function."""

    def test_get_workspace_manager_singleton(self):
        """Test that get_workspace_manager returns singleton."""
        # Reset global
        import boring.workspace

        boring.workspace._workspace = None

        manager1 = get_workspace_manager()
        manager2 = get_workspace_manager()

        assert manager1 is manager2
