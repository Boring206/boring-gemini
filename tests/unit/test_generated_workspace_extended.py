# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Extended unit tests for boring.workspace module.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from boring.workspace import Project, WorkspaceManager, get_workspace_manager

# =============================================================================
# PROJECT DATACLASS TESTS
# =============================================================================


class TestProject:
    """Tests for Project dataclass."""

    def test_project_creation(self):
        """Test Project creation."""
        project = Project(
            name="test_project",
            path=Path("/test/path"),
            description="Test description",
        )
        assert project.name == "test_project"
        assert project.path == Path("/test/path")
        assert project.description == "Test description"

    def test_project_defaults(self):
        """Test Project with default values."""
        project = Project(name="test", path=Path("/test"))
        assert project.description == ""
        assert isinstance(project.added_at, datetime)
        assert project.last_accessed is None
        assert project.tags == []

    def test_project_to_dict(self):
        """Test Project.to_dict method."""
        project = Project(
            name="test",
            path=Path("/test"),
            description="desc",
            tags=["tag1", "tag2"],
        )
        data = project.to_dict()
        assert data["name"] == "test"
        assert Path(data["path"]) == Path("/test")
        assert data["description"] == "desc"
        assert len(data["tags"]) == 2

    def test_project_from_dict(self):
        """Test Project.from_dict method."""
        data = {
            "name": "test",
            "path": "/test/path",
            "description": "desc",
            "added_at": "2024-01-01T00:00:00",
            "last_accessed": "2024-01-02T00:00:00",
            "tags": ["tag1"],
        }
        project = Project.from_dict(data)
        assert project.name == "test"
        assert project.path == Path("/test/path")
        assert project.last_accessed is not None

    def test_project_from_dict_minimal(self):
        """Test Project.from_dict with minimal data."""
        data = {
            "name": "test",
            "path": "/test",
        }
        project = Project.from_dict(data)
        assert project.name == "test"
        assert project.description == ""


# =============================================================================
# WORKSPACE MANAGER TESTS
# =============================================================================


class TestWorkspaceManager:
    """Tests for WorkspaceManager class."""

    def test_workspace_manager_init(self, tmp_path):
        """Test WorkspaceManager initialization."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)
        assert manager.config_dir == config_dir
        assert manager.config_file == config_dir / "workspace.json"
        assert isinstance(manager.projects, dict)

    def test_workspace_manager_init_default(self):
        """Test WorkspaceManager with default config dir."""
        with patch("pathlib.Path.home", return_value=Path("/home/user")):
            manager = WorkspaceManager()
            assert manager.config_dir == Path("/home/user") / ".boring"

    def test_workspace_manager_load_nonexistent(self, tmp_path):
        """Test _load when config file doesn't exist."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)
        assert manager.projects == {}
        assert manager.active_project is None

    def test_workspace_manager_load_existing(self, tmp_path):
        """Test _load with existing config file."""
        config_dir = tmp_path / ".boring"
        config_dir.mkdir()
        config_file = config_dir / "workspace.json"
        config_file.write_text(
            json.dumps(
                {
                    "projects": {
                        "test": {
                            "name": "test",
                            "path": "/test",
                            "description": "",
                            "added_at": "2024-01-01T00:00:00",
                            "last_accessed": None,
                            "tags": [],
                        }
                    },
                    "active_project": "test",
                }
            )
        )

        manager = WorkspaceManager(config_dir)
        assert "test" in manager.projects
        assert manager.active_project == "test"

    def test_workspace_manager_load_invalid_json(self, tmp_path):
        """Test _load with invalid JSON."""
        config_dir = tmp_path / ".boring"
        config_dir.mkdir()
        config_file = config_dir / "workspace.json"
        config_file.write_text("invalid json{")

        manager = WorkspaceManager(config_dir)
        # Should handle gracefully
        assert manager.projects == {}

    def test_workspace_manager_save(self, tmp_path):
        """Test _save method."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)
        manager.projects["test"] = Project(name="test", path=Path("/test"))
        manager._save()

        assert manager.config_file.exists()
        data = json.loads(manager.config_file.read_text())
        assert "test" in data["projects"]

    def test_workspace_manager_add_project(self, tmp_path):
        """Test add_project method."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)
        project_path = tmp_path / "project"
        project_path.mkdir()

        result = manager.add_project("test", str(project_path), "Test project", ["tag1"])
        assert result["status"] == "SUCCESS"
        assert "test" in manager.projects

    def test_workspace_manager_add_project_nonexistent_path(self, tmp_path):
        """Test add_project with nonexistent path."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)

        result = manager.add_project("test", "/nonexistent/path")
        assert result["status"] == "ERROR"
        assert "does not exist" in result["message"]

    def test_workspace_manager_add_project_duplicate(self, tmp_path):
        """Test add_project with duplicate name."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)
        project_path = tmp_path / "project"
        project_path.mkdir()

        manager.add_project("test", str(project_path))
        result = manager.add_project("test", str(project_path))
        assert result["status"] == "ERROR"
        assert "already exists" in result["message"]

    def test_workspace_manager_remove_project(self, tmp_path):
        """Test remove_project method."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)
        project_path = tmp_path / "project"
        project_path.mkdir()

        manager.add_project("test", str(project_path))
        result = manager.remove_project("test")
        assert result["status"] == "SUCCESS"
        assert "test" not in manager.projects

    def test_workspace_manager_remove_project_not_found(self, tmp_path):
        """Test remove_project with nonexistent project."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)

        result = manager.remove_project("nonexistent")
        assert result["status"] == "ERROR"

    def test_workspace_manager_remove_active_project(self, tmp_path):
        """Test remove_project when it's the active project."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)
        project_path = tmp_path / "project"
        project_path.mkdir()

        manager.add_project("test", str(project_path))
        manager.switch_project("test")
        manager.remove_project("test")

        assert manager.active_project is None

    def test_workspace_manager_switch_project(self, tmp_path):
        """Test switch_project method."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)
        project_path = tmp_path / "project"
        project_path.mkdir()

        manager.add_project("test", str(project_path))
        result = manager.switch_project("test")
        assert result["status"] == "SUCCESS"
        assert manager.active_project == "test"

    def test_workspace_manager_switch_project_not_found(self, tmp_path):
        """Test switch_project with nonexistent project."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)

        result = manager.switch_project("nonexistent")
        assert result["status"] == "ERROR"

    def test_workspace_manager_get_active(self, tmp_path):
        """Test get_active method."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)
        project_path = tmp_path / "project"
        project_path.mkdir()

        manager.add_project("test", str(project_path))
        manager.switch_project("test")

        active = manager.get_active()
        assert active is not None
        assert active.name == "test"

    def test_workspace_manager_get_active_none(self, tmp_path):
        """Test get_active when no active project."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)

        active = manager.get_active()
        assert active is None

    def test_workspace_manager_list_projects(self, tmp_path):
        """Test list_projects method."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)
        project_path1 = tmp_path / "project1"
        project_path2 = tmp_path / "project2"
        project_path1.mkdir()
        project_path2.mkdir()

        manager.add_project("test1", str(project_path1), tags=["tag1"])
        manager.add_project("test2", str(project_path2), tags=["tag2"])

        projects = manager.list_projects()
        assert len(projects) == 2

    def test_workspace_manager_list_projects_with_tag(self, tmp_path):
        """Test list_projects with tag filter."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)
        project_path1 = tmp_path / "project1"
        project_path2 = tmp_path / "project2"
        project_path1.mkdir()
        project_path2.mkdir()

        manager.add_project("test1", str(project_path1), tags=["tag1"])
        manager.add_project("test2", str(project_path2), tags=["tag2"])

        projects = manager.list_projects(tag="tag1")
        assert len(projects) == 1
        assert projects[0]["name"] == "test1"

    def test_workspace_manager_get_project_path(self, tmp_path):
        """Test get_project_path method."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)
        project_path = tmp_path / "project"
        project_path.mkdir()

        manager.add_project("test", str(project_path))
        path = manager.get_project_path("test")
        assert path == project_path.resolve()

    def test_workspace_manager_get_project_path_active(self, tmp_path):
        """Test get_project_path with active project."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)
        project_path = tmp_path / "project"
        project_path.mkdir()

        manager.add_project("test", str(project_path))
        manager.switch_project("test")

        path = manager.get_project_path()
        assert path == project_path.resolve()

    def test_workspace_manager_get_project_path_not_found(self, tmp_path):
        """Test get_project_path with nonexistent project."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir)

        path = manager.get_project_path("nonexistent")
        assert path is None


# =============================================================================
# GLOBAL FUNCTION TESTS
# =============================================================================


class TestGetWorkspaceManager:
    """Tests for get_workspace_manager function."""

    def test_get_workspace_manager(self):
        """Test get_workspace_manager function."""
        # Reset global instance
        import boring.workspace

        boring.workspace._workspace = None

        manager = get_workspace_manager()
        assert isinstance(manager, WorkspaceManager)

        # Should return same instance
        manager2 = get_workspace_manager()
        assert manager is manager2
