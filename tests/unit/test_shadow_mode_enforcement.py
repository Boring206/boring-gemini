"""
Unit tests for Shadow Mode security enforcement.

Tests for:
- STRICT mode blocking all write operations
- Mode persistence across guard re-creation
- ENABLED mode blocking HIGH/CRITICAL only
"""

import pytest

from boring.shadow_mode import (
    OperationSeverity,
    ShadowModeGuard,
    ShadowModeLevel,
    create_shadow_guard,
)


@pytest.fixture
def temp_project(tmp_path, monkeypatch):
    """Create a temporary project directory and patch settings.PROJECT_ROOT."""
    from boring.core.config import settings

    monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path)
    return tmp_path


class TestStrictModeEnforcement:
    """Tests for STRICT mode blocking all write operations."""

    def test_strict_mode_blocks_low_severity_write(self, temp_project):
        """STRICT mode should block even LOW severity writes."""
        guard = ShadowModeGuard(temp_project, mode=ShadowModeLevel.STRICT)

        pending = guard.check_operation(
            {
                "name": "write_file",
                "args": {"file_path": "test.py", "content": "print('hello')"},
            }
        )

        assert pending is not None, "STRICT mode should block LOW severity writes"
        assert pending.severity == OperationSeverity.LOW

    def test_strict_mode_blocks_shell_command(self, temp_project):
        """STRICT mode should block shell commands."""
        guard = ShadowModeGuard(temp_project, mode=ShadowModeLevel.STRICT)

        pending = guard.check_operation(
            {
                "name": "shell",
                "args": {"command": "rm -rf test/"},
            }
        )

        assert pending is not None, "STRICT mode should block shell commands"
        assert pending.severity == OperationSeverity.HIGH

    def test_strict_mode_blocks_search_replace(self, temp_project):
        """STRICT mode should block search/replace operations."""
        guard = ShadowModeGuard(temp_project, mode=ShadowModeLevel.STRICT)

        pending = guard.check_operation(
            {
                "name": "search_replace",
                "args": {"file_path": "main.py", "search": "old", "replace": "new"},
            }
        )

        assert pending is not None, "STRICT mode should block search/replace"


class TestModePersistence:
    """Tests for mode persistence across guard re-creation."""

    def test_mode_persists_to_file(self, temp_project):
        """Setting mode should persist to .boring_shadow_mode file."""
        guard = create_shadow_guard(temp_project, mode="STRICT")
        guard.mode = ShadowModeLevel.STRICT  # Trigger setter

        mode_file = temp_project / ".boring_shadow_mode"
        assert mode_file.exists(), "Mode file should be created"
        assert mode_file.read_text().strip() == "STRICT"

    def test_mode_loads_from_file_on_init(self, temp_project):
        """New guard should load persisted mode from file."""
        # First guard sets STRICT
        guard1 = create_shadow_guard(temp_project, mode="STRICT")
        guard1.mode = ShadowModeLevel.STRICT

        # Second guard should load STRICT from file, not use default
        guard2 = create_shadow_guard(temp_project, mode="ENABLED")
        assert guard2.mode == ShadowModeLevel.STRICT, "Should load persisted STRICT mode"

    def test_mode_persists_across_sessions(self, temp_project):
        """Mode should persist across session simulations."""
        # Session 1: Set to STRICT
        mode_file = temp_project / ".boring_shadow_mode"
        mode_file.write_text("STRICT")

        # Session 2: Create new guard (simulating MCP server restart)
        guard = ShadowModeGuard(temp_project)  # Uses default ENABLED, but should load STRICT
        assert guard.mode == ShadowModeLevel.STRICT


class TestEnabledModeEnforcement:
    """Tests for ENABLED mode blocking HIGH/CRITICAL only."""

    def test_enabled_mode_allows_low_severity(self, temp_project):
        """ENABLED mode should auto-approve LOW severity operations."""
        guard = ShadowModeGuard(temp_project, mode=ShadowModeLevel.ENABLED)

        pending = guard.check_operation(
            {
                "name": "write_file",
                "args": {"file_path": "test.py", "content": "print('hello')"},
            }
        )

        assert pending is None, "ENABLED mode should auto-approve LOW severity"

    def test_enabled_mode_blocks_high_severity(self, temp_project):
        """ENABLED mode should block HIGH severity operations."""
        guard = ShadowModeGuard(temp_project, mode=ShadowModeLevel.ENABLED)

        pending = guard.check_operation(
            {
                "name": "delete_file",
                "args": {"file_path": "important.py"},
            }
        )

        assert pending is not None, "ENABLED mode should block file deletion"
        assert pending.severity == OperationSeverity.HIGH

    def test_enabled_mode_blocks_shell_commands(self, temp_project):
        """ENABLED mode should block shell commands (HIGH severity)."""
        guard = ShadowModeGuard(temp_project, mode=ShadowModeLevel.ENABLED)

        pending = guard.check_operation(
            {
                "name": "run_command",
                "args": {"command": "rm -rf *"},
            }
        )

        assert pending is not None, "ENABLED mode should block shell commands"


class TestDisabledMode:
    """Tests for DISABLED mode auto-approving all operations."""

    def test_disabled_mode_allows_all(self, temp_project):
        """DISABLED mode should auto-approve all operations."""
        guard = ShadowModeGuard(temp_project, mode=ShadowModeLevel.DISABLED)

        # Test file deletion
        pending = guard.check_operation(
            {
                "name": "delete_file",
                "args": {"file_path": "critical.py"},
            }
        )
        assert pending is None, "DISABLED mode should auto-approve deletions"

        # Test shell command
        pending = guard.check_operation(
            {
                "name": "shell",
                "args": {"command": "rm -rf /"},
            }
        )
        assert pending is None, "DISABLED mode should auto-approve shell commands"
