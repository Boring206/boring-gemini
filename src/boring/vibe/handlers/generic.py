# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Generic Language Handler.

Fallback handler for unsupported file types.
"""

from ..analysis import DocResult, ReviewResult, TestGenResult
from .base import BaseHandler


class GenericHandler(BaseHandler):
    """Fallback handler for any text file."""

    @property
    def supported_extensions(self) -> list[str]:
        return []  # Registered as default handler manually

    @property
    def language_name(self) -> str:
        return "Generic"

    def analyze_for_test_gen(self, file_path: str, source_code: str) -> TestGenResult:
        """No test gen support for generic files."""
        return TestGenResult(file_path=file_path, functions=[], classes=[])

    def perform_code_review(
        self, file_path: str, source_code: str, focus: str = "all"
    ) -> ReviewResult:
        """Basic generic review."""
        # Could check for TODOs, FIXMEs, or very long lines
        return ReviewResult(file_path=file_path, issues=[])

    def generate_test_code(self, result: TestGenResult, project_root: str) -> str:
        return "# Test generation not supported for this file type"

    def extract_dependencies(self, file_path: str, source_code: str) -> list[str]:
        """Generic dependency extraction is hard without knowing syntax."""
        return []

    def extract_documentation(self, file_path: str, source_code: str) -> DocResult:
        """No doc support for generic files."""
        return DocResult(file_path=file_path, module_doc="", items=[])
