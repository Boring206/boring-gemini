# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.constants module.
"""

from boring.constants import (
    API_REQUEST_TIMEOUT,
    BASE_RETRY_DELAY,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT_SECONDS,
    ERROR_PATTERN_LIMIT,
    FAILED_TEST_LIMIT,
    HISTORY_LIMIT,
    LINT_ISSUE_LIMIT,
    LOG_DEBUG,
    LOG_ERROR,
    LOG_INFO,
    LOG_SUCCESS,
    LOG_WARN,
    MAX_CONSECUTIVE_DONE_SIGNALS,
    MAX_CONSECUTIVE_FAILURES,
    MAX_CONSECUTIVE_TEST_LOOPS,
    MAX_CONTENT_LENGTH,
    MAX_FILE_SIZE,
    MAX_FILENAME_LENGTH,
    MAX_FILES_PER_PATCH,
    MAX_HOURLY_CALLS,
    MAX_INPUT_TOKENS,
    MAX_LOOPS,
    MAX_OUTPUT_TOKENS,
    MAX_RETRIES,
    MAX_RETRY_DELAY,
    MEMORY_LIMIT,
    STATUS_COMPLETE,
    STATUS_FAILED,
    STATUS_IN_PROGRESS,
    STATUS_PARTIAL,
    STATUS_SUCCESS,
    SUBPROCESS_TIMEOUT,
    SUGGESTION_LIMIT,
    TEST_TIMEOUT,
    TRUNCATE_ERROR_MESSAGE,
    TRUNCATE_PREVIEW_LENGTH,
    TRUNCATE_SOLUTION,
    VECTOR_COLLECTION_NAME,
    VECTOR_DEFAULT_RESULTS,
    VECTOR_SIMILARITY_THRESHOLD,
    VERIFICATION_RESULT_LIMIT,
)

# =============================================================================
# API CONFIGURATION TESTS
# =============================================================================


class TestAPIConfiguration:
    """Tests for API configuration constants."""

    def test_max_output_tokens(self):
        """Test MAX_OUTPUT_TOKENS constant."""
        assert MAX_OUTPUT_TOKENS == 8192

    def test_max_input_tokens(self):
        """Test MAX_INPUT_TOKENS constant."""
        assert MAX_INPUT_TOKENS == 128000

    def test_default_temperature(self):
        """Test DEFAULT_TEMPERATURE constant."""
        assert DEFAULT_TEMPERATURE == 0.7

    def test_default_timeout_seconds(self):
        """Test DEFAULT_TIMEOUT_SECONDS constant."""
        assert DEFAULT_TIMEOUT_SECONDS == 900

    def test_api_request_timeout(self):
        """Test API_REQUEST_TIMEOUT constant."""
        assert API_REQUEST_TIMEOUT == 120

    def test_subprocess_timeout(self):
        """Test SUBPROCESS_TIMEOUT constant."""
        assert SUBPROCESS_TIMEOUT == 30

    def test_test_timeout(self):
        """Test TEST_TIMEOUT constant."""
        assert TEST_TIMEOUT == 120

    def test_max_retries(self):
        """Test MAX_RETRIES constant."""
        assert MAX_RETRIES == 3

    def test_base_retry_delay(self):
        """Test BASE_RETRY_DELAY constant."""
        assert BASE_RETRY_DELAY == 2.0

    def test_max_retry_delay(self):
        """Test MAX_RETRY_DELAY constant."""
        assert MAX_RETRY_DELAY == 60.0


# =============================================================================
# LOOP CONFIGURATION TESTS
# =============================================================================


class TestLoopConfiguration:
    """Tests for loop configuration constants."""

    def test_max_loops(self):
        """Test MAX_LOOPS constant."""
        assert MAX_LOOPS == 100

    def test_max_hourly_calls(self):
        """Test MAX_HOURLY_CALLS constant."""
        assert MAX_HOURLY_CALLS == 50

    def test_max_consecutive_failures(self):
        """Test MAX_CONSECUTIVE_FAILURES constant."""
        assert MAX_CONSECUTIVE_FAILURES == 3

    def test_max_consecutive_test_loops(self):
        """Test MAX_CONSECUTIVE_TEST_LOOPS constant."""
        assert MAX_CONSECUTIVE_TEST_LOOPS == 3

    def test_max_consecutive_done_signals(self):
        """Test MAX_CONSECUTIVE_DONE_SIGNALS constant."""
        assert MAX_CONSECUTIVE_DONE_SIGNALS == 2

    def test_history_limit(self):
        """Test HISTORY_LIMIT constant."""
        assert HISTORY_LIMIT == 10

    def test_memory_limit(self):
        """Test MEMORY_LIMIT constant."""
        assert MEMORY_LIMIT == 20

    def test_error_pattern_limit(self):
        """Test ERROR_PATTERN_LIMIT constant."""
        assert ERROR_PATTERN_LIMIT == 50


# =============================================================================
# FILE LIMITS TESTS
# =============================================================================


class TestFileLimits:
    """Tests for file limit constants."""

    def test_max_file_size(self):
        """Test MAX_FILE_SIZE constant."""
        assert MAX_FILE_SIZE == 1_000_000

    def test_max_content_length(self):
        """Test MAX_CONTENT_LENGTH constant."""
        assert MAX_CONTENT_LENGTH == 1_000_000

    def test_max_filename_length(self):
        """Test MAX_FILENAME_LENGTH constant."""
        assert MAX_FILENAME_LENGTH == 255

    def test_max_files_per_patch(self):
        """Test MAX_FILES_PER_PATCH constant."""
        assert MAX_FILES_PER_PATCH == 50

    def test_truncate_preview_length(self):
        """Test TRUNCATE_PREVIEW_LENGTH constant."""
        assert TRUNCATE_PREVIEW_LENGTH == 50

    def test_truncate_error_message(self):
        """Test TRUNCATE_ERROR_MESSAGE constant."""
        assert TRUNCATE_ERROR_MESSAGE == 500

    def test_truncate_solution(self):
        """Test TRUNCATE_SOLUTION constant."""
        assert TRUNCATE_SOLUTION == 2000


# =============================================================================
# VERIFICATION CONFIGURATION TESTS
# =============================================================================


class TestVerificationConfiguration:
    """Tests for verification configuration constants."""

    def test_lint_issue_limit(self):
        """Test LINT_ISSUE_LIMIT constant."""
        assert LINT_ISSUE_LIMIT == 10

    def test_failed_test_limit(self):
        """Test FAILED_TEST_LIMIT constant."""
        assert FAILED_TEST_LIMIT == 5

    def test_verification_result_limit(self):
        """Test VERIFICATION_RESULT_LIMIT constant."""
        assert VERIFICATION_RESULT_LIMIT == 5

    def test_suggestion_limit(self):
        """Test SUGGESTION_LIMIT constant."""
        assert SUGGESTION_LIMIT == 3


# =============================================================================
# VECTOR MEMORY CONFIGURATION TESTS
# =============================================================================


class TestVectorMemoryConfiguration:
    """Tests for vector memory configuration constants."""

    def test_vector_similarity_threshold(self):
        """Test VECTOR_SIMILARITY_THRESHOLD constant."""
        assert VECTOR_SIMILARITY_THRESHOLD == 0.5

    def test_vector_default_results(self):
        """Test VECTOR_DEFAULT_RESULTS constant."""
        assert VECTOR_DEFAULT_RESULTS == 3

    def test_vector_collection_name(self):
        """Test VECTOR_COLLECTION_NAME constant."""
        assert VECTOR_COLLECTION_NAME == "boring_knowledge"


# =============================================================================
# STATUS STRINGS TESTS
# =============================================================================


class TestStatusStrings:
    """Tests for status string constants."""

    def test_status_success(self):
        """Test STATUS_SUCCESS constant."""
        assert STATUS_SUCCESS == "SUCCESS"

    def test_status_failed(self):
        """Test STATUS_FAILED constant."""
        assert STATUS_FAILED == "FAILED"

    def test_status_partial(self):
        """Test STATUS_PARTIAL constant."""
        assert STATUS_PARTIAL == "PARTIAL"

    def test_status_in_progress(self):
        """Test STATUS_IN_PROGRESS constant."""
        assert STATUS_IN_PROGRESS == "IN_PROGRESS"

    def test_status_complete(self):
        """Test STATUS_COMPLETE constant."""
        assert STATUS_COMPLETE == "COMPLETE"


# =============================================================================
# LOG LEVELS TESTS
# =============================================================================


class TestLogLevels:
    """Tests for log level constants."""

    def test_log_info(self):
        """Test LOG_INFO constant."""
        assert LOG_INFO == "INFO"

    def test_log_warn(self):
        """Test LOG_WARN constant."""
        assert LOG_WARN == "WARN"

    def test_log_error(self):
        """Test LOG_ERROR constant."""
        assert LOG_ERROR == "ERROR"

    def test_log_success(self):
        """Test LOG_SUCCESS constant."""
        assert LOG_SUCCESS == "SUCCESS"

    def test_log_debug(self):
        """Test LOG_DEBUG constant."""
        assert LOG_DEBUG == "DEBUG"
