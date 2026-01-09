# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Enhanced unit tests for Workspace Manager.
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from boring.workspace import WorkspaceManager, Project, get_workspace_manager

@pytest.fixture
def workspace():
    with TemporaryDirectory() as tmp_dir:
        config_dir = Path(tmp_dir)
        # Reset global instance for testing
        import boring.workspace as ws
        ws._workspace = None
        yield WorkspaceManager(config_dir=config_dir)

def test_project_serialization():
    path = Path("/tmp/proj")
    proj = Project(name="test", path=path, description="desc", tags=["tag1"])
    data = proj.to_dict()
    assert data["name"] == "test"
    assert data["path"] == str(path)
    
    new_proj = Project.from_dict(data)
    assert new_proj.name == "test"
    assert new_proj.path == path
    assert new_proj.tags == ["tag1"]

def test_workspace_add_project(workspace):
    with TemporaryDirectory() as proj_dir:
        proj_path = Path(proj_dir)
        result = workspace.add_project("p1", str(proj_path), "desc", ["t1"])
        assert result["status"] == "SUCCESS"
        assert "p1" in workspace.projects
        assert workspace.projects["p1"].description == "desc"

def test_workspace_add_nonexistent_path(workspace):
    result = workspace.add_project("p1", "/nonexistent/path/xyz")
    assert result["status"] == "ERROR"
    assert "not exist" in result["message"]

def test_workspace_remove_project(workspace):
    with TemporaryDirectory() as proj_dir:
        workspace.add_project("p1", proj_dir)
        workspace.switch_project("p1")
        assert workspace.active_project == "p1"
        
        result = workspace.remove_project("p1")
        assert result["status"] == "SUCCESS"
        assert "p1" not in workspace.projects
        assert workspace.active_project is None

def test_workspace_switch_project(workspace):
    with TemporaryDirectory() as p1_dir, TemporaryDirectory() as p2_dir:
        workspace.add_project("p1", p1_dir)
        workspace.add_project("p2", p2_dir)
        
        workspace.switch_project("p1")
        assert workspace.active_project == "p1"
        assert workspace.get_active().name == "p1"
        
        workspace.switch_project("p2")
        assert workspace.active_project == "p2"
        assert workspace.get_active().name == "p2"

def test_workspace_list_projects(workspace):
    with TemporaryDirectory() as p1_dir, TemporaryDirectory() as p2_dir:
        workspace.add_project("p1", p1_dir, tags=["web"])
        workspace.add_project("p2", p2_dir, tags=["api"])
        
        all_projs = workspace.list_projects()
        assert len(all_projs) == 2
        
        web_projs = workspace.list_projects(tag="web")
        assert len(web_projs) == 1
        assert web_projs[0]["name"] == "p1"

def test_workspace_persistence(workspace):
    config_dir = workspace.config_dir
    with TemporaryDirectory() as proj_dir:
        workspace.add_project("p1", proj_dir)
        workspace.switch_project("p1")
        workspace.flush()
        
        # New manager should load existing data
        new_ws = WorkspaceManager(config_dir=config_dir)
        assert "p1" in new_ws.projects
        assert new_ws.active_project == "p1"

def test_workspace_get_project_path(workspace):
    with TemporaryDirectory() as proj_dir:
        workspace.add_project("p1", proj_dir)
        assert workspace.get_project_path("p1") == Path(proj_dir).resolve()
        
        workspace.switch_project("p1")
        assert workspace.get_project_path() == Path(proj_dir).resolve()
        assert workspace.get_project_path("nonexistent") is None
