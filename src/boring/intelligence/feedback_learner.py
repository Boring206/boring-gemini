"""
Feedback Learning Module (V10.15)

Records review outcomes to improve future suggestions.
Learns patterns from successful and failed reviews.
"""

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..config import settings
from ..logger import get_logger

logger = get_logger("feedback_learner")


@dataclass
class FeedbackEntry:
    """A single feedback record."""

    timestamp: float
    date: str
    review_id: str
    verdict: str  # PASS, NEEDS_WORK, REJECT
    issues: list[str]
    fix_applied: bool
    fix_successful: bool
    code_hash: str
    pattern_type: str  # security, performance, correctness, etc.
    context: str = ""


class FeedbackLearner:
    """
    V10.15: Records and learns from review feedback.

    Features:
    - Records review outcomes (verdict, issues, fixes)
    - Tracks fix success rates
    - Identifies recurring patterns
    - Provides suggestions based on history

    Usage:
        learner = FeedbackLearner(project_root)
        learner.record_review("review_123", "NEEDS_WORK", ["null check missing"])
        learner.record_fix("review_123", success=True)
        suggestions = learner.get_suggestions("auth.py")
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self.brain_dir = self.project_root / settings.BRAIN_DIR
        self.feedback_file = self.brain_dir / "review_feedback.json"
        self._ensure_dir()

    def _ensure_dir(self):
        self.brain_dir.mkdir(parents=True, exist_ok=True)

    def record_review(
        self,
        review_id: str,
        verdict: str,
        issues: list[str],
        code_hash: str = "",
        pattern_type: str = "general",
        context: str = "",
    ) -> None:
        """Record a review outcome."""
        entry = FeedbackEntry(
            timestamp=time.time(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            review_id=review_id,
            verdict=verdict,
            issues=issues,
            fix_applied=False,
            fix_successful=False,
            code_hash=code_hash,
            pattern_type=pattern_type,
            context=context,
        )

        history = self._load_history()
        history.append(asdict(entry))
        self._save_history(history)
        logger.info(f"Recorded review {review_id}: {verdict}")

    def record_fix(self, review_id: str, success: bool) -> None:
        """Record whether a fix was applied and successful."""
        history = self._load_history()

        for entry in reversed(history):
            if entry.get("review_id") == review_id:
                entry["fix_applied"] = True
                entry["fix_successful"] = success
                break

        self._save_history(history)
        logger.info(f"Recorded fix for {review_id}: {'success' if success else 'failed'}")

    def get_suggestions(self, filename: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Get suggestions based on historical patterns.

        Returns issues that frequently occurred in similar files.
        """
        history = self._load_history()

        # Count issue frequency by pattern type
        issue_counts: dict[str, int] = {}
        for entry in history:
            if entry.get("verdict") != "PASS":
                for issue in entry.get("issues", []):
                    issue_key = issue[:100]  # Truncate for matching
                    issue_counts[issue_key] = issue_counts.get(issue_key, 0) + 1

        # Sort by frequency
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)

        return [{"issue": issue, "frequency": count} for issue, count in sorted_issues[:limit]]

    def get_fix_success_rate(self, pattern_type: str = None) -> dict[str, float]:
        """Get fix success rate by pattern type."""
        history = self._load_history()

        stats: dict[str, dict[str, int]] = {}

        for entry in history:
            if entry.get("fix_applied"):
                ptype = entry.get("pattern_type", "general")
                if pattern_type and ptype != pattern_type:
                    continue

                if ptype not in stats:
                    stats[ptype] = {"total": 0, "success": 0}

                stats[ptype]["total"] += 1
                if entry.get("fix_successful"):
                    stats[ptype]["success"] += 1

        return {
            ptype: data["success"] / data["total"] if data["total"] > 0 else 0.0
            for ptype, data in stats.items()
        }

    def get_recurring_issues(self, min_occurrences: int = 3) -> list[dict[str, Any]]:
        """Find issues that recur frequently."""
        history = self._load_history()

        issue_details: dict[str, dict] = {}

        for entry in history:
            for issue in entry.get("issues", []):
                key = issue[:100]
                if key not in issue_details:
                    issue_details[key] = {
                        "issue": issue,
                        "count": 0,
                        "pattern_types": set(),
                        "last_seen": entry.get("date", ""),
                    }
                issue_details[key]["count"] += 1
                issue_details[key]["pattern_types"].add(entry.get("pattern_type", "general"))
                issue_details[key]["last_seen"] = entry.get("date", "")

        recurring = [
            {
                "issue": d["issue"],
                "count": d["count"],
                "pattern_types": list(d["pattern_types"]),
                "last_seen": d["last_seen"],
            }
            for d in issue_details.values()
            if d["count"] >= min_occurrences
        ]

        return sorted(recurring, key=lambda x: x["count"], reverse=True)

    def _load_history(self) -> list[dict]:
        if not self.feedback_file.exists():
            return []
        try:
            with open(self.feedback_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_history(self, history: list[dict]) -> None:
        with open(self.feedback_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, default=str)
