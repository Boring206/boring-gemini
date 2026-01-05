"""
Error Diagnostics Module (V10.15)

Provides detailed error messages and fix suggestions for common issues.
Analyzes verification failures, test errors, and lint warnings to suggest fixes.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .config import settings
from .logger import get_logger

logger = get_logger("error_diagnostics")


@dataclass
class DiagnosticResult:
    """A diagnostic result with error details and fix suggestions."""

    error_type: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    severity: str = "error"  # error, warning, info
    suggestions: list[str] = field(default_factory=list)
    auto_fixable: bool = False
    fix_command: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "type": self.error_type,
            "message": self.message,
            "file": self.file_path,
            "line": self.line_number,
            "column": self.column,
            "severity": self.severity,
            "suggestions": self.suggestions,
            "autoFixable": self.auto_fixable,
            "fixCommand": self.fix_command,
        }


class ErrorDiagnostics:
    """
    V10.15: Detailed error diagnostics with fix suggestions.

    Features:
    - Parses verification errors and explains them
    - Provides actionable fix suggestions
    - Identifies auto-fixable issues
    - Generates CLI commands for fixes

    Usage:
        diagnostics = ErrorDiagnostics()
        results = diagnostics.analyze_error(error_output)
        for result in results:
            print(result.message)
            for suggestion in result.suggestions:
                print(f"  - {suggestion}")
    """

    # Common error patterns and their explanations/fixes
    ERROR_PATTERNS = {
        # Python Syntax Errors
        r"SyntaxError: invalid syntax": {
            "type": "syntax_error",
            "message": "Python syntax error detected",
            "suggestions": [
                "Check for missing colons (:) after if/for/def/class statements",
                "Ensure all parentheses/brackets are properly closed",
                "Verify string quotes are matched",
            ],
        },
        r"IndentationError": {
            "type": "indentation_error",
            "message": "Inconsistent indentation",
            "suggestions": [
                "Use consistent indentation (4 spaces recommended)",
                "Don't mix tabs and spaces",
                "Check indentation after control structures",
            ],
            "auto_fix": "ruff check --fix --select=I",
        },
        r"NameError: name '(.+)' is not defined": {
            "type": "name_error",
            "message": "Undefined variable or function",
            "suggestions": [
                "Add missing import statement",
                "Check for typos in variable/function names",
                "Ensure variable is defined before use",
            ],
        },
        r"ImportError: cannot import name '(.+)'": {
            "type": "import_error",
            "message": "Import failed",
            "suggestions": [
                "Verify the module is installed: pip install <package>",
                "Check for circular imports",
                "Ensure the name exists in the target module",
            ],
        },
        r"ModuleNotFoundError: No module named '(.+)'": {
            "type": "module_not_found",
            "message": "Module not installed",
            "suggestions": [
                "Install the missing module: pip install {match}",
                "Check if running in correct virtual environment",
                "Verify PYTHONPATH includes the module location",
            ],
        },
        # Ruff/Lint Errors
        r"F401 \[.*\] `(.+)` imported but unused": {
            "type": "unused_import",
            "message": "Unused import detected",
            "suggestions": ["Remove the unused import", "Use the imported module in your code"],
            "auto_fix": "ruff check --fix --select=F401",
        },
        r"E501 \[.*\] Line too long \((\d+) > (\d+)\)": {
            "type": "line_too_long",
            "message": "Line exceeds maximum length",
            "suggestions": [
                "Break line into multiple lines",
                "Use parentheses for implicit line continuation",
                "Extract long expressions into variables",
            ],
        },
        # TypeScript/JavaScript Errors
        r"Cannot find module '(.+)'": {
            "type": "module_not_found",
            "message": "Node module not found",
            "suggestions": [
                "Install the missing module: npm install {match}",
                "Check if node_modules directory exists",
                "Run npm install to restore dependencies",
            ],
        },
        r"Property '(.+)' does not exist on type '(.+)'": {
            "type": "type_error",
            "message": "TypeScript type error",
            "suggestions": [
                "Add the missing property to the type definition",
                "Use type assertion if you're sure the property exists",
                "Check the type definition for typos",
            ],
        },
        # Test Failures
        r"FAILED (.+)::(.+) - (.+)": {
            "type": "test_failure",
            "message": "Test failed",
            "suggestions": [
                "Check the assertion message for expected vs actual values",
                "Review the test logic for correctness",
                "Run the test in isolation with -vvs for more details",
            ],
        },
        r"AssertionError: (.+)": {
            "type": "assertion_error",
            "message": "Assertion failed",
            "suggestions": [
                "Compare expected vs actual values",
                "Check if test fixtures are set up correctly",
                "Add print statements or breakpoints to debug",
            ],
        },
        # Git Errors
        r"fatal: not a git repository": {
            "type": "git_error",
            "message": "Not in a Git repository",
            "suggestions": [
                "Initialize a Git repository: git init",
                "Navigate to the correct project directory",
            ],
        },
        # General Errors
        r"TypeError: (.+)": {
            "type": "type_error",
            "message": "Type mismatch error",
            "suggestions": [
                "Check function argument types",
                "Verify object types before operations",
                "Add type checking or validation",
            ],
        },
        r"ValueError: (.+)": {
            "type": "value_error",
            "message": "Invalid value",
            "suggestions": [
                "Validate input values before processing",
                "Add bounds checking for numeric values",
                "Handle edge cases explicitly",
            ],
        },
    }

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or settings.PROJECT_ROOT

    def analyze_error(self, error_output: str) -> list[DiagnosticResult]:
        """
        Analyze error output and return diagnostic results.

        Args:
            error_output: Raw error output from verification/tests

        Returns:
            List of DiagnosticResult with explanations and suggestions
        """
        results = []

        for pattern, info in self.ERROR_PATTERNS.items():
            matches = re.finditer(pattern, error_output, re.MULTILINE)
            for match in matches:
                # Format suggestions with captured groups
                suggestions = []
                for suggestion in info.get("suggestions", []):
                    try:
                        if "{match}" in suggestion and match.groups():
                            suggestion = suggestion.replace("{match}", match.group(1))
                    except IndexError:
                        pass
                    suggestions.append(suggestion)

                result = DiagnosticResult(
                    error_type=info["type"],
                    message=info["message"],
                    suggestions=suggestions,
                    auto_fixable="auto_fix" in info,
                    fix_command=info.get("auto_fix"),
                )

                # Try to extract file/line info
                file_line_match = re.search(
                    r'(?:File "([^"]+)", line (\d+))|(?:(\S+\.py):(\d+))',
                    error_output[max(0, match.start() - 200) : match.end() + 50],
                )
                if file_line_match:
                    groups = file_line_match.groups()
                    result.file_path = groups[0] or groups[2]
                    result.line_number = int(groups[1] or groups[3] or 0)

                results.append(result)

        # If no patterns matched, provide generic diagnostic
        if not results and error_output.strip():
            results.append(
                DiagnosticResult(
                    error_type="unknown_error",
                    message="Unrecognized error",
                    suggestions=[
                        "Check the full error output for details",
                        "Search for the error message online",
                        "Try running with verbose mode for more info",
                    ],
                )
            )

        return results

    def analyze_verification_result(self, result) -> list[DiagnosticResult]:
        """Analyze a VerificationResult and return diagnostics."""
        diagnostics = []

        if not result.passed:
            # Analyze the main message
            diagnostics.extend(self.analyze_error(result.message))

            # Analyze each detail
            for detail in result.details:
                diagnostics.extend(self.analyze_error(detail))

        return diagnostics

    def format_diagnostic(self, diagnostic: DiagnosticResult) -> str:
        """Format a diagnostic result for display."""
        lines = []

        # Header
        icon = (
            "❌"
            if diagnostic.severity == "error"
            else ("⚠️" if diagnostic.severity == "warning" else "ℹ️")
        )
        location = ""
        if diagnostic.file_path:
            location = f" in {diagnostic.file_path}"
            if diagnostic.line_number:
                location += f":{diagnostic.line_number}"

        lines.append(f"{icon} **{diagnostic.error_type}**{location}")
        lines.append(f"   {diagnostic.message}")

        # Suggestions
        if diagnostic.suggestions:
            lines.append("   **Suggestions:**")
            for suggestion in diagnostic.suggestions:
                lines.append(f"   • {suggestion}")

        # Auto-fix command
        if diagnostic.auto_fixable and diagnostic.fix_command:
            lines.append(f"   **Auto-fix:** `{diagnostic.fix_command}`")

        return "\n".join(lines)

    def get_quick_fixes(self, error_output: str) -> list[tuple[str, str]]:
        """
        Get list of quick-fix commands for auto-fixable issues.

        Returns:
            List of (description, command) tuples
        """
        diagnostics = self.analyze_error(error_output)
        fixes = []

        for diag in diagnostics:
            if diag.auto_fixable and diag.fix_command:
                fixes.append((diag.message, diag.fix_command))

        # Add common fix commands
        if any(d.error_type == "unused_import" for d in diagnostics):
            fixes.append(("Fix all unused imports", "ruff check --fix --select=F401"))

        if any(d.error_type == "line_too_long" for d in diagnostics):
            fixes.append(("Auto-format code", "ruff format"))

        return list(set(fixes))  # Remove duplicates
