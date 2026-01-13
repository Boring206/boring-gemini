# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Boring Metrics Module

Provides project health and integrity metrics.
"""

from boring.metrics.integrity import (
    IntegrityReport,
    calculate_integrity_score,
    display_integrity_report,
)

__all__ = [
    "calculate_integrity_score",
    "display_integrity_report",
    "IntegrityReport",
]
