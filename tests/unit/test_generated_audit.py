"""
Unit tests for boring.audit module.

Tests the AuditLogger class and audited decorator for MCP tool invocation logging.
"""

import json
import time
from unittest.mock import patch

import pytest

from boring.audit import AuditLogger, audited


@pytest.fixture(autouse=True)
def reset_audit_logger_singleton():
    """Reset AuditLogger singleton before each test."""
    AuditLogger._instance = None
    yield
    AuditLogger._instance = None


class TestAuditLogger:
    """Test AuditLogger class."""

    def test_audit_logger_initialization(self, tmp_path):
        """Test AuditLogger initialization."""
        log_dir = tmp_path / "logs"
        logger = AuditLogger(log_dir)

        assert logger.log_dir == log_dir
        assert logger.log_file == log_dir / "audit.jsonl"
        assert logger._enabled is True
        assert log_dir.exists()

    def test_audit_logger_get_instance_singleton(self, tmp_path):
        """Test that get_instance returns singleton."""
        log_dir = tmp_path / "logs"
        logger1 = AuditLogger.get_instance(log_dir)
        logger2 = AuditLogger.get_instance()

        assert logger1 is logger2
        assert logger1.log_dir == log_dir

    def test_audit_logger_get_instance_default_dir(self, tmp_path):
        """Test get_instance with default log directory."""
        # Use a real tmp directory since Path.cwd() patching is complex
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            logger = AuditLogger.get_instance()
            assert logger.log_dir == tmp_path / "logs"
        finally:
            os.chdir(original_cwd)

    def test_audit_logger_enable_disable(self, tmp_path):
        """Test enable and disable methods."""
        logger = AuditLogger(tmp_path / "logs")
        assert logger._enabled is True

        logger.disable()
        assert logger._enabled is False

        logger.enable()
        assert logger._enabled is True

    def test_audit_logger_log_when_disabled(self, tmp_path):
        """Test that log doesn't write when disabled."""
        logger = AuditLogger(tmp_path / "logs")
        logger.disable()

        logger.log("test_tool", {"arg1": "value1"}, {"status": "OK"}, 100, "/project")

        assert not logger.log_file.exists()

    def test_audit_logger_log_writes_entry(self, tmp_path):
        """Test that log writes correct entry."""
        logger = AuditLogger(tmp_path / "logs")

        logger.log(
            tool_name="test_tool",
            args={"arg1": "value1", "arg2": 42},
            result={"status": "SUCCESS", "value": "result"},
            duration_ms=150,
            project_root="/project/root",
        )

        assert logger.log_file.exists()
        content = logger.log_file.read_text(encoding="utf-8")
        entry = json.loads(content.strip())

        assert entry["tool"] == "test_tool"
        assert entry["args"]["arg1"] == "value1"
        assert entry["args"]["arg2"] == 42
        assert entry["result_status"] == "SUCCESS"
        assert entry["duration_ms"] == 150
        assert entry["project_root"] == "/project/root"
        assert "timestamp" in entry

    def test_audit_logger_log_sanitizes_sensitive_args(self, tmp_path):
        """Test that log sanitizes sensitive arguments."""
        logger = AuditLogger(tmp_path / "logs")

        logger.log(
            tool_name="test_tool",
            args={"token": "secret123", "password": "pass", "api_key": "key", "normal": "value"},
            result={"status": "OK"},
            duration_ms=100,
        )

        content = logger.log_file.read_text(encoding="utf-8")
        entry = json.loads(content.strip())

        assert entry["args"]["token"] == "[REDACTED]"
        assert entry["args"]["password"] == "[REDACTED]"
        assert entry["args"]["api_key"] == "[REDACTED]"
        assert entry["args"]["normal"] == "value"

    def test_audit_logger_log_truncates_long_strings(self, tmp_path):
        """Test that log truncates long string values."""
        logger = AuditLogger(tmp_path / "logs")
        long_string = "x" * 600

        logger.log(
            tool_name="test_tool",
            args={"long_arg": long_string, "short_arg": "short"},
            result={"status": "OK"},
            duration_ms=100,
        )

        content = logger.log_file.read_text(encoding="utf-8")
        entry = json.loads(content.strip())

        assert len(entry["args"]["long_arg"]) < len(long_string)
        assert "... [truncated" in entry["args"]["long_arg"]
        assert entry["args"]["short_arg"] == "short"

    def test_audit_logger_log_handles_non_dict_result(self, tmp_path):
        """Test that log handles non-dict results."""
        logger = AuditLogger(tmp_path / "logs")

        logger.log(
            tool_name="test_tool",
            args={},
            result="string result",
            duration_ms=100,
        )

        content = logger.log_file.read_text(encoding="utf-8")
        entry = json.loads(content.strip())

        assert entry["result_status"] == "UNKNOWN"  # Non-dict result returns UNKNOWN
        # Note: The actual log method doesn't store the raw result value for non-dict results

    def test_audit_logger_log_handles_write_error(self, tmp_path):
        """Test that log handles write errors gracefully."""
        logger = AuditLogger(tmp_path / "logs")

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            # Should not raise exception
            logger.log("test_tool", {}, {"status": "OK"}, 100)

    def test_audit_logger_get_recent_logs_empty_file(self, tmp_path):
        """Test get_recent_logs with non-existent file."""
        logger = AuditLogger(tmp_path / "logs")

        logs = logger.get_recent_logs()
        assert logs == []

    def test_audit_logger_get_recent_logs_returns_entries(self, tmp_path):
        """Test get_recent_logs returns correct entries."""
        logger = AuditLogger(tmp_path / "logs")

        # Write multiple entries
        logger.log("tool1", {"arg": 1}, {"status": "OK"}, 100)
        logger.log("tool2", {"arg": 2}, {"status": "OK"}, 200)
        logger.log("tool3", {"arg": 3}, {"status": "OK"}, 300)

        logs = logger.get_recent_logs()
        assert len(logs) == 3
        assert logs[0]["tool"] == "tool1"
        assert logs[1]["tool"] == "tool2"
        assert logs[2]["tool"] == "tool3"

    def test_audit_logger_get_recent_logs_respects_limit(self, tmp_path):
        """Test get_recent_logs respects limit parameter."""
        logger = AuditLogger(tmp_path / "logs")

        # Write 10 entries
        for i in range(10):
            logger.log(f"tool{i}", {}, {"status": "OK"}, 100)

        logs = logger.get_recent_logs(limit=5)
        assert len(logs) == 5
        assert logs[0]["tool"] == "tool5"  # Last 5 entries

    def test_audit_logger_get_recent_logs_handles_invalid_json(self, tmp_path):
        """Test get_recent_logs handles invalid JSON lines."""
        logger = AuditLogger(tmp_path / "logs")

        # Write valid entry
        logger.log("tool1", {}, {"status": "OK"}, 100)

        # Write invalid JSON manually
        with open(logger.log_file, "a", encoding="utf-8") as f:
            f.write("invalid json line\n")

        logs = logger.get_recent_logs()
        assert len(logs) == 1
        assert logs[0]["tool"] == "tool1"


class TestAuditedDecorator:
    """Test audited decorator."""

    def test_audited_decorator_success(self, tmp_path):
        """Test audited decorator logs successful function calls."""
        logger = AuditLogger.get_instance(tmp_path / "logs")

        @audited
        def test_function(arg1: str, arg2: int = 42) -> dict:
            return {"status": "SUCCESS", "value": arg1 + str(arg2)}

        result = test_function("test", arg2=100)

        assert result == {"status": "SUCCESS", "value": "test100"}

        # Check that log was written
        logs = logger.get_recent_logs()
        assert len(logs) > 0
        assert logs[0]["tool"] == "test_function"
        assert logs[0]["args"]["arg1"] == "test"
        assert logs[0]["args"]["arg2"] == 100
        assert logs[0]["result_status"] == "SUCCESS"

    def test_audited_decorator_exception(self, tmp_path):
        """Test audited decorator logs exceptions."""
        logger = AuditLogger.get_instance(tmp_path / "logs")

        @audited
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

        # Check that exception was logged
        logs = logger.get_recent_logs()
        assert len(logs) > 0
        assert logs[0]["tool"] == "failing_function"
        assert logs[0]["result_status"] == "EXCEPTION"
        assert "error" in logs[0]["result"]

    def test_audited_decorator_measures_duration(self, tmp_path):
        """Test audited decorator measures execution duration."""
        logger = AuditLogger.get_instance(tmp_path / "logs")

        @audited
        def slow_function():
            time.sleep(0.1)
            return {"status": "OK"}

        slow_function()

        logs = logger.get_recent_logs()
        assert len(logs) > 0
        assert logs[0]["duration_ms"] >= 100

    def test_audited_decorator_preserves_function_metadata(self, tmp_path):
        """Test audited decorator preserves function metadata."""

        @audited
        def documented_function():
            """This is a test function."""
            return "result"

        assert documented_function.__name__ == "documented_function"
        assert "test function" in documented_function.__doc__.lower()

    def test_audited_decorator_with_positional_args(self, tmp_path):
        """Test audited decorator with positional arguments."""
        logger = AuditLogger.get_instance(tmp_path / "logs")

        @audited
        def test_function(arg1, arg2):
            return {"result": arg1 + arg2}

        result = test_function("a", "b")

        assert result == {"result": "ab"}

        logs = logger.get_recent_logs()
        assert len(logs) > 0
        # Note: decorator only logs kwargs, not positional args
        assert logs[0]["tool"] == "test_function"
