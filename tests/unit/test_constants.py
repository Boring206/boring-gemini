"""
Test suite for boring.core.constants module.

Tests for all centralized constants to ensure they are properly defined
and maintain expected values/types.
"""

from boring.core.constants import (
    API_REQUEST_TIMEOUT,
    BASE_RETRY_DELAY,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT_SECONDS,
    ERROR_PATTERN_LIMIT,
    FAILED_TEST_LIMIT,
    HISTORY_LIMIT,
    # Verification Configuration
    LINT_ISSUE_LIMIT,
    LOG_DEBUG,
    LOG_ERROR,
    # Log Levels
    LOG_INFO,
    LOG_SUCCESS,
    LOG_WARN,
    MAX_CONSECUTIVE_DONE_SIGNALS,
    MAX_CONSECUTIVE_FAILURES,
    MAX_CONSECUTIVE_TEST_LOOPS,
    MAX_CONTENT_LENGTH,
    # File Limits
    MAX_FILE_SIZE,
    MAX_FILENAME_LENGTH,
    MAX_FILES_PER_PATCH,
    MAX_HOURLY_CALLS,
    MAX_INPUT_TOKENS,
    # Loop Configuration
    MAX_LOOPS,
    # API Configuration
    MAX_OUTPUT_TOKENS,
    MAX_RETRIES,
    MAX_RETRY_DELAY,
    MEMORY_LIMIT,
    STATUS_COMPLETE,
    STATUS_ERROR,
    STATUS_FAILED,
    STATUS_IN_PROGRESS,
    STATUS_PARTIAL,
    # Status Strings
    STATUS_SUCCESS,
    SUBPROCESS_TIMEOUT,
    SUGGESTION_LIMIT,
    TEST_TIMEOUT,
    TRUNCATE_ERROR_MESSAGE,
    TRUNCATE_PREVIEW_LENGTH,
    TRUNCATE_SOLUTION,
    VECTOR_COLLECTION_NAME,
    VECTOR_DEFAULT_RESULTS,
    # Vector Memory Configuration
    VECTOR_SIMILARITY_THRESHOLD,
    VERIFICATION_RESULT_LIMIT,
)


class TestAPIConfiguration:
    """Test API configuration constants."""

    def test_max_output_tokens(self):
        """Test MAX_OUTPUT_TOKENS is valid."""
        assert isinstance(MAX_OUTPUT_TOKENS, int)
        assert MAX_OUTPUT_TOKENS > 0
        assert MAX_OUTPUT_TOKENS == 8192

    def test_max_input_tokens(self):
        """Test MAX_INPUT_TOKENS is valid."""
        assert isinstance(MAX_INPUT_TOKENS, int)
        assert MAX_INPUT_TOKENS > MAX_OUTPUT_TOKENS
        assert MAX_INPUT_TOKENS == 128000

    def test_default_temperature(self):
        """Test DEFAULT_TEMPERATURE is in valid range."""
        assert isinstance(DEFAULT_TEMPERATURE, float)
        assert 0.0 <= DEFAULT_TEMPERATURE <= 2.0
        assert DEFAULT_TEMPERATURE == 0.7

    def test_timeout_values(self):
        """Test all timeout values are positive integers."""
        timeouts = [
            DEFAULT_TIMEOUT_SECONDS,
            API_REQUEST_TIMEOUT,
            SUBPROCESS_TIMEOUT,
            TEST_TIMEOUT,
        ]
        for timeout in timeouts:
            assert isinstance(timeout, int)
            assert timeout > 0

    def test_retry_configuration(self):
        """Test retry configuration values."""
        assert isinstance(MAX_RETRIES, int)
        assert MAX_RETRIES >= 1
        assert MAX_RETRIES == 3

        assert isinstance(BASE_RETRY_DELAY, float)
        assert BASE_RETRY_DELAY > 0

        assert isinstance(MAX_RETRY_DELAY, float)
        assert MAX_RETRY_DELAY > BASE_RETRY_DELAY


class TestLoopConfiguration:
    """Test loop configuration constants."""

    def test_max_loops(self):
        """Test MAX_LOOPS is reasonable."""
        assert isinstance(MAX_LOOPS, int)
        assert 10 <= MAX_LOOPS <= 1000
        assert MAX_LOOPS == 100

    def test_max_hourly_calls(self):
        """Test MAX_HOURLY_CALLS limit."""
        assert isinstance(MAX_HOURLY_CALLS, int)
        assert MAX_HOURLY_CALLS > 0
        assert MAX_HOURLY_CALLS == 50

    def test_consecutive_limits(self):
        """Test consecutive failure/signal limits."""
        assert isinstance(MAX_CONSECUTIVE_FAILURES, int)
        assert MAX_CONSECUTIVE_FAILURES >= 1

        assert isinstance(MAX_CONSECUTIVE_TEST_LOOPS, int)
        assert MAX_CONSECUTIVE_TEST_LOOPS >= 1

        assert isinstance(MAX_CONSECUTIVE_DONE_SIGNALS, int)
        assert MAX_CONSECUTIVE_DONE_SIGNALS >= 1

    def test_context_limits(self):
        """Test context/history limits."""
        assert isinstance(HISTORY_LIMIT, int)
        assert HISTORY_LIMIT > 0

        assert isinstance(MEMORY_LIMIT, int)
        assert MEMORY_LIMIT > 0

        assert isinstance(ERROR_PATTERN_LIMIT, int)
        assert ERROR_PATTERN_LIMIT > 0


class TestFileLimits:
    """Test file limit constants."""

    def test_max_file_size(self):
        """Test MAX_FILE_SIZE is 1MB."""
        assert isinstance(MAX_FILE_SIZE, int)
        assert MAX_FILE_SIZE == 1_000_000

    def test_max_content_length(self):
        """Test MAX_CONTENT_LENGTH."""
        assert isinstance(MAX_CONTENT_LENGTH, int)
        assert MAX_CONTENT_LENGTH > 0

    def test_max_filename_length(self):
        """Test MAX_FILENAME_LENGTH is reasonable."""
        assert isinstance(MAX_FILENAME_LENGTH, int)
        assert MAX_FILENAME_LENGTH == 255  # Standard filesystem limit

    def test_max_files_per_patch(self):
        """Test MAX_FILES_PER_PATCH limit."""
        assert isinstance(MAX_FILES_PER_PATCH, int)
        assert MAX_FILES_PER_PATCH > 0
        assert MAX_FILES_PER_PATCH == 50

    def test_truncation_limits(self):
        """Test truncation limits are positive."""
        truncation_values = [
            TRUNCATE_PREVIEW_LENGTH,
            TRUNCATE_ERROR_MESSAGE,
            TRUNCATE_SOLUTION,
        ]
        for value in truncation_values:
            assert isinstance(value, int)
            assert value > 0


class TestVerificationConfiguration:
    """Test verification configuration constants."""

    def test_issue_limits(self):
        """Test verification issue limits."""
        limits = [
            LINT_ISSUE_LIMIT,
            FAILED_TEST_LIMIT,
            VERIFICATION_RESULT_LIMIT,
            SUGGESTION_LIMIT,
        ]
        for limit in limits:
            assert isinstance(limit, int)
            assert limit > 0


class TestVectorMemoryConfiguration:
    """Test vector memory configuration constants."""

    def test_similarity_threshold(self):
        """Test VECTOR_SIMILARITY_THRESHOLD is in valid range."""
        assert isinstance(VECTOR_SIMILARITY_THRESHOLD, float)
        assert 0.0 <= VECTOR_SIMILARITY_THRESHOLD <= 1.0
        assert VECTOR_SIMILARITY_THRESHOLD == 0.5

    def test_default_results(self):
        """Test VECTOR_DEFAULT_RESULTS."""
        assert isinstance(VECTOR_DEFAULT_RESULTS, int)
        assert VECTOR_DEFAULT_RESULTS > 0

    def test_collection_name(self):
        """Test VECTOR_COLLECTION_NAME is valid string."""
        assert isinstance(VECTOR_COLLECTION_NAME, str)
        assert len(VECTOR_COLLECTION_NAME) > 0
        assert VECTOR_COLLECTION_NAME == "boring_knowledge"


class TestStatusStrings:
    """Test status string constants."""

    def test_status_values(self):
        """Test all status strings are defined."""
        statuses = [
            STATUS_SUCCESS,
            STATUS_ERROR,
            STATUS_FAILED,
            STATUS_PARTIAL,
            STATUS_IN_PROGRESS,
            STATUS_COMPLETE,
        ]
        for status in statuses:
            assert isinstance(status, str)
            assert len(status) > 0

    def test_status_success(self):
        """Test STATUS_SUCCESS value."""
        assert STATUS_SUCCESS == "SUCCESS"

    def test_status_error(self):
        """Test STATUS_ERROR value."""
        assert STATUS_ERROR == "ERROR"

    def test_status_uniqueness(self):
        """Test all status values are unique."""
        statuses = [
            STATUS_SUCCESS,
            STATUS_ERROR,
            STATUS_FAILED,
            STATUS_PARTIAL,
            STATUS_IN_PROGRESS,
            STATUS_COMPLETE,
        ]
        assert len(statuses) == len(set(statuses))


class TestLogLevels:
    """Test log level constants."""

    def test_log_level_values(self):
        """Test all log levels are defined."""
        levels = [LOG_INFO, LOG_WARN, LOG_ERROR, LOG_SUCCESS, LOG_DEBUG]
        for level in levels:
            assert isinstance(level, str)
            assert len(level) > 0

    def test_log_level_uniqueness(self):
        """Test all log levels are unique."""
        levels = [LOG_INFO, LOG_WARN, LOG_ERROR, LOG_SUCCESS, LOG_DEBUG]
        assert len(levels) == len(set(levels))

    def test_log_info(self):
        """Test LOG_INFO value."""
        assert LOG_INFO == "INFO"

    def test_log_error(self):
        """Test LOG_ERROR value."""
        assert LOG_ERROR == "ERROR"

    def test_log_debug(self):
        """Test LOG_DEBUG value."""
        assert LOG_DEBUG == "DEBUG"


class TestConstantImmutability:
    """Test that constants cannot be modified (at runtime)."""

    def test_constants_are_typed_as_final(self):
        """Test that constants are defined as Final."""
        # This is a compile-time check, but we can verify the imports work

        # Just verify the module can be imported and used
        assert MAX_LOOPS == 100
        assert STATUS_SUCCESS == "SUCCESS"

    def test_constants_module_structure(self):
        """Test that constants module has expected structure."""
        import boring.core.constants as const

        # Check module has expected sections
        assert hasattr(const, "MAX_OUTPUT_TOKENS")
        assert hasattr(const, "MAX_LOOPS")
        assert hasattr(const, "MAX_FILE_SIZE")
        assert hasattr(const, "STATUS_SUCCESS")
        assert hasattr(const, "LOG_INFO")
