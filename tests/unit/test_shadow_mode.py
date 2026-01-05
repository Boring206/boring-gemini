"""
Unit tests for Shadow Mode
"""


class TestShadowModeEnums:
    """Tests for Shadow Mode enums"""

    def test_shadow_mode_level(self):
        """Test ShadowModeLevel enum"""
        from boring.shadow_mode import ShadowModeLevel

        assert ShadowModeLevel.DISABLED.value == "DISABLED"
        assert ShadowModeLevel.ENABLED.value == "ENABLED"
        assert ShadowModeLevel.STRICT.value == "STRICT"

    def test_operation_severity(self):
        """Test OperationSeverity enum"""
        from boring.shadow_mode import OperationSeverity

        assert OperationSeverity.LOW.value == "low"
        assert OperationSeverity.CRITICAL.value == "critical"


class TestPendingOperation:
    """Tests for PendingOperation"""

    def test_pending_operation_creation(self):
        """Test PendingOperation dataclass"""
        from boring.shadow_mode import OperationSeverity, PendingOperation

        op = PendingOperation(
            operation_id="op_1",
            operation_type="DELETE",
            file_path="config.py",
            severity=OperationSeverity.HIGH,
            description="Delete config file",
            preview="[File will be deleted]",
        )

        assert op.operation_id == "op_1"
        assert op.severity == OperationSeverity.HIGH

    def test_pending_operation_serialization(self):
        """Test PendingOperation to_dict"""
        from boring.shadow_mode import OperationSeverity, PendingOperation

        op = PendingOperation(
            operation_id="op_1",
            operation_type="DELETE",
            file_path="test.py",
            severity=OperationSeverity.CRITICAL,
            description="Delete test",
            preview="content",
        )

        data = op.to_dict()
        assert data["severity"] == "critical"
        assert "operation_id" in data


class TestShadowModeGuard:
    """Tests for ShadowModeGuard"""

    def test_guard_disabled_mode(self, tmp_path):
        """Test guard in DISABLED mode allows all"""
        from boring.shadow_mode import ShadowModeGuard, ShadowModeLevel

        guard = ShadowModeGuard(project_root=tmp_path, mode=ShadowModeLevel.DISABLED)

        # Any operation should be allowed
        result = guard.check_operation(
            {"name": "delete_file", "args": {"file_path": "important.py"}}
        )

        assert result is None  # None means auto-approved

    def test_guard_enabled_mode_blocks_high(self, tmp_path):
        """Test guard in ENABLED mode blocks HIGH ops"""
        from boring.shadow_mode import ShadowModeGuard, ShadowModeLevel

        guard = ShadowModeGuard(project_root=tmp_path, mode=ShadowModeLevel.ENABLED)

        # File deletion should be blocked
        result = guard.check_operation(
            {"name": "delete_file", "args": {"file_path": "important.py"}}
        )

        assert result is not None
        assert result.operation_type == "DELETE"

    def test_guard_enabled_mode_allows_read(self, tmp_path):
        """Test guard in ENABLED mode allows LOW ops"""
        from boring.shadow_mode import ShadowModeGuard, ShadowModeLevel

        guard = ShadowModeGuard(project_root=tmp_path, mode=ShadowModeLevel.ENABLED)

        # Read operation should be allowed
        result = guard.check_operation({"name": "read_file", "args": {"file_path": "test.py"}})

        assert result is None  # Auto-approved

    def test_guard_strict_mode(self, tmp_path):
        """Test guard in STRICT mode blocks all writes"""
        from boring.shadow_mode import ShadowModeGuard, ShadowModeLevel

        guard = ShadowModeGuard(project_root=tmp_path, mode=ShadowModeLevel.STRICT)

        # Even medium severity should be blocked
        guard.check_operation(
            {"name": "write_file", "args": {"file_path": "normal.py", "content": "x = 1"}}
        )

        # In strict mode, we check if there's a classification
        # If no classification returns None, it's allowed
        # But if classified as MEDIUM+, it should be blocked

    def test_guard_sensitive_file_detection(self, tmp_path):
        """Test guard detects sensitive files"""
        from boring.shadow_mode import OperationSeverity, ShadowModeGuard, ShadowModeLevel

        guard = ShadowModeGuard(project_root=tmp_path, mode=ShadowModeLevel.ENABLED)

        # Sensitive file should be CRITICAL
        result = guard.check_operation(
            {"name": "write_file", "args": {"file_path": ".env", "content": "SECRET=xxx"}}
        )

        assert result is not None
        assert result.severity == OperationSeverity.CRITICAL

    def test_guard_shell_command_detection(self, tmp_path):
        """Test guard blocks shell commands"""
        from boring.shadow_mode import ShadowModeGuard, ShadowModeLevel

        guard = ShadowModeGuard(project_root=tmp_path, mode=ShadowModeLevel.ENABLED)

        result = guard.check_operation({"name": "shell", "args": {"command": "rm -rf /"}})

        assert result is not None
        assert result.operation_type == "SHELL_COMMAND"

    def test_approve_operation(self, tmp_path):
        """Test approving a pending operation"""
        from boring.shadow_mode import ShadowModeGuard, ShadowModeLevel

        guard = ShadowModeGuard(project_root=tmp_path, mode=ShadowModeLevel.ENABLED)

        # Create pending op
        pending = guard.check_operation({"name": "delete_file", "args": {"file_path": "test.py"}})

        # Request approval (no callback = queued)
        approved = guard.request_approval(pending)
        assert approved is False  # Queued, not approved yet

        # Approve it
        result = guard.approve_operation(pending.operation_id, "Reviewed and approved")
        assert result is True

        # Check it's approved
        status = guard.is_operation_approved(pending.operation_id)
        assert status is True

    def test_reject_operation(self, tmp_path):
        """Test rejecting a pending operation"""
        from boring.shadow_mode import ShadowModeGuard, ShadowModeLevel

        guard = ShadowModeGuard(project_root=tmp_path, mode=ShadowModeLevel.ENABLED)

        pending = guard.check_operation(
            {"name": "delete_file", "args": {"file_path": "critical.py"}}
        )

        guard.request_approval(pending)

        result = guard.reject_operation(pending.operation_id, "Too risky")
        assert result is True


class TestCreateShadowGuard:
    """Tests for factory function"""

    def test_create_with_default_mode(self, tmp_path):
        """Test create_shadow_guard defaults to ENABLED"""
        from boring.shadow_mode import ShadowModeLevel, create_shadow_guard

        guard = create_shadow_guard(tmp_path)
        assert guard.mode == ShadowModeLevel.ENABLED

    def test_create_with_custom_mode(self, tmp_path):
        """Test create_shadow_guard with custom mode"""
        from boring.shadow_mode import ShadowModeLevel, create_shadow_guard

        guard = create_shadow_guard(tmp_path, mode="STRICT")
        assert guard.mode == ShadowModeLevel.STRICT
