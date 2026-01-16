"""
Predictive Error Detection Engine for Boring V14.0

Uses learned patterns to predict and warn about potential errors
BEFORE they occur, enabling proactive code quality.

Features:
- Pattern-based risk assessment
- Historical error correlation
- Real-time code analysis
- Proactive warnings
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PredictedIssue:
    """A predicted potential issue."""

    severity: str  # "info", "warning", "error", "critical"
    category: str  # "null_check", "resource_leak", "type_error", etc.
    message: str
    file_path: str | None
    line_number: int | None
    code_snippet: str | None
    confidence: float  # 0.0 to 1.0
    pattern_id: str | None  # Reference to Brain pattern
    suggested_fix: str | None


@dataclass
class PredictionReport:
    """Report of predicted issues for a code change."""

    issues: list[PredictedIssue]
    files_analyzed: int
    patterns_checked: int
    overall_risk: str  # "low", "medium", "high"


# Common anti-patterns to detect
ANTI_PATTERNS = {
    "null_check_missing": {
        "pattern": r"(\w+)\.([\w_]+)\s*\(",
        "context": "function call on potentially None value",
        "severity": "warning",
        "category": "null_check",
    },
    "bare_except": {
        "pattern": r"except\s*:",
        "context": "bare except catches all exceptions including KeyboardInterrupt",
        "severity": "warning",
        "category": "exception_handling",
    },
    "hardcoded_secret": {
        "pattern": r"(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]",
        "context": "potential hardcoded secret",
        "severity": "critical",
        "category": "security",
    },
    "sql_injection": {
        "pattern": r"execute\s*\(\s*[f'\"].*%s",
        "context": "potential SQL injection vulnerability",
        "severity": "critical",
        "category": "security",
    },
    "infinite_loop_risk": {
        "pattern": r"while\s+True\s*:",
        "context": "infinite loop without obvious break condition",
        "severity": "info",
        "category": "logic",
    },
    "mutable_default": {
        "pattern": r"def\s+\w+\s*\([^)]*=\s*(\[\]|\{\})",
        "context": "mutable default argument",
        "severity": "warning",
        "category": "python_gotcha",
    },
    "global_variable": {
        "pattern": r"^\s*global\s+\w+",
        "context": "global variable usage can cause unexpected state",
        "severity": "info",
        "category": "code_smell",
    },
}


class Predictor:
    """
    Predictive error detection engine.

    Analyzes code changes and predicts potential issues
    based on learned patterns and static analysis.
    """

    def __init__(self, project_root: Path | None = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.brain: Any | None = None
        self._pattern_cache: dict[str, list] = {}

    def _get_brain(self) -> Any | None:
        """Lazy-load Brain Manager."""
        if self.brain is None:
            try:
                from ..intelligence import BrainManager

                self.brain = BrainManager(self.project_root)
            except ImportError:
                pass
        return self.brain

    def analyze_file(self, file_path: Path) -> list[PredictedIssue]:
        """
        Analyze a single file for potential issues.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List of predicted issues
        """
        if not file_path.exists():
            return []

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
            return []

        issues = []

        # Check static anti-patterns
        issues.extend(self._check_static_patterns(content, str(file_path)))
        issues.extend(self._check_python_n_plus_one(content, str(file_path)))
        issues.extend(self._check_js_memory_leak(content, str(file_path)))

        # Check Brain patterns
        issues.extend(self._check_brain_patterns(content, str(file_path)))

        return issues

    def analyze_diff(self, diff_content: str, file_path: str) -> list[PredictedIssue]:
        """
        Analyze a diff for potential issues in added lines.

        Args:
            diff_content: The diff content (unified format)
            file_path: Path to the file being changed

        Returns:
            List of predicted issues
        """
        issues = []

        # Extract added lines from diff
        added_lines = []
        line_numbers = []
        current_line = 0

        for line in diff_content.split("\n"):
            if line.startswith("@@"):
                # Parse line number from hunk header
                match = re.search(r"\+(\d+)", line)
                if match:
                    current_line = int(match.group(1)) - 1
            elif line.startswith("+") and not line.startswith("+++"):
                current_line += 1
                added_lines.append(line[1:])
                line_numbers.append(current_line)
            elif not line.startswith("-"):
                current_line += 1

        # Analyze added content
        added_content = "\n".join(added_lines)
        for issue in self._check_static_patterns(added_content, file_path):
            # Try to map to specific line number
            if issue.code_snippet:
                for i, line in enumerate(added_lines):
                    if issue.code_snippet in line:
                        issue.line_number = line_numbers[i] if i < len(line_numbers) else None
                        break
            issues.append(issue)

        issues.extend(self._check_python_n_plus_one(added_content, file_path))
        issues.extend(self._check_js_memory_leak(added_content, file_path))

        return issues

    def _check_static_patterns(self, content: str, file_path: str) -> list[PredictedIssue]:
        """Check content against static anti-patterns."""
        issues = []

        for pattern_name, pattern_info in ANTI_PATTERNS.items():
            matches = re.finditer(pattern_info["pattern"], content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                # Find line number
                line_num = content[: match.start()].count("\n") + 1

                issues.append(
                    PredictedIssue(
                        severity=pattern_info["severity"],
                        category=pattern_info["category"],
                        message=pattern_info["context"],
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=match.group(0)[:50],
                        confidence=0.8,
                        pattern_id=pattern_name,
                        suggested_fix=self._get_fix_suggestion(pattern_name),
                    )
                )

        return issues

    def _check_python_n_plus_one(self, content: str, file_path: str) -> list[PredictedIssue]:
        """Heuristic detection of Python N+1 query patterns."""
        if not file_path.endswith(".py"):
            return []
        issues: list[PredictedIssue] = []
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("for ") and " in " in stripped and stripped.endswith(":"):
                window = "\n".join(lines[idx + 1 : idx + 8])
                if any(
                    token in window for token in (".objects.", ".filter(", ".get(", ".exclude(")
                ):
                    issues.append(
                        PredictedIssue(
                            severity="warning",
                            category="performance",
                            message="Potential N+1 query: database access inside loop",
                            file_path=file_path,
                            line_number=idx + 1,
                            code_snippet=stripped,
                            confidence=0.55,
                            pattern_id="python_n_plus_one_query",
                            suggested_fix=(
                                "Move queries outside the loop or use select_related/prefetch_related."
                            ),
                        )
                    )
        return issues

    def _check_js_memory_leak(self, content: str, file_path: str) -> list[PredictedIssue]:
        """Heuristic detection of JS event listener leaks."""
        if not file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
            return []
        issues: list[PredictedIssue] = []
        lines = content.splitlines()
        add_lines = [i for i, line in enumerate(lines) if "addEventListener(" in line]
        if add_lines:
            remove_count = content.count("removeEventListener(")
            if remove_count == 0 or remove_count < len(add_lines):
                first_line = add_lines[0]
                issues.append(
                    PredictedIssue(
                        severity="warning",
                        category="memory_leak",
                        message="Potential memory leak: addEventListener without removeEventListener",
                        file_path=file_path,
                        line_number=first_line + 1,
                        code_snippet=lines[first_line].strip(),
                        confidence=0.5,
                        pattern_id="js_event_listener_leak",
                        suggested_fix="Remove event listeners during cleanup/unmount.",
                    )
                )
        return issues

    def _check_brain_patterns(self, content: str, file_path: str) -> list[PredictedIssue]:
        """Check content against learned Brain patterns."""
        issues = []
        brain = self._get_brain()

        if not brain:
            return issues

        try:
            # Query patterns related to errors
            error_patterns = brain.get_relevant_patterns(
                f"error {file_path} common mistakes", limit=10
            )

            for pattern in error_patterns:
                pattern_type = pattern.get("pattern_type", "")
                if pattern_type != "error_solution":
                    continue

                context = pattern.get("context", "")
                solution = pattern.get("solution", "")

                # Check if pattern context appears in content
                if context and len(context) > 20:
                    # Extract key phrases from context
                    key_phrases = self._extract_key_phrases(context)
                    for phrase in key_phrases:
                        if phrase.lower() in content.lower():
                            issues.append(
                                PredictedIssue(
                                    severity="warning",
                                    category="learned_pattern",
                                    message=f"Similar issue encountered before: {pattern.get('description', '')[:50]}",
                                    file_path=file_path,
                                    line_number=None,
                                    code_snippet=phrase[:50],
                                    confidence=pattern.get("success_count", 1) / 10.0,
                                    pattern_id=pattern.get("pattern_id"),
                                    suggested_fix=solution[:100] if solution else None,
                                )
                            )
                            break
        except Exception as e:
            logger.debug(f"Brain pattern check failed: {e}")

        return issues

    def _extract_key_phrases(self, text: str) -> list[str]:
        """Extract key phrases from text for matching."""
        # Simple extraction: look for code-like patterns
        phrases = []

        # Extract function calls
        phrases.extend(re.findall(r"\w+\([^)]*\)", text))

        # Extract error types
        phrases.extend(re.findall(r"\w+Error", text))
        phrases.extend(re.findall(r"\w+Exception", text))

        # Extract variable patterns
        phrases.extend(re.findall(r"\w+\.\w+", text))

        return phrases[:5]  # Limit to avoid performance issues

    def _get_fix_suggestion(self, pattern_name: str) -> str | None:
        """Get fix suggestion for a known anti-pattern."""
        suggestions = {
            "null_check_missing": "Add null/None check before accessing",
            "bare_except": "Use specific exception types (e.g., except ValueError:)",
            "hardcoded_secret": "Move to environment variable or secrets manager",
            "sql_injection": "Use parameterized queries with ?/% placeholders",
            "infinite_loop_risk": "Ensure break condition or timeout exists",
            "mutable_default": "Use None as default and initialize in function body",
            "global_variable": "Consider passing as parameter or using class attribute",
        }
        return suggestions.get(pattern_name)

    def generate_report(self, file_paths: list[Path]) -> PredictionReport:
        """
        Generate a prediction report for multiple files.

        Args:
            file_paths: List of files to analyze

        Returns:
            PredictionReport with all findings
        """
        all_issues = []

        for file_path in file_paths:
            if file_path.suffix in {".py", ".js", ".ts", ".tsx", ".jsx"}:
                issues = self.analyze_file(file_path)
                all_issues.extend(issues)

        # Calculate overall risk
        critical_count = sum(1 for i in all_issues if i.severity == "critical")
        warning_count = sum(1 for i in all_issues if i.severity == "warning")

        if critical_count > 0:
            risk = "high"
        elif warning_count > 3:
            risk = "medium"
        else:
            risk = "low"

        return PredictionReport(
            issues=all_issues,
            files_analyzed=len(file_paths),
            patterns_checked=len(ANTI_PATTERNS),
            overall_risk=risk,
        )

    def analyze_regression(
        self,
        error_message: str,
        target_file: str | None = None,
        max_commits: int = 10,
    ) -> dict:
        """
        AI Git Bisect: Analyze recent commits to find the likely source of a bug.

        Args:
            error_message: The error message to trace
            target_file: Optional file where error occurred
            max_commits: Number of recent commits to analyze

        Returns:
            Dict with suspects and recommendation
        """
        suspects = []
        recommendation = None

        try:
            import subprocess

            # Get recent commits
            cmd = ["git", "log", f"-{max_commits}", "--pretty=format:%H|%s|%an", "--"]
            if target_file:
                cmd.append(target_file)

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.project_root))

            if result.returncode != 0:
                return {"suspects": [], "recommendation": "Failed to read git log"}

            # Parse commits
            commits = []
            for line in result.stdout.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|", 2)
                    if len(parts) >= 2:
                        commits.append(
                            {
                                "sha": parts[0],
                                "message": parts[1],
                                "author": parts[2] if len(parts) > 2 else "Unknown",
                            }
                        )

            # Score each commit based on error relevance
            error_keywords = set(re.findall(r"\w+", error_message.lower()))

            for commit in commits:
                msg_words = set(re.findall(r"\w+", commit["message"].lower()))
                overlap = len(error_keywords & msg_words)
                # Higher score for more keyword overlap
                score = min(1.0, overlap / max(len(error_keywords), 1) + 0.1)

                # Boost score for recent commits
                idx = commits.index(commit)
                recency_boost = 0.3 * (1 - idx / len(commits))
                score = min(1.0, score + recency_boost)

                suspects.append(
                    {
                        "sha": commit["sha"],
                        "message": commit["message"],
                        "score": round(score, 2),
                    }
                )

            # Sort by score
            suspects.sort(key=lambda x: x["score"], reverse=True)

            if suspects:
                top = suspects[0]
                recommendation = (
                    f"Start investigation at commit {top['sha'][:7]}: {top['message'][:50]}"
                )

        except Exception as e:
            recommendation = f"Analysis failed: {e}"

        return {"suspects": suspects, "recommendation": recommendation}

    def deep_diagnostic(self, since_commit: str = "HEAD~10") -> dict:
        """
        Deep diagnostic: Comprehensive project health analysis.

        Args:
            since_commit: Reference commit for comparison

        Returns:
            Dict with risk_score, issues, and patterns
        """
        issues = []
        patterns = []
        risk_score = 0

        try:
            import subprocess

            # Get changed files since commit
            result = subprocess.run(
                ["git", "diff", "--name-only", since_commit],
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
            )

            changed_files = [
                self.project_root / f.strip()
                for f in result.stdout.strip().split("\n")
                if f.strip()
            ]

            # Analyze each changed file
            for file_path in changed_files:
                if file_path.suffix in {".py", ".js", ".ts"}:
                    file_issues = self.analyze_file(file_path)
                    for issue in file_issues:
                        issues.append(
                            f"{issue.severity.upper()}: {issue.message} ({file_path.name}:{issue.line_number})"
                        )

            # Calculate risk score
            critical_count = sum(1 for i in issues if "CRITICAL" in i)
            warning_count = sum(1 for i in issues if "WARNING" in i)
            risk_score = min(100, critical_count * 30 + warning_count * 10 + len(changed_files) * 2)

            # Check Brain for related patterns
            brain = self._get_brain()
            if brain:
                try:
                    related = brain.get_relevant_patterns("common errors issues bugs", limit=3)
                    patterns = [p.get("description", "Pattern")[:60] for p in related]
                except Exception:
                    pass

        except Exception as e:
            issues.append(f"Diagnostic error: {e}")
            risk_score = 50

        return {
            "risk_score": risk_score,
            "issues": issues,
            "patterns": patterns,
        }


def predict_issues(project_root: Path, file_paths: list[Path]) -> PredictionReport:
    """
    Convenience function for predictive error detection.

    Args:
        project_root: Project root directory
        file_paths: Files to analyze

    Returns:
        PredictionReport with findings
    """
    predictor = Predictor(project_root)
    return predictor.generate_report(file_paths)
