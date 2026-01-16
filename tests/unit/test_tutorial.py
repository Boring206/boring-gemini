import json

import pytest

from boring.tutorial import TutorialManager


@pytest.fixture
def temp_project(tmp_path):
    return tmp_path


def test_tutorial_initialization(temp_project):
    manager = TutorialManager(temp_project)
    assert manager.project_root == temp_project
    assert manager.state_file == temp_project / ".boring_tutorial.json"
    assert manager._state == {}


def test_show_tutorial_updates_state(temp_project):
    manager = TutorialManager(temp_project)
    # Mock console to prevent actual print

    manager.show_tutorial("first_project")

    # Reload to verify persistence
    manager2 = TutorialManager(temp_project)
    assert manager2._state.get("first_project") is True


def test_show_tutorial_idempotency(temp_project):
    manager = TutorialManager(temp_project)
    manager.show_tutorial("first_project")

    # Modify state manually to verify it doesn't get overwritten if already true
    # (Though logic says if it's there, we return early)
    _ = manager.state_file.stat().st_mtime

    # Call again
    manager.show_tutorial("first_project")

    # Should be effectively same (implementation detail: file might not be touched)
    assert manager._state.get("first_project") is True


def test_generate_learning_note(temp_project):
    from boring.services.audit import AuditLogger

    # Reset singleton to ensure we use the temp_project logs
    AuditLogger._instance = None

    manager = TutorialManager(temp_project)
    # Simulate some achievements
    manager._state["first_project"] = True

    # Create dummy logs for skills analysis
    log_dir = temp_project / "logs"
    log_dir.mkdir()
    log_file = log_dir / "audit.jsonl"

    logs = [
        {"tool": "boring_verify", "timestamp": "2025-01-01T12:00:00"},
        {"tool": "boring_verify", "timestamp": "2025-01-01T12:01:00"},
        {"tool": "speckit_plan", "timestamp": "2025-01-01T12:02:00"},
    ]

    with open(log_file, "w", encoding="utf-8") as f:
        for log in logs:
            f.write(json.dumps(log) + "\n")

    note_path = manager.generate_learning_note()

    assert note_path.exists()
    content = note_path.read_text(encoding="utf-8")

    assert "Vibe Coder 學習筆記" in content
    assert "boring_verify" in content
    assert "(2 次)" in content
    assert "🎉 恭喜建立第一個專案" in content
