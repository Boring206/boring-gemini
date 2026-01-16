"""
AI Git Bisect for Boring V14.0

Uses AI-powered pattern matching to intelligently identify which commit
introduced a bug, leveraging the Brain's learned patterns.

Features:
- Semantic commit analysis
- Pattern-based suspicion scoring
- Interactive bisect guidance
- Integration with Brain Manager for historical learning
"""

import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CommitInfo:
    """Information about a Git commit."""

    hash: str
    short_hash: str
    author: str
    date: datetime
    message: str
    files_changed: list[str]
    insertions: int
    deletions: int
    suspicion_score: float = 0.0
    suspicion_reasons: list[str] = None

    def __post_init__(self):
        if self.suspicion_reasons is None:
            self.suspicion_reasons = []


@dataclass
class BisectResult:
    """Result of AI-assisted git bisect."""

    suspect_commits: list[CommitInfo]
    analysis: str
    confidence: float
    recommended_action: str


class AIGitBisect:
    """
    AI-powered git bisect assistant.

    Uses semantic analysis and Brain patterns to identify likely
    bug-introducing commits without running tests.
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.brain: Any | None = None

    def _get_brain(self) -> Any | None:
        """Lazy-load Brain Manager."""
        if self.brain is None:
            try:
                from ..intelligence import BrainManager

                self.brain = BrainManager(self.project_root)
            except ImportError:
                pass
        return self.brain

    def get_recent_commits(self, count: int = 20) -> list[CommitInfo]:
        """Get recent commits with metadata."""
        try:
            # Get commit hashes and messages
            result = subprocess.run(
                ["git", "log", f"-{count}", "--format=%H|%h|%an|%aI|%s"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            commits = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|", 4)
                if len(parts) < 5:
                    continue

                hash_, short, author, date_str, message = parts

                # Get file stats for this commit
                stats = self._get_commit_stats(hash_)

                commits.append(
                    CommitInfo(
                        hash=hash_,
                        short_hash=short,
                        author=author,
                        date=datetime.fromisoformat(date_str),
                        message=message,
                        files_changed=stats.get("files", []),
                        insertions=stats.get("insertions", 0),
                        deletions=stats.get("deletions", 0),
                    )
                )

            return commits
        except subprocess.CalledProcessError as e:
            logger.error(f"Git log failed: {e}")
            return []

    def _get_commit_stats(self, commit_hash: str) -> dict:
        """Get statistics for a specific commit."""
        try:
            # Get changed files
            files_result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            files = [f for f in files_result.stdout.strip().split("\n") if f]

            # Get insertions/deletions
            stat_result = subprocess.run(
                ["git", "show", "--stat", "--format=", commit_hash],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            insertions = 0
            deletions = 0
            for line in stat_result.stdout.split("\n"):
                if "insertion" in line or "deletion" in line:
                    parts = line.split(",")
                    for part in parts:
                        if "insertion" in part:
                            try:
                                insertions = int(part.strip().split()[0])
                            except (ValueError, IndexError):
                                pass
                        if "deletion" in part:
                            try:
                                deletions = int(part.strip().split()[0])
                            except (ValueError, IndexError):
                                pass

            return {"files": files, "insertions": insertions, "deletions": deletions}
        except subprocess.CalledProcessError:
            return {"files": [], "insertions": 0, "deletions": 0}

    def analyze_for_error(
        self, error_message: str, error_file: str | None = None, lookback_commits: int = 20
    ) -> BisectResult:
        """
        Analyze recent commits to find likely bug introducers.

        Args:
            error_message: The error message to analyze
            error_file: Optional file where error occurred
            lookback_commits: Number of commits to analyze

        Returns:
            BisectResult with ranked suspect commits
        """
        commits = self.get_recent_commits(lookback_commits)
        if not commits:
            return BisectResult(
                suspect_commits=[],
                analysis="No commits found to analyze",
                confidence=0.0,
                recommended_action="Check if this is a git repository",
            )

        # Score each commit
        for commit in commits:
            self._score_commit(commit, error_message, error_file)

        # Sort by suspicion score
        commits.sort(key=lambda c: c.suspicion_score, reverse=True)

        # Get top suspects
        suspects = [c for c in commits if c.suspicion_score > 0.3][:5]

        # Generate analysis
        brain = self._get_brain()
        analysis = self._generate_analysis(suspects, error_message, brain)

        # Calculate overall confidence
        confidence = min(0.9, max(s.suspicion_score for s in suspects) if suspects else 0.1)

        # Recommend action
        if suspects and suspects[0].suspicion_score > 0.7:
            action = f"Highly likely: {suspects[0].short_hash} - {suspects[0].message[:50]}"
        elif suspects:
            action = f"Investigate commits: {', '.join(s.short_hash for s in suspects[:3])}"
        else:
            action = "No clear suspects. Consider manual git bisect or expanding search range."

        return BisectResult(
            suspect_commits=suspects,
            analysis=analysis,
            confidence=confidence,
            recommended_action=action,
        )

    def _score_commit(self, commit: CommitInfo, error_message: str, error_file: str | None) -> None:
        """Score a commit based on likelihood of introducing the bug."""
        score = 0.0
        reasons = []

        # 1. File match (highest weight)
        if error_file:
            error_file_name = Path(error_file).name
            for changed_file in commit.files_changed:
                if error_file_name in changed_file or changed_file in error_file:
                    score += 0.4
                    reasons.append(f"Modified related file: {changed_file}")
                    break

        # 2. Error keywords in commit message
        error_keywords = self._extract_keywords(error_message)
        message_lower = commit.message.lower()
        for keyword in error_keywords:
            if keyword in message_lower:
                score += 0.15
                reasons.append(f"Commit mentions: '{keyword}'")

        # 3. Risk indicators in commit message
        risk_words = ["fix", "bug", "hack", "workaround", "temporary", "quick", "hotfix"]
        for word in risk_words:
            if word in message_lower:
                score += 0.1
                reasons.append(f"Risk indicator: '{word}'")
                break

        # 4. Large changes are riskier
        total_changes = commit.insertions + commit.deletions
        if total_changes > 500:
            score += 0.15
            reasons.append(f"Large change: {total_changes} lines")
        elif total_changes > 200:
            score += 0.1
            reasons.append(f"Medium change: {total_changes} lines")

        # 5. Recent commits are more likely
        days_ago = (datetime.now(commit.date.tzinfo) - commit.date).days
        if days_ago < 1:
            score += 0.1
            reasons.append("Very recent (< 1 day)")
        elif days_ago < 3:
            score += 0.05
            reasons.append("Recent (< 3 days)")

        # 6. Brain patterns (if available)
        brain = self._get_brain()
        if brain:
            try:
                patterns = brain.get_relevant_patterns(
                    f"{commit.message} {' '.join(commit.files_changed)}", limit=3
                )
                for pattern in patterns:
                    if "error" in pattern.get("pattern_type", "").lower():
                        score += 0.2
                        reasons.append(
                            f"Brain pattern match: {pattern.get('description', '')[:30]}"
                        )
                        break
            except Exception:
                pass

        commit.suspicion_score = min(1.0, score)
        commit.suspicion_reasons = reasons

    def _extract_keywords(self, error_message: str) -> list[str]:
        """Extract meaningful keywords from error message."""
        # Common words to ignore
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for"}

        words = error_message.lower().split()
        keywords = []
        for word in words:
            # Clean word
            clean = "".join(c for c in word if c.isalnum())
            if len(clean) > 3 and clean not in stopwords:
                keywords.append(clean)

        return keywords[:10]  # Limit to top 10

    def _generate_analysis(
        self, suspects: list[CommitInfo], error_message: str, brain: Any | None
    ) -> str:
        """Generate human-readable analysis."""
        if not suspects:
            return "No suspicious commits found based on error pattern analysis."

        lines = ["## AI Git Bisect Analysis\n"]
        lines.append(f"**Error:** {error_message[:100]}...\n")
        lines.append(f"**Top Suspects:** ({len(suspects)} found)\n")

        for i, commit in enumerate(suspects, 1):
            lines.append(f"\n### {i}. `{commit.short_hash}` - Score: {commit.suspicion_score:.2f}")
            lines.append(f"- **Message:** {commit.message}")
            lines.append(f"- **Author:** {commit.author}")
            lines.append(f"- **Files:** {len(commit.files_changed)} changed")
            if commit.suspicion_reasons:
                lines.append("- **Reasons:**")
                for reason in commit.suspicion_reasons:
                    lines.append(f"  - {reason}")

        return "\n".join(lines)


def ai_bisect(
    project_root: Path, error_message: str, error_file: str | None = None, lookback: int = 20
) -> BisectResult:
    """
    Convenience function for AI git bisect.

    Args:
        project_root: Project root directory
        error_message: The error to analyze
        error_file: Optional file where error occurred
        lookback: Number of commits to analyze

    Returns:
        BisectResult with analysis
    """
    bisect = AIGitBisect(project_root)
    return bisect.analyze_for_error(error_message, error_file, lookback)
