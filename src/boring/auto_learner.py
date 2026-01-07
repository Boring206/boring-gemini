"""
Auto Learner Module for Boring MCP

Automatically detects and learns from error→solution patterns
without requiring explicit AI calls to boring_learn_pattern.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ErrorSolutionPair:
    """Represents a detected error and its solution."""

    error_type: str
    error_message: str
    solution_summary: str
    file_context: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class AutoLearner:
    """
    Automatically learns from AI interactions.

    Detects patterns like:
    - Error messages followed by fixes
    - Repeated code patterns
    - Successful workflow completions
    """

    # Common error patterns to detect
    ERROR_PATTERNS = [
        # Python errors
        (r"(?:Error|Exception):\s*(.+)", "python_error"),
        (r"ModuleNotFoundError:\s*(.+)", "import_error"),
        (r"ImportError:\s*(.+)", "import_error"),
        (r"TypeError:\s*(.+)", "type_error"),
        (r"AttributeError:\s*(.+)", "attribute_error"),
        (r"SyntaxError:\s*(.+)", "syntax_error"),
        # JavaScript/TypeScript errors
        (r"ReferenceError:\s*(.+)", "js_reference_error"),
        (r"Cannot find module\s*['\"](.+)['\"]", "js_import_error"),
        # General patterns
        (r"FAILED.*?(\w+Error)", "test_failure"),
        (r"error\[E\d+\]:\s*(.+)", "rust_error"),
        (r"error:\s*(.+)", "generic_error"),
    ]

    # Solution indicators
    SOLUTION_INDICATORS = [
        "fixed",
        "resolved",
        "solved",
        "corrected",
        "updated",
        "changed to",
        "replaced with",
        "added",
        "removed",
        "installed",
        "pip install",
        "npm install",
    ]

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self._pending_errors: list[ErrorSolutionPair] = []

    def analyze_response(self, response_text: str) -> list[ErrorSolutionPair]:
        """
        Analyze AI response text for error→solution pairs.

        Args:
            response_text: The AI's response text

        Returns:
            List of detected error-solution pairs
        """
        pairs = []

        # Split response into sections (errors tend to be followed by solutions)
        sections = response_text.split("\n\n")

        for i, section in enumerate(sections):
            # Check for error patterns
            for pattern, error_type in self.ERROR_PATTERNS:
                match = re.search(pattern, section, re.IGNORECASE)
                if match:
                    error_msg = match.group(1) if match.groups() else match.group(0)

                    # Look for solution in next sections
                    solution = self._find_solution(
                        sections[i + 1 :] if i + 1 < len(sections) else []
                    )

                    if solution:
                        pairs.append(
                            ErrorSolutionPair(
                                error_type=error_type,
                                error_message=error_msg[:200],
                                solution_summary=solution[:300],
                            )
                        )
                    else:
                        # Store as pending - solution might come later
                        self._pending_errors.append(
                            ErrorSolutionPair(
                                error_type=error_type,
                                error_message=error_msg[:200],
                                solution_summary="",
                            )
                        )
                    break  # Only match first error pattern per section

        return pairs

    def _find_solution(self, sections: list[str]) -> Optional[str]:
        """Find solution text in subsequent sections."""
        for section in sections[:3]:  # Look in next 3 sections max
            section_lower = section.lower()
            for indicator in self.SOLUTION_INDICATORS:
                if indicator in section_lower:
                    # Extract the relevant part
                    lines = section.strip().split("\n")
                    # Return first 3 lines as solution summary
                    return "\n".join(lines[:3])
        return None

    def record_success(self, context: str = "") -> list[ErrorSolutionPair]:
        """
        Record that a task was successful, resolving pending errors.

        Args:
            context: Additional context about what succeeded

        Returns:
            List of resolved error-solution pairs
        """
        resolved = []

        for pending in self._pending_errors:
            if not pending.solution_summary:
                pending.solution_summary = context or "Task completed successfully"
                resolved.append(pending)

        self._pending_errors = []
        return resolved

    def learn_to_brain(self, project_root: Path) -> dict:
        """
        Transfer learned patterns to BrainManager.

        Args:
            project_root: Project root for BrainManager

        Returns:
            Result of learning operation
        """
        from .brain_manager import BrainManager

        brain = BrainManager(project_root)
        learned_count = 0

        # Get all resolved pairs
        pairs = self.record_success()

        for pair in pairs:
            if pair.solution_summary:
                result = brain.learn_pattern(
                    pattern_type=pair.error_type,
                    description=f"Auto-learned: {pair.error_type}",
                    context=pair.error_message,
                    solution=pair.solution_summary,
                )
                if result.get("status") in ("CREATED", "UPDATED"):
                    learned_count += 1

        return {"status": "SUCCESS", "patterns_learned": learned_count}


# Singleton instance per project
_learners: dict[str, AutoLearner] = {}


def get_auto_learner(project_root: Path) -> AutoLearner:
    """Get or create AutoLearner for project."""
    key = str(project_root.resolve())
    if key not in _learners:
        _learners[key] = AutoLearner(project_root)
    return _learners[key]


def auto_learn_from_response(project_root: Path, response_text: str) -> dict:
    """
    Convenience function to analyze response and learn patterns.

    Args:
        project_root: Project directory
        response_text: AI response to analyze

    Returns:
        Learning result
    """
    learner = get_auto_learner(project_root)
    pairs = learner.analyze_response(response_text)

    if pairs:
        return learner.learn_to_brain(project_root)

    return {"status": "NO_PATTERNS", "patterns_learned": 0}
