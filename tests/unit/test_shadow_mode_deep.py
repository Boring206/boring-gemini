from unittest.mock import MagicMock, patch

import pytest

from boring.loop.shadow_mode import (
    OperationSeverity,
    PendingOperation,
    ShadowModeGuard,
    ShadowModeLevel,
    create_shadow_guard,
    interactive_approval_ui,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure."""
    (tmp_path / "src").mkdir()
    # No pre-existing mode file to avoid confusion
    return tmp_path


@pytest.fixture(autouse=True)
def reset_globals():
    """Reset global state between tests."""
    from boring import trust_rules
    from boring.loop import shadow_mode

    shadow_mode._trust_manager = None
    trust_rules._managers = {}


class TestShadowModeDeep:
    """Deep tests for Shadow Mode logic and edge cases."""

    def test_mode_persistence(self, tmp_path):
        # Use tmp_path directly to eliminate fixture complexity
        guard = ShadowModeGuard(tmp_path)
        assert guard.mode == ShadowModeLevel.ENABLED  # Default

        guard.mode = ShadowModeLevel.STRICT
        # Verify file exists and content
        p = tmp_path / ".boring_shadow_mode"
        assert p.exists()
        assert p.read_text().strip() == "STRICT"

        # Load again in new instance
        guard2 = ShadowModeGuard(tmp_path)
        assert guard2.mode == ShadowModeLevel.STRICT

    def test_classify_delete(self, temp_project):
        guard = ShadowModeGuard(temp_project)
        pending = guard.check_operation({"name": "delete_file", "args": {"file_path": "danger.py"}})
        assert pending is not None
        assert pending.operation_type == "DELETE"
        assert pending.severity == OperationSeverity.HIGH

    def test_classify_sensitive(self, temp_project):
        guard = ShadowModeGuard(temp_project)
        # .env is sensitive
        pending = guard.check_operation(
            {"name": "write_file", "args": {"file_path": ".env", "content": "KEY=VALUE"}}
        )
        assert pending is not None
        assert pending.operation_type == "SENSITIVE_CHANGE"
        assert pending.severity == OperationSeverity.CRITICAL

    def test_classify_config(self, temp_project):
        guard = ShadowModeGuard(temp_project)
        pending = guard.check_operation(
            {"name": "search_replace", "args": {"file_path": "pyproject.toml", "replace": "new"}}
        )
        assert pending is not None
        assert pending.operation_type == "CONFIG_CHANGE"
        assert pending.severity == OperationSeverity.HIGH

    def test_classify_shell(self, temp_project):
        guard = ShadowModeGuard(temp_project)
        pending = guard.check_operation({"name": "run_command", "args": {"command": "rm -rf /"}})
        assert pending is not None
        assert pending.operation_type == "SHELL_COMMAND"
        assert pending.severity == OperationSeverity.HIGH

    def test_classify_large_edit(self, temp_project):
        guard = ShadowModeGuard(temp_project)
        guard.mode = ShadowModeLevel.STRICT
        large_content = "line\n" * 50
        pending = guard.check_operation(
            {"name": "search_replace", "args": {"file_path": "test.py", "search": large_content}}
        )
        assert pending is not None
        assert pending.operation_type == "LARGE_EDIT"
        assert pending.severity == OperationSeverity.MEDIUM

    def test_classify_protected_path(self, temp_project):
        guard = ShadowModeGuard(temp_project)
        pending = guard.check_operation(
            {"name": "write_file", "args": {"file_path": "/etc/passwd"}}
        )
        assert pending is not None
        assert pending.operation_type == "PROTECTED_PATH"
        assert pending.severity == OperationSeverity.CRITICAL

    def test_trust_rule_bypass(self, temp_project):
        with patch("boring.loop.shadow_mode._get_trust_manager") as mock_get:
            mock_trust = MagicMock()
            mock_trust.check_trust.return_value = {"rule": "allow_all"}
            mock_get.return_value = mock_trust

            guard = ShadowModeGuard(temp_project)
            # Should be blocked normally
            pending = guard.check_operation(
                {"name": "delete_file", "args": {"file_path": "test.py"}}
            )
            assert pending is None  # Auto-approved by trust rule

    def test_approval_flow(self, temp_project):
        callback_mock = MagicMock(return_value=True)
        guard = ShadowModeGuard(temp_project, approval_callback=callback_mock)

        pending = guard.check_operation({"name": "delete_file", "args": {"file_path": "test.py"}})
        assert pending is not None

        # Test request_approval using callback
        result = guard.request_approval(pending)
        assert result is True
        callback_mock.assert_called_once_with(pending)

    def test_rejection_flow(self, temp_project):
        guard = ShadowModeGuard(temp_project)
        guard.mode = ShadowModeLevel.STRICT
        pending = guard.check_operation({"name": "delete_file", "args": {"file_path": "test.py"}})

        # Test queue fall back
        result = guard.request_approval(pending)
        assert result is False
        assert len(guard.pending_queue) == 1

        op_id = pending.operation_id
        assert guard.is_operation_approved(op_id) is None

        # Approve manually
        guard.approve_operation(op_id, note="Proceed")
        assert guard.is_operation_approved(op_id) is True

        # Reject another
        pending2 = guard.check_operation({"name": "rm", "args": {"path": "tmp"}})
        guard.request_approval(pending2)
        guard.reject_operation(pending2.operation_id, note="Reason")
        # get_pending_operations returns approved is None.
        # The approved one is approved=True, the rejected one is removed.
        assert len(guard.get_pending_operations()) == 0

    def test_clear_pending(self, temp_project):
        guard = ShadowModeGuard(temp_project)
        guard.mode = ShadowModeLevel.STRICT
        pending = guard.check_operation({"name": "rm", "args": {"path": "tmp"}})
        guard.request_approval(pending)
        assert len(guard.pending_queue) == 1
        guard.clear_pending()
        assert len(guard.pending_queue) == 0

    def test_safe_preview_redaction(self, temp_project):
        guard = ShadowModeGuard(temp_project)
        secret_content = "GITHUB_TOKEN=ghp_123456789\npassword: 'mypassword'"
        preview = guard._safe_preview(secret_content)
        assert "REDACTED" in preview
        assert "ghp_123456789" not in preview
        assert "mypassword" not in preview

    def test_load_pending_error_handling(self, temp_project):
        pending_file = temp_project / ".boring_pending_approval.json"
        pending_file.write_text("invalid json")
        # Should not crash
        guard = ShadowModeGuard(temp_project, pending_file=pending_file)
        assert guard.pending_queue == []

    @patch("rich.console.Console")
    def test_interactive_approval_ui_rich(self, mock_console_class):
        mock_console = mock_console_class.return_value
        mock_console.input.return_value = "y"

        pending = PendingOperation("id", "type", "path", OperationSeverity.HIGH, "desc", "prev")
        result = interactive_approval_ui(pending)
        assert result is True

    @patch("builtins.input", return_value="n")
    def test_interactive_approval_ui_fallback(self, mock_input):
        # Force ImportError for rich
        with patch.dict("sys.modules", {"rich.console": None}):
            pending = PendingOperation("id", "type", "path", OperationSeverity.HIGH, "desc", "prev")
            result = interactive_approval_ui(pending)
            assert result is False

    def test_create_shadow_guard_factory(self, temp_project):
        guard = create_shadow_guard(temp_project, mode="STRICT", interactive=False)
        assert guard.mode == ShadowModeLevel.STRICT
        assert guard.approval_callback is None

        guard2 = create_shadow_guard(temp_project, mode="INVALID")
        assert guard2.mode == ShadowModeLevel.ENABLED
