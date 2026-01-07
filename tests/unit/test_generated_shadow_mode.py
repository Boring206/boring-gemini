"""
Unit tests for shadow_mode.py

Tests Shadow Mode protection system for human-in-the-loop operations.
"""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from boring.shadow_mode import (
    OperationSeverity,
    PendingOperation,
    ShadowModeGuard,
    ShadowModeLevel,
    create_shadow_guard,
    interactive_approval_ui,
)


class TestShadowModeLevel:
    """Test ShadowModeLevel enum."""

    def test_shadow_mode_level_values(self):
        """Test enum values."""
        assert ShadowModeLevel.DISABLED.value == "DISABLED"
        assert ShadowModeLevel.ENABLED.value == "ENABLED"
        assert ShadowModeLevel.STRICT.value == "STRICT"


class TestOperationSeverity:
    """Test OperationSeverity enum."""

    def test_operation_severity_values(self):
        """Test enum values."""
        assert OperationSeverity.LOW.value == "low"
        assert OperationSeverity.MEDIUM.value == "medium"
        assert OperationSeverity.HIGH.value == "high"
        assert OperationSeverity.CRITICAL.value == "critical"


class TestPendingOperation:
    """Test PendingOperation dataclass."""

    def test_pending_operation_creation(self):
        """Test creating a pending operation."""
        op = PendingOperation(
            operation_id="op_1",
            operation_type="WRITE_FILE",
            file_path="test.py",
            severity=OperationSeverity.LOW,
            description="Test operation",
            preview="Preview content",
        )
        assert op.operation_id == "op_1"
        assert op.operation_type == "WRITE_FILE"
        assert op.file_path == "test.py"
        assert op.severity == OperationSeverity.LOW
        assert op.description == "Test operation"
        assert op.preview == "Preview content"
        assert op.approved is None
        assert op.approver_note is None

    def test_pending_operation_to_dict(self):
        """Test converting to dict."""
        op = PendingOperation(
            operation_id="op_1",
            operation_type="WRITE_FILE",
            file_path="test.py",
            severity=OperationSeverity.HIGH,
            description="Test",
            preview="A" * 1000,  # Long preview
        )
        result = op.to_dict()
        assert result["operation_id"] == "op_1"
        assert result["operation_type"] == "WRITE_FILE"
        assert result["file_path"] == "test.py"
        assert result["severity"] == "high"
        assert len(result["preview"]) == 500  # Truncated


class TestShadowModeGuard:
    """Test ShadowModeGuard class."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project directory."""
        return tmp_path / "project"

    @pytest.fixture
    def guard(self, temp_project):
        """Create a ShadowModeGuard instance."""
        temp_project.mkdir()
        return ShadowModeGuard(project_root=temp_project, mode=ShadowModeLevel.ENABLED)

    def test_guard_initialization(self, temp_project):
        """Test guard initialization."""
        guard = ShadowModeGuard(project_root=temp_project, mode=ShadowModeLevel.ENABLED)
        assert guard.project_root == temp_project
        assert guard.mode == ShadowModeLevel.ENABLED
        assert guard.pending_queue == []
        assert guard._operation_counter == 0

    def test_guard_initialization_with_callback(self, temp_project):
        """Test guard initialization with approval callback."""
        callback = Mock(return_value=True)
        guard = ShadowModeGuard(
            project_root=temp_project, mode=ShadowModeLevel.ENABLED, approval_callback=callback
        )
        assert guard.approval_callback == callback

    def test_guard_initialization_with_pending_file(self, temp_project):
        """Test guard initialization with custom pending file."""
        pending_file = temp_project / "custom_pending.json"
        guard = ShadowModeGuard(
            project_root=temp_project, mode=ShadowModeLevel.ENABLED, pending_file=pending_file
        )
        assert guard.pending_file == pending_file

    def test_guard_mode_property(self, guard):
        """Test mode property getter and setter."""
        assert guard.mode == ShadowModeLevel.ENABLED
        guard.mode = ShadowModeLevel.STRICT
        assert guard.mode == ShadowModeLevel.STRICT

    @patch("boring.shadow_mode.logger")
    def test_guard_mode_persistence(self, mock_logger, temp_project):
        """Test mode persistence to disk."""
        # Ensure project directory exists
        temp_project.mkdir(parents=True, exist_ok=True)
        # Initialize guard
        guard = ShadowModeGuard(project_root=temp_project, mode=ShadowModeLevel.ENABLED)
        # Setting mode should create the file
        guard.mode = ShadowModeLevel.STRICT
        mode_file = temp_project / ".boring_shadow_mode"
        assert mode_file.exists()
        assert mode_file.read_text().strip() == "STRICT"

        # Load persisted mode
        guard2 = ShadowModeGuard(project_root=temp_project, mode=ShadowModeLevel.ENABLED)
        assert guard2.mode == ShadowModeLevel.STRICT  # Should load persisted value

    def test_check_operation_disabled_mode(self, guard):
        """Test check_operation in DISABLED mode."""
        guard.mode = ShadowModeLevel.DISABLED
        operation = {"name": "write_file", "args": {"file_path": "test.py", "content": "code"}}
        result = guard.check_operation(operation)
        assert result is None  # Auto-approved

    def test_check_operation_enabled_mode_low_severity(self, guard):
        """Test check_operation in ENABLED mode with LOW severity."""
        operation = {"name": "write_file", "args": {"file_path": "test.py", "content": "code"}}
        result = guard.check_operation(operation)
        assert result is None  # LOW severity auto-approved in ENABLED mode

    def test_check_operation_enabled_mode_high_severity(self, guard):
        """Test check_operation in ENABLED mode with HIGH severity."""
        operation = {"name": "delete_file", "args": {"file_path": "test.py"}}
        result = guard.check_operation(operation)
        assert result is not None
        assert result.severity == OperationSeverity.HIGH

    def test_check_operation_strict_mode(self, guard):
        """Test check_operation in STRICT mode."""
        guard.mode = ShadowModeLevel.STRICT
        operation = {"name": "write_file", "args": {"file_path": "test.py", "content": "code"}}
        result = guard.check_operation(operation)
        assert result is not None  # All writes blocked in STRICT mode

    def test_classify_operation_delete_file(self, guard):
        """Test classifying delete file operation."""
        operation = {"name": "delete_file", "args": {"file_path": "test.py"}}
        result = guard._classify_operation(operation["name"], operation["args"])
        assert result is not None
        assert result.operation_type == "DELETE"
        assert result.severity == OperationSeverity.HIGH

    def test_classify_operation_sensitive_file(self, guard):
        """Test classifying sensitive file operation."""
        operation = {
            "name": "write_file",
            "args": {"file_path": ".env", "content": "API_KEY=secret"},
        }
        result = guard._classify_operation(operation["name"], operation["args"])
        assert result is not None
        assert result.operation_type == "SENSITIVE_CHANGE"
        assert result.severity == OperationSeverity.CRITICAL

    def test_classify_operation_config_file(self, guard):
        """Test classifying config file operation."""
        operation = {
            "name": "write_file",
            "args": {"file_path": "config.yaml", "content": "settings"},
        }
        result = guard._classify_operation(operation["name"], operation["args"])
        assert result is not None
        assert result.operation_type == "CONFIG_CHANGE"
        assert result.severity == OperationSeverity.HIGH

    def test_classify_operation_large_edit(self, guard):
        """Test classifying large edit operation."""
        large_content = "x" * 2000
        operation = {
            "name": "search_replace",
            "args": {"file_path": "test.py", "search": large_content, "replace": "new"},
        }
        result = guard._classify_operation(operation["name"], operation["args"])
        assert result is not None
        assert result.operation_type == "LARGE_EDIT"
        assert result.severity == OperationSeverity.MEDIUM

    def test_classify_operation_shell_command(self, guard):
        """Test classifying shell command operation."""
        operation = {"name": "exec", "args": {"command": "rm -rf /"}}
        result = guard._classify_operation(operation["name"], operation["args"])
        assert result is not None
        assert result.operation_type == "SHELL_COMMAND"
        assert result.severity == OperationSeverity.HIGH

    def test_classify_operation_protected_path(self, guard):
        """Test classifying protected path operation."""
        # Use a protected path that is not a config file
        operation = {
            "name": "write_file",
            "args": {"file_path": "~/.ssh/id_rsa", "content": "data"},
        }
        result = guard._classify_operation(operation["name"], operation["args"])
        assert result is not None
        assert result.operation_type == "PROTECTED_PATH"
        assert result.severity == OperationSeverity.CRITICAL

    def test_classify_operation_write_file(self, guard):
        """Test classifying regular write file operation."""
        operation = {"name": "write_file", "args": {"file_path": "test.py", "content": "code"}}
        result = guard._classify_operation(operation["name"], operation["args"])
        assert result is not None
        assert result.operation_type == "WRITE_FILE"
        assert result.severity == OperationSeverity.LOW

    def test_is_sensitive_file(self, guard):
        """Test _is_sensitive_file method."""
        assert guard._is_sensitive_file(".env") is True
        assert guard._is_sensitive_file("secret.txt") is True
        assert guard._is_sensitive_file("api_key.json") is True
        assert guard._is_sensitive_file("normal.py") is False

    def test_is_config_file(self, guard):
        """Test _is_config_file method."""
        assert guard._is_config_file("config.yaml") is True
        assert guard._is_config_file("settings.json") is True
        assert guard._is_config_file("pyproject.toml") is True
        assert guard._is_config_file("normal.py") is False

    def test_is_protected_path(self, guard):
        """Test _is_protected_path method."""
        assert guard._is_protected_path(".git/config") is True
        assert guard._is_protected_path("~/.ssh/id_rsa") is True
        assert guard._is_protected_path("/etc/passwd") is True
        assert guard._is_protected_path("normal.py") is False

    def test_safe_preview(self, guard):
        """Test _safe_preview method."""
        content = "password=secret123"
        preview = guard._safe_preview(content)
        assert "[REDACTED]" in preview

        long_content = "x" * 500
        preview = guard._safe_preview(long_content, max_len=100)
        assert len(preview) <= 103  # 100 + "..."

    def test_request_approval_with_callback(self, guard):
        """Test request_approval with callback."""
        callback = Mock(return_value=True)
        guard.approval_callback = callback
        pending = PendingOperation(
            operation_id="op_1",
            operation_type="WRITE_FILE",
            file_path="test.py",
            severity=OperationSeverity.HIGH,
            description="Test",
            preview="Preview",
        )
        result = guard.request_approval(pending)
        assert result is True
        callback.assert_called_once_with(pending)

    def test_request_approval_without_callback(self, guard):
        """Test request_approval without callback (queues operation)."""
        pending = PendingOperation(
            operation_id="op_1",
            operation_type="WRITE_FILE",
            file_path="test.py",
            severity=OperationSeverity.HIGH,
            description="Test",
            preview="Preview",
        )
        result = guard.request_approval(pending)
        assert result is False
        assert len(guard.pending_queue) == 1
        assert guard.pending_queue[0] == pending

    def test_request_approval_callback_exception(self, guard):
        """Test request_approval when callback raises exception."""
        callback = Mock(side_effect=Exception("Callback error"))
        guard.approval_callback = callback
        pending = PendingOperation(
            operation_id="op_1",
            operation_type="WRITE_FILE",
            file_path="test.py",
            severity=OperationSeverity.HIGH,
            description="Test",
            preview="Preview",
        )
        result = guard.request_approval(pending)
        assert result is False  # Falls back to queue

    def test_approve_operation(self, guard):
        """Test approve_operation method."""
        pending = PendingOperation(
            operation_id="op_1",
            operation_type="WRITE_FILE",
            file_path="test.py",
            severity=OperationSeverity.HIGH,
            description="Test",
            preview="Preview",
        )
        guard.pending_queue.append(pending)
        result = guard.approve_operation("op_1", note="Approved")
        assert result is True
        assert pending.approved is True
        assert pending.approver_note == "Approved"

    def test_approve_operation_not_found(self, guard):
        """Test approve_operation with non-existent ID."""
        result = guard.approve_operation("nonexistent")
        assert result is False

    def test_reject_operation(self, guard):
        """Test reject_operation method."""
        pending = PendingOperation(
            operation_id="op_1",
            operation_type="WRITE_FILE",
            file_path="test.py",
            severity=OperationSeverity.HIGH,
            description="Test",
            preview="Preview",
        )
        guard.pending_queue.append(pending)
        result = guard.reject_operation("op_1", note="Rejected")
        assert result is True
        assert pending.approved is False
        assert pending.approver_note == "Rejected"
        assert "op_1" not in [op.operation_id for op in guard.pending_queue]

    def test_reject_operation_not_found(self, guard):
        """Test reject_operation with non-existent ID."""
        result = guard.reject_operation("nonexistent")
        assert result is False

    def test_get_pending_operations(self, guard):
        """Test get_pending_operations method."""
        pending1 = PendingOperation(
            operation_id="op_1",
            operation_type="WRITE_FILE",
            file_path="test.py",
            severity=OperationSeverity.HIGH,
            description="Test",
            preview="Preview",
        )
        pending2 = PendingOperation(
            operation_id="op_2",
            operation_type="DELETE",
            file_path="test2.py",
            severity=OperationSeverity.HIGH,
            description="Test",
            preview="Preview",
            approved=True,
        )
        guard.pending_queue = [pending1, pending2]
        result = guard.get_pending_operations()
        assert len(result) == 1
        assert result[0].operation_id == "op_1"

    def test_clear_pending(self, guard):
        """Test clear_pending method."""
        pending1 = PendingOperation(
            operation_id="op_1",
            operation_type="WRITE_FILE",
            file_path="test.py",
            severity=OperationSeverity.HIGH,
            description="Test",
            preview="Preview",
        )
        guard.pending_queue = [pending1]
        count = guard.clear_pending()
        assert count == 1
        assert len(guard.pending_queue) == 0

    def test_is_operation_approved(self, guard):
        """Test is_operation_approved method."""
        pending1 = PendingOperation(
            operation_id="op_1",
            operation_type="WRITE_FILE",
            file_path="test.py",
            severity=OperationSeverity.HIGH,
            description="Test",
            preview="Preview",
            approved=True,
        )
        pending2 = PendingOperation(
            operation_id="op_2",
            operation_type="DELETE",
            file_path="test2.py",
            severity=OperationSeverity.HIGH,
            description="Test",
            preview="Preview",
            approved=False,
        )
        guard.pending_queue = [pending1, pending2]
        assert guard.is_operation_approved("op_1") is True
        assert guard.is_operation_approved("op_2") is False
        assert guard.is_operation_approved("op_3") is None

    def test_load_pending(self, temp_project):
        """Test loading pending operations from file."""
        temp_project.mkdir(parents=True, exist_ok=True)
        pending_file = temp_project / ".boring_pending_approval.json"
        data = [
            {
                "operation_id": "op_1",
                "operation_type": "WRITE_FILE",
                "file_path": "test.py",
                "severity": "high",
                "description": "Test",
                "preview": "Preview",
                "approved": None,
            }
        ]
        pending_file.write_text(json.dumps(data))
        guard = ShadowModeGuard(project_root=temp_project)
        assert len(guard.pending_queue) == 1
        assert guard.pending_queue[0].operation_id == "op_1"

    def test_load_pending_invalid_json(self, temp_project):
        """Test loading pending operations with invalid JSON."""
        temp_project.mkdir(parents=True, exist_ok=True)
        pending_file = temp_project / ".boring_pending_approval.json"
        pending_file.write_text("invalid json")
        guard = ShadowModeGuard(project_root=temp_project)
        assert len(guard.pending_queue) == 0  # Should handle gracefully

    def test_save_pending(self, guard, temp_project):
        """Test saving pending operations to file."""
        pending = PendingOperation(
            operation_id="op_1",
            operation_type="WRITE_FILE",
            file_path="test.py",
            severity=OperationSeverity.HIGH,
            description="Test",
            preview="Preview",
        )
        guard.pending_queue.append(pending)
        guard._save_pending()
        assert guard.pending_file.exists()
        data = json.loads(guard.pending_file.read_text())
        assert len(data) == 1
        assert data[0]["operation_id"] == "op_1"

    def test_load_mode(self, temp_project):
        """Test loading persisted mode."""
        temp_project.mkdir(parents=True, exist_ok=True)
        mode_file = temp_project / ".boring_shadow_mode"
        mode_file.write_text("STRICT")
        guard = ShadowModeGuard(project_root=temp_project, mode=ShadowModeLevel.ENABLED)
        assert guard.mode == ShadowModeLevel.STRICT

    def test_load_mode_invalid(self, temp_project):
        """Test loading invalid persisted mode."""
        temp_project.mkdir(parents=True, exist_ok=True)
        mode_file = temp_project / ".boring_shadow_mode"
        mode_file.write_text("INVALID")
        guard = ShadowModeGuard(project_root=temp_project, mode=ShadowModeLevel.ENABLED)
        assert guard.mode == ShadowModeLevel.ENABLED  # Should use default


class TestInteractiveApprovalUI:
    """Test interactive_approval_ui function."""

    def test_interactive_approval_ui_with_rich(self):
        """Test interactive approval UI with Rich available."""
        pending = PendingOperation(
            operation_id="op_1",
            operation_type="WRITE_FILE",
            file_path="test.py",
            severity=OperationSeverity.HIGH,
            description="Test",
            preview="Preview content",
        )
        with patch("rich.console.Console") as mock_console_class:
            mock_console = MagicMock()
            mock_console_class.return_value = mock_console
            mock_console.input.return_value = "y"
            result = interactive_approval_ui(pending)
            assert result is True
            mock_console.print.assert_called()
            mock_console.input.assert_called()

    def test_interactive_approval_ui_without_rich(self):
        """Test interactive approval UI without Rich (fallback)."""
        pending = PendingOperation(
            operation_id="op_1",
            operation_type="WRITE_FILE",
            file_path="test.py",
            severity=OperationSeverity.HIGH,
            description="Test",
            preview="Preview",
        )
        with patch("rich.console.Console", side_effect=ImportError):
            with patch("builtins.input", return_value="yes"):
                result = interactive_approval_ui(pending)
                assert result is True

    def test_interactive_approval_ui_reject(self):
        """Test interactive approval UI rejection."""
        pending = PendingOperation(
            operation_id="op_1",
            operation_type="WRITE_FILE",
            file_path="test.py",
            severity=OperationSeverity.HIGH,
            description="Test",
            preview="Preview",
        )
        with patch("rich.console.Console", side_effect=ImportError):
            with patch("builtins.input", return_value="n"):
                result = interactive_approval_ui(pending)
                assert result is False


class TestCreateShadowGuard:
    """Test create_shadow_guard function."""

    def test_create_shadow_guard_enabled(self, tmp_path):
        """Test creating guard with ENABLED mode."""
        guard = create_shadow_guard(project_root=tmp_path, mode="ENABLED")
        assert guard.mode == ShadowModeLevel.ENABLED
        assert guard.approval_callback is None

    def test_create_shadow_guard_strict(self, tmp_path):
        """Test creating guard with STRICT mode."""
        guard = create_shadow_guard(project_root=tmp_path, mode="STRICT")
        assert guard.mode == ShadowModeLevel.STRICT

    def test_create_shadow_guard_disabled(self, tmp_path):
        """Test creating guard with DISABLED mode."""
        guard = create_shadow_guard(project_root=tmp_path, mode="DISABLED")
        assert guard.mode == ShadowModeLevel.DISABLED

    def test_create_shadow_guard_invalid_mode(self, tmp_path):
        """Test creating guard with invalid mode (defaults to ENABLED)."""
        guard = create_shadow_guard(project_root=tmp_path, mode="INVALID")
        assert guard.mode == ShadowModeLevel.ENABLED

    def test_create_shadow_guard_interactive(self, tmp_path):
        """Test creating guard with interactive mode."""
        guard = create_shadow_guard(project_root=tmp_path, mode="ENABLED", interactive=True)
        assert guard.approval_callback is not None
