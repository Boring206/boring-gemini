# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Vibe Analysis Data Structures.

Defines the common data objects used across different language handlers.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CodeIssue:
    """Represents a single issue found during code review."""

    category: str  # e.g., "Naming", "Error Handling", "Performance", "Security"
    message: str
    severity: str  # "high", "medium", "low"
    line: int
    suggestion: Optional[str] = None


@dataclass
class CodeFunction:
    """Represents a function definition."""

    name: str
    args: list[str]
    docstring: Optional[str]
    lineno: int
    is_async: bool = False
    is_exported: bool = True  # For JS/TS


@dataclass
class CodeClass:
    """Represents a class definition."""

    name: str
    methods: list[str]
    docstring: Optional[str]
    lineno: int
    is_exported: bool = True


@dataclass
class DocItem:
    """Documentation for a code element (function/class)."""

    name: str
    type: str  # function, class, method
    docstring: str
    signature: str
    line_number: int
    params: list[str] = field(default_factory=list)


@dataclass
class DocResult:
    """Documentation extraction result."""

    file_path: str
    module_doc: str
    items: list[DocItem] = field(default_factory=list)
    score: int = 100  # 0-100 score based on issues


@dataclass
class ReviewResult:
    """Result of a code review analysis."""

    file_path: str
    issues: list[CodeIssue] = field(default_factory=list)
    score: int = 100  # 0-100 score based on issues


@dataclass
class TestGenResult:
    """Result of test generation analysis."""

    file_path: str
    functions: list[CodeFunction] = field(default_factory=list)
    classes: list[CodeClass] = field(default_factory=list)
    module_name: str = ""
    source_language: str = "python"  # python, javascript, typescript, etc.
