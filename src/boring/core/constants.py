"""
Constants Module for Boring V4.0

Centralizes all magic numbers and configuration constants.
"""

from typing import Final

# =============================================================================
# API CONFIGURATION
# =============================================================================

# Token limits
MAX_OUTPUT_TOKENS: Final[int] = 8192
MAX_INPUT_TOKENS: Final[int] = 128000
DEFAULT_TEMPERATURE: Final[float] = 0.7

# Timeouts (seconds)
DEFAULT_TIMEOUT_SECONDS: Final[int] = 900  # 15 minutes
API_REQUEST_TIMEOUT: Final[int] = 120
SUBPROCESS_TIMEOUT: Final[int] = 30
TEST_TIMEOUT: Final[int] = 120

# Retry configuration
MAX_RETRIES: Final[int] = 3
BASE_RETRY_DELAY: Final[float] = 2.0
MAX_RETRY_DELAY: Final[float] = 60.0

# =============================================================================
# LOOP CONFIGURATION
# =============================================================================

MAX_LOOPS: Final[int] = 100
MAX_HOURLY_CALLS: Final[int] = 50
MAX_CONSECUTIVE_FAILURES: Final[int] = 3
MAX_CONSECUTIVE_TEST_LOOPS: Final[int] = 3
MAX_CONSECUTIVE_DONE_SIGNALS: Final[int] = 2

# Context limits
HISTORY_LIMIT: Final[int] = 10
MEMORY_LIMIT: Final[int] = 20
ERROR_PATTERN_LIMIT: Final[int] = 50

# =============================================================================
# FILE LIMITS
# =============================================================================

MAX_FILE_SIZE: Final[int] = 1_000_000  # 1MB
MAX_CONTENT_LENGTH: Final[int] = 1_000_000
MAX_FILENAME_LENGTH: Final[int] = 255
MAX_FILES_PER_PATCH: Final[int] = 50

# Truncation
TRUNCATE_PREVIEW_LENGTH: Final[int] = 50
TRUNCATE_ERROR_MESSAGE: Final[int] = 500
TRUNCATE_SOLUTION: Final[int] = 2000

# =============================================================================
# VERIFICATION CONFIGURATION
# =============================================================================

LINT_ISSUE_LIMIT: Final[int] = 10
FAILED_TEST_LIMIT: Final[int] = 5
VERIFICATION_RESULT_LIMIT: Final[int] = 5
SUGGESTION_LIMIT: Final[int] = 3

# =============================================================================
# VECTOR MEMORY CONFIGURATION
# =============================================================================

VECTOR_SIMILARITY_THRESHOLD: Final[float] = 0.5
VECTOR_DEFAULT_RESULTS: Final[int] = 3
VECTOR_COLLECTION_NAME: Final[str] = "boring_knowledge"

# =============================================================================
# STATUS STRINGS
# =============================================================================

STATUS_SUCCESS: Final[str] = "SUCCESS"
STATUS_ERROR: Final[str] = "ERROR"  # V11.2.3: For BoringResult compatibility
STATUS_FAILED: Final[str] = "FAILED"
STATUS_PARTIAL: Final[str] = "PARTIAL"
STATUS_IN_PROGRESS: Final[str] = "IN_PROGRESS"
STATUS_COMPLETE: Final[str] = "COMPLETE"

# =============================================================================
# LOG LEVELS
# =============================================================================

LOG_INFO: Final[str] = "INFO"
LOG_WARN: Final[str] = "WARN"
LOG_ERROR: Final[str] = "ERROR"
LOG_SUCCESS: Final[str] = "SUCCESS"
LOG_DEBUG: Final[str] = "DEBUG"
