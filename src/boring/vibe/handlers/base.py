# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Base Language Handler.

Abstract base class for language-specific analysis handlers.
"""

from abc import ABC, abstractmethod

from ..analysis import ReviewResult, TestGenResult


class BaseHandler(ABC):
    """Abstract base class for all language handlers."""

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """List of file extensions supported by this handler (e.g., ['.py'])."""
        pass

    @property
    @abstractmethod
    def language_name(self) -> str:
        """Name of the language (e.g., 'Python')."""
        pass

    @abstractmethod
    def analyze_for_test_gen(self, file_path: str, source_code: str) -> TestGenResult:
        """
        Analyze source code to extract structure for test generation.
        """
        pass

    @abstractmethod
    def perform_code_review(
        self, file_path: str, source_code: str, focus: str = "all"
    ) -> ReviewResult:
        """
        Perform code review on the source code.

        Args:
            file_path: Path to the file
            source_code: Content of the file
            focus: Focus area ('all', 'naming', 'error_handling', 'performance', 'security')

        Returns:
            ReviewResult containing found issues
        """
        pass

    @abstractmethod
    def generate_test_code(self, result: TestGenResult, project_root: str) -> str:
        """
        Generate test code based on analysis result.

        Args:
            result: The TestGenResult from analyze_for_test_gen
            project_root: Root path of the project (for import resolution)

        Returns:
            String containing the generated test code
        """
        pass

    @abstractmethod
    def extract_dependencies(self, file_path: str, source_code: str) -> list[str]:
        """
        Extract list of imported modules/dependencies.

        Args:
            file_path: Path to the file
            source_code: Content of the file

        Returns:
            List of imported module names (e.g. ['os', 'numpy', './utils'])
        """
        pass
