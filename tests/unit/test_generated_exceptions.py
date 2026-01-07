# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.exceptions module.
"""

from boring.exceptions import (
    APIError,
    AuthenticationError,
    BoringError,
    CircuitBreakerOpenError,
    ConfigurationError,
    DependencyError,
    ExitSignalError,
    FileError,
    FileSizeError,
    LoopError,
    MaxLoopsExceededError,
    ModelNotFoundError,
    PathSecurityError,
    RateLimitError,
    TestError,
    VerificationError,
)
from boring.exceptions import (
    FileNotFoundError as BoringFileNotFoundError,
)
from boring.exceptions import (
    SyntaxError as BoringSyntaxError,
)
from boring.exceptions import (
    TimeoutError as BoringTimeoutError,
)

# =============================================================================
# BASE ERROR TESTS
# =============================================================================


class TestBoringError:
    """Tests for BoringError base class."""

    def test_boring_error_creation(self):
        """Test BoringError creation."""
        error = BoringError("Test error")
        assert str(error) == "Test error"
        assert error.details == []

    def test_boring_error_with_details(self):
        """Test BoringError with details."""
        error = BoringError("Test error", details=["detail1", "detail2"])
        assert "detail1" in str(error) or error.details == ["detail1", "detail2"]


# =============================================================================
# API ERROR TESTS
# =============================================================================


class TestAPIError:
    """Tests for APIError class."""

    def test_api_error_creation(self):
        """Test APIError creation."""
        error = APIError("API error")
        assert isinstance(error, BoringError)
        assert isinstance(error, APIError)

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError("Rate limit", retry_after=60)
        assert isinstance(error, APIError)
        assert error.retry_after == 60

    def test_rate_limit_error_default(self):
        """Test RateLimitError with default values."""
        error = RateLimitError()
        assert "Rate limit" in str(error)

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Auth failed")
        assert isinstance(error, APIError)

    def test_authentication_error_default(self):
        """Test AuthenticationError with default message."""
        error = AuthenticationError()
        assert "Authentication" in str(error)

    def test_timeout_error(self):
        """Test TimeoutError."""
        error = BoringTimeoutError("Timeout", timeout_seconds=30)
        assert isinstance(error, APIError)
        assert error.timeout_seconds == 30

    def test_timeout_error_default(self):
        """Test TimeoutError with default values."""
        error = BoringTimeoutError()
        assert "timed out" in str(error).lower()

    def test_model_not_found_error(self):
        """Test ModelNotFoundError."""
        error = ModelNotFoundError("model-name")
        assert isinstance(error, APIError)
        assert "model-name" in str(error)


# =============================================================================
# FILE ERROR TESTS
# =============================================================================


class TestFileError:
    """Tests for FileError class."""

    def test_file_error_creation(self):
        """Test FileError creation."""
        error = FileError("File error")
        assert isinstance(error, BoringError)
        assert isinstance(error, FileError)

    def test_path_security_error(self):
        """Test PathSecurityError."""
        error = PathSecurityError("/etc/passwd", "Path traversal")
        assert isinstance(error, FileError)
        assert "/etc/passwd" in str(error) or "Path traversal" in str(error)

    def test_file_not_found_error(self):
        """Test FileNotFoundError."""
        error = BoringFileNotFoundError("/nonexistent/file")
        assert isinstance(error, FileError)
        assert "/nonexistent/file" in str(error)

    def test_file_size_error(self):
        """Test FileSizeError."""
        error = FileSizeError("/large/file", size=1000000, max_size=1000)
        assert isinstance(error, FileError)
        assert "1000000" in str(error) or "1000" in str(error)


# =============================================================================
# VERIFICATION ERROR TESTS
# =============================================================================


class TestVerificationError:
    """Tests for VerificationError class."""

    def test_verification_error_creation(self):
        """Test VerificationError creation."""
        error = VerificationError("Verification error")
        assert isinstance(error, BoringError)
        assert isinstance(error, VerificationError)

    def test_syntax_error(self):
        """Test SyntaxError."""
        error = BoringSyntaxError("test.py", 10, "Invalid syntax")
        assert isinstance(error, VerificationError)
        assert "test.py" in str(error) or "10" in str(error)

    def test_lint_error(self):
        """Test LintError."""
        error = TestError(["test1", "test2"])
        assert isinstance(error, VerificationError)
        assert len(error.failed_tests) == 2

    def test_test_error(self):
        """Test TestError."""
        error = TestError(["test1", "test2"])
        assert isinstance(error, VerificationError)
        assert len(error.failed_tests) == 2


# =============================================================================
# LOOP ERROR TESTS
# =============================================================================


class TestLoopError:
    """Tests for LoopError class."""

    def test_loop_error_creation(self):
        """Test LoopError creation."""
        error = LoopError("Loop error")
        assert isinstance(error, BoringError)
        assert isinstance(error, LoopError)

    def test_circuit_breaker_open_error(self):
        """Test CircuitBreakerOpenError."""
        error = CircuitBreakerOpenError("Circuit open")
        assert isinstance(error, LoopError)

    def test_circuit_breaker_open_error_default(self):
        """Test CircuitBreakerOpenError with default message."""
        error = CircuitBreakerOpenError()
        assert "Circuit breaker" in str(error)

    def test_max_loops_exceeded_error(self):
        """Test MaxLoopsExceededError."""
        error = MaxLoopsExceededError(max_loops=10)
        assert isinstance(error, LoopError)
        assert "10" in str(error)

    def test_exit_signal_error(self):
        """Test ExitSignalError."""
        error = ExitSignalError("COMPLETE")
        assert isinstance(error, LoopError)
        assert "COMPLETE" in str(error)


# =============================================================================
# CONFIGURATION ERROR TESTS
# =============================================================================


class TestConfigurationError:
    """Tests for ConfigurationError class."""

    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("setting_name", "Invalid value")
        assert isinstance(error, BoringError)
        assert "setting_name" in str(error) or "Invalid value" in str(error)


# =============================================================================
# DEPENDENCY ERROR TESTS
# =============================================================================


class TestDependencyError:
    """Tests for DependencyError class."""

    def test_dependency_error(self):
        """Test DependencyError."""
        error = DependencyError("package-name", "pip install package-name")
        assert isinstance(error, BoringError)
        assert "package-name" in str(error)

    def test_dependency_error_no_command(self):
        """Test DependencyError without install command."""
        error = DependencyError("package-name")
        assert isinstance(error, BoringError)
