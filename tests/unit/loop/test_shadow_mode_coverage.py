from unittest.mock import MagicMock, patch

import pytest

from boring.loop.shadow_mode import (
    OperationSeverity,
    PendingOperation,
    ShadowModeGuard,
    ShadowModeLevel,
    interactive_approval_ui,
)


class TestShadowModeGuard:
    @pytest.fixture
    def temp_dir(self, tmp_path, monkeypatch):
        from boring.core.config import settings

        (tmp_path / ".boring").mkdir(exist_ok=True)
        monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path)
        return tmp_path

    @pytest.fixture
    def guard(self, temp_dir):
        return ShadowModeGuard(temp_dir)

    def test_init_defaults(self, guard, temp_dir):
        assert guard.mode == ShadowModeLevel.ENABLED
        assert guard.pending_file == temp_dir / ".boring_pending_approval.json"
        assert guard.pending_queue == []

    def test_mode_setter_persists(self, guard, temp_dir):
        guard.mode = ShadowModeLevel.STRICT
        assert guard.mode == ShadowModeLevel.STRICT
        mode_file = temp_dir / ".boring_shadow_mode"
        assert mode_file.exists()
        assert mode_file.read_text().strip() == "STRICT"

    def test_load_mode(self, temp_dir):
        mode_file = temp_dir / ".boring_shadow_mode"
        mode_file.write_text("DISABLED")
        guard = ShadowModeGuard(temp_dir)
        assert guard.mode == ShadowModeLevel.DISABLED

    def test_classify_delete(self, guard):
        op = {"name": "delete_file", "args": {"file_path": "test.txt"}}
        pending = guard._classify_operation(op["name"], op["args"])
        assert pending.operation_type == "DELETE"
        assert pending.severity == OperationSeverity.HIGH
        assert pending.file_path == "test.txt"

    def test_classify_sensitive(self, guard):
        op = {"name": "write_file", "args": {"file_path": ".env", "content": "SECRET=123"}}
        pending = guard._classify_operation(op["name"], op["args"])
        assert pending.operation_type == "SENSITIVE_CHANGE"
        assert pending.severity == OperationSeverity.CRITICAL

    def test_classify_shell(self, guard):
        op = {"name": "run_command", "args": {"command": "rm -rf /"}}
        pending = guard._classify_operation(op["name"], op["args"])
        assert pending.operation_type == "SHELL_COMMAND"
        assert pending.severity == OperationSeverity.HIGH

    def test_classify_large_edit(self, guard):
        large_content = "x" * 2000
        op = {"name": "search_replace", "args": {"file_path": "a.py", "search": large_content}}
        pending = guard._classify_operation(op["name"], op["args"])
        assert pending.operation_type == "LARGE_EDIT"
        assert pending.severity == OperationSeverity.MEDIUM

    def test_classify_protected(self, guard):
        op = {"name": "write_file", "args": {"file_path": "/etc/passwd"}}
        pending = guard._classify_operation(op["name"], op["args"])
        assert pending.operation_type == "PROTECTED_PATH"
        assert pending.severity == OperationSeverity.CRITICAL

    def test_check_operation_disabled(self, guard):
        guard.mode = ShadowModeLevel.DISABLED
        op = {"name": "delete_file", "args": {"path": "a.txt"}}
        assert guard.check_operation(op) is None

    def test_check_operation_enabled_low(self, guard):
        guard.mode = ShadowModeLevel.ENABLED
        # write_file is LOW by default if not sensitive/config
        op = {"name": "write_file", "args": {"file_path": "regular.txt", "content": "hello"}}
        assert guard.check_operation(op) is None

    def test_check_operation_enabled_high(self, guard):
        guard.mode = ShadowModeLevel.ENABLED
        op = {"name": "delete_file", "args": {"file_path": "a.txt"}}
        pending = guard.check_operation(op)
        assert pending is not None
        assert pending.severity == OperationSeverity.HIGH

    def test_check_operation_strict(self, guard):
        guard.mode = ShadowModeLevel.STRICT
        op = {"name": "write_file", "args": {"file_path": "regular.txt"}}
        pending = guard.check_operation(op)
        assert pending is not None
        assert pending.severity == OperationSeverity.LOW  # STRICT blocks even LOW

    @patch("boring.loop.shadow_mode._get_trust_manager")
    def test_check_operation_trusted(self, mock_get_trust, guard):
        mock_trust = MagicMock()
        mock_trust.check_trust.return_value = True  # Trusted!
        mock_get_trust.return_value = mock_trust

        op = {"name": "delete_file", "args": {"file_path": "trusted.txt"}}
        assert guard.check_operation(op) is None

    def test_request_approval_callback(self, guard):
        cb = MagicMock(return_value=True)
        guard.approval_callback = cb
        pending = PendingOperation("id1", "TYPE", "path", OperationSeverity.HIGH, "desc", "prev")

        assert guard.request_approval(pending) is True
        cb.assert_called_once_with(pending)

    def test_request_approval_queue(self, guard):
        pending = PendingOperation("id1", "TYPE", "path", OperationSeverity.HIGH, "desc", "prev")
        assert guard.request_approval(pending) is False
        assert len(guard.pending_queue) == 1
        assert guard.pending_file.exists()

    def test_approve_operation(self, guard):
        pending = PendingOperation("id1", "TYPE", "path", OperationSeverity.HIGH, "desc", "prev")
        guard.pending_queue.append(pending)

        assert guard.approve_operation("id1", "looks good") is True
        assert pending.approved is True
        assert pending.approver_note == "looks good"

    def test_reject_operation(self, guard):
        pending = PendingOperation("id1", "TYPE", "path", OperationSeverity.HIGH, "desc", "prev")
        guard.pending_queue.append(pending)

        assert guard.reject_operation("id1", "too risky") is True
        assert len(guard.pending_queue) == 0  # Rejection removes from queue or sets approved=False?
        # Code says: self._remove_pending(operation_id)

    def test_get_pending_operations(self, guard):
        op1 = PendingOperation("1", "T", "P", OperationSeverity.LOW, "D", "V")
        op2 = PendingOperation("2", "T", "P", OperationSeverity.LOW, "D", "V", approved=True)
        guard.pending_queue = [op1, op2]

        pending = guard.get_pending_operations()
        assert len(pending) == 1
        assert pending[0].operation_id == "1"

    def test_clear_pending(self, guard):
        guard.pending_queue = [PendingOperation("1", "T", "P", OperationSeverity.LOW, "D", "V")]
        assert guard.clear_pending() == 1
        assert len(guard.pending_queue) == 0

    def test_safe_preview_redaction(self, guard):
        content = "API_KEY=secret123\nother_config=val"
        preview = guard._safe_preview(content)
        assert "REDACTED" in preview
        assert "secret123" not in preview
        assert "other_config=val" in preview

    @patch("rich.console.Console")
    def test_interactive_approval_ui_yes(self, mock_console_cls, guard):
        mock_console = mock_console_cls.return_value
        mock_console.input.return_value = "y"

        pending = PendingOperation("id1", "TYPE", "path", OperationSeverity.HIGH, "desc", "prev")
        assert interactive_approval_ui(pending) is True

    @patch("rich.console.Console")
    def test_interactive_approval_ui_no(self, mock_console_cls, guard):
        mock_console = mock_console_cls.return_value
        mock_console.input.return_value = "n"

        pending = PendingOperation("id1", "TYPE", "path", OperationSeverity.HIGH, "desc", "prev")
        assert interactive_approval_ui(pending) is False
