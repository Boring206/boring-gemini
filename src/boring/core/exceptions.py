"""
Exceptions Module for Boring V4.0

Defines custom exception hierarchy for consistent error handling.
"""

from typing import Optional


class BoringError(Exception):
    """Base exception for all Boring errors."""

    def __init__(self, message: str, details: Optional[list[str]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or []

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {'; '.join(self.details)}"
        return self.message


# =============================================================================
# API ERRORS
# =============================================================================


class APIError(BoringError):
    """Base class for API-related errors."""

    pass


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class AuthenticationError(APIError):
    """Raised when API authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, ["Check GOOGLE_API_KEY environment variable"])


class TimeoutError(APIError):
    """Raised when API request times out."""

    def __init__(self, message: str = "Request timed out", timeout_seconds: Optional[int] = None):
        super().__init__(message)
        self.timeout_seconds = timeout_seconds


class ModelNotFoundError(APIError):
    """Raised when specified model is not available."""

    def __init__(self, model_name: str):
        super().__init__(f"Model not found: {model_name}")
        self.model_name = model_name


# =============================================================================
# FILE ERRORS
# =============================================================================


class FileError(BoringError):
    """Base class for file-related errors."""

    pass


class PathSecurityError(FileError):
    """Raised when a path fails security validation."""

    def __init__(self, path: str, reason: str):
        super().__init__(f"Security violation for path '{path}': {reason}")
        self.path = path
        self.reason = reason


# TODO(V12.0): Rename to BoringFileNotFoundError to avoid shadowing builtin
class FileNotFoundError(FileError):
    """Raised when a required file is not found."""

    def __init__(self, path: str):
        super().__init__(f"File not found: {path}")
        self.path = path


class FileSizeError(FileError):
    """Raised when file exceeds size limits."""

    def __init__(self, path: str, size: int, max_size: int):
        super().__init__(f"File too large: {path} ({size} > {max_size})")
        self.path = path
        self.size = size
        self.max_size = max_size


# =============================================================================
# VERIFICATION ERRORS
# =============================================================================


class VerificationError(BoringError):
    """Base class for verification-related errors."""

    pass


# TODO(V12.0): Rename to BoringSyntaxError to avoid shadowing builtin
class SyntaxError(VerificationError):
    """Raised when Python syntax check fails."""

    def __init__(self, file_path: str, line: int, message: str):
        super().__init__(f"Syntax error in {file_path}:{line}: {message}")
        self.file_path = file_path
        self.line = line


class LintError(VerificationError):
    """Raised when linting fails."""

    def __init__(self, file_path: str, issues: list[str]):
        super().__init__(f"Lint errors in {file_path}", issues)
        self.file_path = file_path
        self.issues = issues


class TestError(VerificationError):
    """Raised when tests fail."""

    def __init__(self, failed_tests: list[str]):
        super().__init__(f"{len(failed_tests)} test(s) failed", failed_tests)
        self.failed_tests = failed_tests


# =============================================================================
# LOOP ERRORS
# =============================================================================


class LoopError(BoringError):
    """Base class for loop-related errors."""

    pass


class CircuitBreakerOpenError(LoopError):
    """Raised when circuit breaker is open."""

    def __init__(self, message: str = "Circuit breaker is open"):
        super().__init__(message, ["Use 'boring reset-circuit' to reset"])


class MaxLoopsExceededError(LoopError):
    """Raised when maximum loop count is exceeded."""

    def __init__(self, max_loops: int):
        super().__init__(f"Maximum loops exceeded: {max_loops}")
        self.max_loops = max_loops


class ExitSignalError(LoopError):
    """Raised when an exit signal is detected."""

    def __init__(self, signal_type: str):
        super().__init__(f"Exit signal detected: {signal_type}")
        self.signal_type = signal_type


# =============================================================================
# CONFIGURATION ERRORS
# =============================================================================


class ConfigurationError(BoringError):
    """Raised when configuration is invalid."""

    def __init__(self, setting: str, issue: str):
        super().__init__(f"Configuration error for '{setting}': {issue}")
        self.setting = setting
        self.issue = issue


class DependencyError(BoringError):
    """Raised when a required dependency is missing."""

    def __init__(self, package: str, install_command: Optional[str] = None):
        install_hint = f"Install with: {install_command}" if install_command else ""
        super().__init__(f"Missing dependency: {package}", [install_hint] if install_hint else [])
        self.package = package
        self.install_command = install_command


# =============================================================================
# STORAGE ERRORS (V11.2.3)
# =============================================================================


class StorageError(BoringError):
    """Base class for storage-related errors (SQLite, JSON, etc.)."""

    pass


class DatabaseConnectionError(StorageError):
    """Raised when database connection fails."""

    def __init__(self, db_path: str, reason: str):
        super().__init__(f"Failed to connect to database '{db_path}': {reason}")
        self.db_path = db_path
        self.reason = reason


class MigrationError(StorageError):
    """Raised when data migration fails."""

    def __init__(self, source: str, target: str, reason: str):
        super().__init__(f"Migration from {source} to {target} failed: {reason}")
        self.source = source
        self.target = target
        self.reason = reason


# =============================================================================
# BRAIN ERRORS (V11.2.3)
# =============================================================================


class BrainError(BoringError):
    """Base class for Brain Manager errors."""

    pass


class PatternNotFoundError(BrainError):
    """Raised when a pattern cannot be found in the brain."""

    def __init__(self, pattern_id: str):
        super().__init__(f"Pattern not found: {pattern_id}")
        self.pattern_id = pattern_id


class KnowledgeSyncError(BrainError):
    """Raised when Knowledge Swarm sync fails."""

    def __init__(self, remote_url: str, reason: str):
        super().__init__(f"Failed to sync with '{remote_url}': {reason}")
        self.remote_url = remote_url
        self.reason = reason


# =============================================================================
# MCP TOOL ERRORS (V11.2.3)
# =============================================================================


class MCPToolError(BoringError):
    """Base class for MCP tool execution errors."""

    pass


class ToolNotFoundError(MCPToolError):
    """Raised when requested MCP tool is not found."""

    def __init__(self, tool_name: str):
        super().__init__(f"MCP tool not found: {tool_name}")
        self.tool_name = tool_name


class ToolExecutionError(MCPToolError):
    """Raised when MCP tool execution fails."""

    def __init__(self, tool_name: str, reason: str):
        super().__init__(f"Tool '{tool_name}' execution failed: {reason}")
        self.tool_name = tool_name
        self.reason = reason


# =============================================================================
# SHADOW MODE ERRORS (V11.2.3)
# =============================================================================


class ShadowModeError(BoringError):
    """Base class for Shadow Mode errors."""

    pass


class OperationBlockedError(ShadowModeError):
    """Raised when an operation is blocked by Shadow Mode."""

    def __init__(self, operation: str, severity: str, reason: str):
        super().__init__(
            f"Operation '{operation}' blocked (severity: {severity}): {reason}",
            ["Use 'boring shadow_approve' to review pending operations"],
        )
        self.operation = operation
        self.severity = severity
        self.reason = reason


class RollbackError(ShadowModeError):
    """Raised when rollback operation fails."""

    def __init__(self, checkpoint_id: str, reason: str):
        super().__init__(f"Failed to rollback to checkpoint '{checkpoint_id}': {reason}")
        self.checkpoint_id = checkpoint_id
        self.reason = reason
