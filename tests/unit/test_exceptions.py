"""
Tests for exceptions module.
"""


class TestBoringError:
    """Tests for BoringError base class."""

    def test_boring_error_exists(self):
        """Test that BoringError exists."""
        from boring.exceptions import BoringError

        assert BoringError is not None
        assert issubclass(BoringError, Exception)

    def test_boring_error_message(self):
        """Test BoringError with message."""
        from boring.exceptions import BoringError

        error = BoringError("Test error")
        assert "Test error" in str(error)

    def test_boring_error_with_details(self):
        """Test BoringError with details."""
        from boring.exceptions import BoringError

        error = BoringError("Test error", details=["detail1", "detail2"])
        assert error.details == ["detail1", "detail2"]


class TestAPIErrors:
    """Tests for API error classes."""

    def test_api_error_exists(self):
        """Test that APIError exists."""
        from boring.exceptions import APIError

        assert APIError is not None

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        from boring.exceptions import RateLimitError

        error = RateLimitError()
        assert "Rate limit" in str(error)

    def test_authentication_error(self):
        """Test AuthenticationError."""
        from boring.exceptions import AuthenticationError

        error = AuthenticationError()
        assert "Authentication" in str(error) or "failed" in str(error)


class TestFileErrors:
    """Tests for file error classes."""

    def test_file_error_exists(self):
        """Test that FileError exists."""
        from boring.exceptions import FileError

        assert FileError is not None

    def test_path_security_error(self):
        """Test PathSecurityError."""
        from boring.exceptions import PathSecurityError

        error = PathSecurityError("/etc/passwd", "Path traversal")
        assert "Security" in str(error) or "violation" in str(error)


class TestVerificationErrors:
    """Tests for verification error classes."""

    def test_verification_error_exists(self):
        """Test that VerificationError exists."""
        from boring.exceptions import VerificationError

        assert VerificationError is not None

    def test_lint_error(self):
        """Test LintError."""
        from boring.exceptions import LintError

        error = LintError("test.py", ["issue1", "issue2"])
        assert error.issues == ["issue1", "issue2"]


class TestLoopErrors:
    """Tests for loop error classes."""

    def test_loop_error_exists(self):
        """Test that LoopError exists."""
        from boring.exceptions import LoopError

        assert LoopError is not None

    def test_circuit_breaker_open_error(self):
        """Test CircuitBreakerOpenError."""
        from boring.exceptions import CircuitBreakerOpenError

        error = CircuitBreakerOpenError()
        assert "Circuit breaker" in str(error) or "open" in str(error)


class TestConfigurationErrors:
    """Tests for configuration error classes."""

    def test_configuration_error(self):
        """Test ConfigurationError."""
        from boring.exceptions import ConfigurationError

        error = ConfigurationError("API_KEY", "missing")
        assert "API_KEY" in str(error)

    def test_dependency_error(self):
        """Test DependencyError."""
        from boring.exceptions import DependencyError

        error = DependencyError("chromadb", "pip install chromadb")
        assert error.package == "chromadb"


class TestExceptionHierarchy:
    """Tests for exception hierarchy."""

    def test_api_error_inherits_from_boring_error(self):
        """Test that APIError inherits from BoringError."""
        from boring.exceptions import APIError, BoringError

        assert issubclass(APIError, BoringError)

    def test_file_error_inherits_from_boring_error(self):
        """Test that FileError inherits from BoringError."""
        from boring.exceptions import BoringError, FileError

        assert issubclass(FileError, BoringError)

    def test_verification_error_inherits_from_boring_error(self):
        """Test that VerificationError inherits from BoringError."""
        from boring.exceptions import BoringError, VerificationError

        assert issubclass(VerificationError, BoringError)
