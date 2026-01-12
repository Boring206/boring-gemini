import pytest

from boring.loop.shadow_mode import (
    OperationSeverity,
    ShadowModeGuard,
    ShadowModeLevel,
)


@pytest.fixture
def mock_project_root(tmp_path):
    # Ensure .boring directory exists if needed by implementation
    (tmp_path / ".boring").mkdir(exist_ok=True)
    return tmp_path


@pytest.fixture
def shadow_guard(mock_project_root):
    return ShadowModeGuard(mock_project_root, mode=ShadowModeLevel.ENABLED)


def test_guard_init(shadow_guard, mock_project_root):
    assert shadow_guard.project_root == mock_project_root
    assert shadow_guard.mode == ShadowModeLevel.ENABLED
    assert shadow_guard.pending_file == mock_project_root / ".boring_pending_approval.json"


def test_classify_high_severity(shadow_guard):
    op = {"name": "delete_file", "args": {"file_path": "important.txt"}}
    pending = shadow_guard.check_operation(op)
    assert pending is not None
    assert pending.severity == OperationSeverity.HIGH
    assert pending.operation_type == "DELETE"


def test_classify_low_severity_auto_approve(shadow_guard):
    # ENABLED mode auto-approves LOW
    op = {"name": "write_file", "args": {"file_path": "notes.txt", "content": "hello"}}
    pending = shadow_guard.check_operation(op)
    # WRITE_FILE is usually LOW, but check logic.
    # In shadow_mode.py: WRITE_FILE is LOW.
    # In ENABLED mode, LOW is auto-approved (returns None).
    assert pending is None


def test_classify_sensitive_critical(shadow_guard):
    op = {"name": "write_file", "args": {"file_path": ".env", "content": "SECRET=123"}}
    pending = shadow_guard.check_operation(op)
    assert pending is not None
    assert pending.severity == OperationSeverity.CRITICAL


def test_strict_mode_blocks_all(mock_project_root):
    guard = ShadowModeGuard(mock_project_root, mode=ShadowModeLevel.STRICT)
    op = {"name": "write_file", "args": {"file_path": "notes.txt", "content": "hi"}}
    pending = guard.check_operation(op)
    assert pending is not None  # STRICT blocks everything


def test_approval_workflow(shadow_guard):
    op = {"name": "delete_file", "args": {"file_path": "test.txt"}}
    pending = shadow_guard.check_operation(op)

    assert shadow_guard.request_approval(pending) is False  # Queued
    assert len(shadow_guard.pending_queue) == 1

    op_id = pending.operation_id
    assert shadow_guard.approve_operation(op_id, "Safe") is True

    # Check if approved state is persisted/retrievable
    assert shadow_guard.is_operation_approved(op_id) is True


def test_rejection_workflow(shadow_guard):
    op = {"name": "delete_file", "args": {"file_path": "test.txt"}}
    pending = shadow_guard.check_operation(op)
    shadow_guard.request_approval(pending)

    op_id = pending.operation_id
    assert shadow_guard.reject_operation(op_id, "Unsafe") is True
    # Operation is removed from queue, so it should return None (not found)
    assert shadow_guard.is_operation_approved(op_id) is None
