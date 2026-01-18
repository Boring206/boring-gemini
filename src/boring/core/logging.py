# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Unified Structured Logging for Boring.

Supports standard text and structured JSON logging for automated analysis.
"""

import json
import logging
import sys
from datetime import datetime

from boring.core.config import settings
from boring.core.telemetry import CORRELATION_ID


class BoringJSONFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
            "correlation_id": CORRELATION_ID.get(),
        }

        # Add extra attributes if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(level: str = None, json_format: bool = False):
    """
    Configure global logging.

    Args:
        level: Log level (DEBUG, INFO, etc.)
        json_format: Whether to use JSON formatting for stdout
    """
    log_level = level or settings.LOG_LEVEL
    root_logger = logging.getLogger()

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(log_level)

    # Stdout Handler
    handler = logging.StreamHandler(sys.stdout)
    if json_format or settings.LOG_LEVEL == "JSON":
        handler.setFormatter(BoringJSONFormatter())
    else:
        # Standard elegant Boring format
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s", datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)

    root_logger.addHandler(handler)

    # Critical Log Handler (V14.8)
    if settings.LOG_DIR:
        try:
            settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
            critical_handler = logging.FileHandler(
                settings.LOG_DIR / "critical.log", encoding="utf-8"
            )
            critical_handler.setLevel(logging.ERROR)

            # Always use JSON for critical logs for improved observability
            critical_handler.setFormatter(BoringJSONFormatter())
            root_logger.addHandler(critical_handler)
        except Exception as e:
            # Fallback if FS is not writable
            handler.stream.write(f"Warning: Failed to setup critical.log: {e}\n")

    # Disable heavy logs from dependencies
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("pydantic").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.debug(f"Logging initialized at level {log_level} (JSON={json_format})")
