"""
Tests for core/exceptions.py - Exception Hierarchy (V11.2.3)

Tests the new exception classes added for Storage, Brain, MCP, and Shadow Mode.
"""

from boring.core.exceptions import (
    # API Errors
    APIError,
    AuthenticationError,
    # Base
    BoringError,
    # Brain Errors (V11.2.3)
    BrainError,
    CircuitBreakerOpenError,
    # Configuration Errors
    ConfigurationError,
    DatabaseConnectionError,
    DependencyError,
    ExitSignalError,
    # File Errors
    FileError,
    FileSizeError,
    KnowledgeSyncError,
    LintError,
    # Loop Errors
    LoopError,
    MaxLoopsExceededError,
    # MCP Tool Errors (V11.2.3)
    MCPToolError,
    MigrationError,
    ModelNotFoundError,
    OperationBlockedError,
    PathSecurityError,
    PatternNotFoundError,
    RateLimitError,
    RollbackError,
    # Shadow Mode Errors (V11.2.3)
    ShadowModeError,
    # Storage Errors (V11.2.3)
    StorageError,
    TestError,
    TimeoutError,
    ToolExecutionError,
    ToolNotFoundError,
    # Verification Errors
    VerificationError,
)
from boring.core.exceptions import (
    FileNotFoundError as BoringFileNotFoundError,
)
from boring.core.exceptions import (
    SyntaxError as BoringSyntaxError,
)


class TestBoringErrorBase:
    """Tests for base BoringError class."""

    def test_basic_message(self):
        """Basic error message."""
        err = BoringError("Something went wrong")
        assert str(err) == "Something went wrong"
        assert err.message == "Something went wrong"
        assert err.details == []

    def test_with_details(self):
        """Error with details list."""
        err = BoringError("Failed", details=["Reason 1", "Reason 2"])
        assert "Reason 1" in str(err)
        assert "Reason 2" in str(err)
        assert err.details == ["Reason 1", "Reason 2"]


class TestAPIErrors:
    """Tests for API-related errors."""

    def test_rate_limit_error(self):
        """RateLimitError with retry_after."""
        err = RateLimitError(retry_after=60)
        assert "Rate limit" in str(err)
        assert err.retry_after == 60

    def test_authentication_error(self):
        """AuthenticationError includes API key hint."""
        err = AuthenticationError()
        assert "Authentication failed" in str(err)
        assert "GOOGLE_API_KEY" in str(err)

    def test_timeout_error(self):
        """TimeoutError with timeout value."""
        err = TimeoutError(timeout_seconds=30)
        assert "timed out" in str(err)
        assert err.timeout_seconds == 30

    def test_model_not_found_error(self):
        """ModelNotFoundError with model name."""
        err = ModelNotFoundError("gemini-pro-vision")
        assert "gemini-pro-vision" in str(err)
        assert err.model_name == "gemini-pro-vision"


class TestFileErrors:
    """Tests for file-related errors."""

    def test_path_security_error(self):
        """PathSecurityError with path and reason."""
        err = PathSecurityError("/etc/passwd", "Outside project root")
        assert "/etc/passwd" in str(err)
        assert "Outside project root" in str(err)
        assert err.path == "/etc/passwd"
        assert err.reason == "Outside project root"

    def test_file_not_found_error(self):
        """BoringFileNotFoundError with path."""
        err = BoringFileNotFoundError("/missing/file.py")
        assert "/missing/file.py" in str(err)
        assert err.path == "/missing/file.py"

    def test_file_size_error(self):
        """FileSizeError with size details."""
        err = FileSizeError("/large/file.bin", 5000000, 1000000)
        assert "/large/file.bin" in str(err)
        assert err.size == 5000000
        assert err.max_size == 1000000


class TestVerificationErrors:
    """Tests for verification-related errors."""

    def test_syntax_error(self):
        """BoringSyntaxError with location."""
        err = BoringSyntaxError("main.py", 42, "unexpected indent")
        assert "main.py" in str(err)
        assert "42" in str(err)
        assert "unexpected indent" in str(err)
        assert err.file_path == "main.py"
        assert err.line == 42

    def test_lint_error(self):
        """LintError with issues list."""
        issues = ["E501: line too long", "W291: trailing whitespace"]
        err = LintError("utils.py", issues)
        assert "utils.py" in str(err)
        assert err.issues == issues

    def test_test_error(self):
        """TestError with failed tests."""
        failed = ["test_auth", "test_api"]
        err = TestError(failed)
        assert "2 test(s) failed" in str(err)
        assert err.failed_tests == failed


class TestLoopErrors:
    """Tests for loop-related errors."""

    def test_circuit_breaker_open_error(self):
        """CircuitBreakerOpenError with reset hint."""
        err = CircuitBreakerOpenError()
        assert "Circuit breaker" in str(err)
        assert "reset-circuit" in str(err)

    def test_max_loops_exceeded_error(self):
        """MaxLoopsExceededError with count."""
        err = MaxLoopsExceededError(100)
        assert "100" in str(err)
        assert err.max_loops == 100

    def test_exit_signal_error(self):
        """ExitSignalError with signal type."""
        err = ExitSignalError("DONE")
        assert "DONE" in str(err)
        assert err.signal_type == "DONE"


class TestConfigurationErrors:
    """Tests for configuration-related errors."""

    def test_configuration_error(self):
        """ConfigurationError with setting and issue."""
        err = ConfigurationError("GOOGLE_API_KEY", "Not set")
        assert "GOOGLE_API_KEY" in str(err)
        assert "Not set" in str(err)
        assert err.setting == "GOOGLE_API_KEY"

    def test_dependency_error(self):
        """DependencyError with install command."""
        err = DependencyError("chromadb", "pip install boring-aicoding[vector]")
        assert "chromadb" in str(err)
        assert "pip install" in str(err)
        assert err.package == "chromadb"


class TestStorageErrors:
    """Tests for storage-related errors (V11.2.3)."""

    def test_storage_error_base(self):
        """StorageError base class."""
        err = StorageError("Storage operation failed")
        assert isinstance(err, BoringError)
        assert "Storage operation failed" in str(err)

    def test_database_connection_error(self):
        """DatabaseConnectionError with db path."""
        err = DatabaseConnectionError("/path/to/db.sqlite", "File locked")
        assert "/path/to/db.sqlite" in str(err)
        assert "File locked" in str(err)
        assert err.db_path == "/path/to/db.sqlite"
        assert err.reason == "File locked"

    def test_migration_error(self):
        """MigrationError with source and target."""
        err = MigrationError("JSON", "SQLite", "Schema mismatch")
        assert "JSON" in str(err)
        assert "SQLite" in str(err)
        assert "Schema mismatch" in str(err)
        assert err.source == "JSON"
        assert err.target == "SQLite"


class TestBrainErrors:
    """Tests for brain-related errors (V11.2.3)."""

    def test_brain_error_base(self):
        """BrainError base class."""
        err = BrainError("Brain operation failed")
        assert isinstance(err, BoringError)

    def test_pattern_not_found_error(self):
        """PatternNotFoundError with pattern ID."""
        err = PatternNotFoundError("ERR_AUTH_001")
        assert "ERR_AUTH_001" in str(err)
        assert err.pattern_id == "ERR_AUTH_001"

    def test_knowledge_sync_error(self):
        """KnowledgeSyncError with remote URL."""
        err = KnowledgeSyncError("https://github.com/user/brain", "Network timeout")
        assert "github.com" in str(err)
        assert "Network timeout" in str(err)
        assert err.remote_url == "https://github.com/user/brain"


class TestMCPToolErrors:
    """Tests for MCP tool errors (V11.2.3)."""

    def test_mcp_tool_error_base(self):
        """MCPToolError base class."""
        err = MCPToolError("Tool execution failed")
        assert isinstance(err, BoringError)

    def test_tool_not_found_error(self):
        """ToolNotFoundError with tool name."""
        err = ToolNotFoundError("boring_unknown_tool")
        assert "boring_unknown_tool" in str(err)
        assert err.tool_name == "boring_unknown_tool"

    def test_tool_execution_error(self):
        """ToolExecutionError with tool name and reason."""
        err = ToolExecutionError("boring_verify", "Timeout after 60s")
        assert "boring_verify" in str(err)
        assert "Timeout" in str(err)
        assert err.tool_name == "boring_verify"
        assert err.reason == "Timeout after 60s"


class TestShadowModeErrors:
    """Tests for shadow mode errors (V11.2.3)."""

    def test_shadow_mode_error_base(self):
        """ShadowModeError base class."""
        err = ShadowModeError("Shadow mode operation failed")
        assert isinstance(err, BoringError)

    def test_operation_blocked_error(self):
        """OperationBlockedError with operation details."""
        err = OperationBlockedError("DELETE_FILE", "HIGH", "Destructive operation")
        assert "DELETE_FILE" in str(err)
        assert "HIGH" in str(err)
        assert "Destructive" in str(err)
        assert "shadow_approve" in str(err)  # Should include hint
        assert err.operation == "DELETE_FILE"
        assert err.severity == "HIGH"

    def test_rollback_error(self):
        """RollbackError with checkpoint ID."""
        err = RollbackError("chkpt_20260112_1234", "Checkpoint corrupted")
        assert "chkpt_20260112_1234" in str(err)
        assert "corrupted" in str(err)
        assert err.checkpoint_id == "chkpt_20260112_1234"


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_all_inherit_from_boring_error(self):
        """All custom exceptions should inherit from BoringError."""
        exceptions = [
            APIError("test"),
            FileError("test"),
            VerificationError("test"),
            LoopError("test"),
            ConfigurationError("test", "test"),
            StorageError("test"),
            BrainError("test"),
            MCPToolError("test"),
            ShadowModeError("test"),
        ]
        for exc in exceptions:
            assert isinstance(exc, BoringError)

    def test_specific_exceptions_inherit_correctly(self):
        """Specific exceptions should inherit from their parent."""
        # API errors
        assert isinstance(RateLimitError(), APIError)
        assert isinstance(AuthenticationError(), APIError)

        # Storage errors
        assert isinstance(DatabaseConnectionError("db", "reason"), StorageError)
        assert isinstance(MigrationError("a", "b", "c"), StorageError)

        # Brain errors
        assert isinstance(PatternNotFoundError("id"), BrainError)
        assert isinstance(KnowledgeSyncError("url", "reason"), BrainError)

        # MCP errors
        assert isinstance(ToolNotFoundError("tool"), MCPToolError)
        assert isinstance(ToolExecutionError("tool", "reason"), MCPToolError)

        # Shadow mode errors
        assert isinstance(OperationBlockedError("op", "sev", "reason"), ShadowModeError)
        assert isinstance(RollbackError("id", "reason"), ShadowModeError)
