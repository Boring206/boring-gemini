"""
Tests for Progress Persistence Service.
"""

import json

import pytest

from boring.loop.context import LoopContext
from boring.services.progress import ProgressManager


@pytest.fixture
def mock_project_root(tmp_path):
    return tmp_path


@pytest.fixture
def progress_manager(mock_project_root):
    return ProgressManager(mock_project_root)


def test_save_and_load_progress(progress_manager, mock_project_root):
    # Setup context
    ctx = LoopContext(project_root=mock_project_root)
    ctx.loop_count = 5
    ctx.current_task_type = "testing"
    ctx.session_keywords = ["test", "verify"]

    # Save
    success = progress_manager.save_progress(ctx)
    assert success
    assert (mock_project_root / ".boring_progress.json").exists()

    # Load
    data = progress_manager.load_progress()
    assert data is not None
    assert data["loop_count"] == 5
    assert data["current_task_type"] == "testing"
    assert "test" in data["session_keywords"]


def test_restore_context(progress_manager, mock_project_root):
    # Save fake progress
    data = {"loop_count": 10, "current_task_type": "debugging", "session_keywords": ["bug", "fix"]}
    (mock_project_root / ".boring_progress.json").write_text(json.dumps(data))

    # Restore
    ctx = LoopContext(project_root=mock_project_root)
    success = progress_manager.restore_context(ctx)

    assert success
    assert ctx.loop_count == 10
    assert ctx.current_task_type == "debugging"
    assert ctx.session_keywords == ["bug", "fix"]


def test_clear_progress(progress_manager, mock_project_root):
    (mock_project_root / ".boring_progress.json").write_text("{}")
    assert progress_manager.has_progress()

    progress_manager.clear_progress()
    assert not progress_manager.has_progress()
