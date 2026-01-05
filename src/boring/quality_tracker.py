"""
Quality Trend Tracker
Tracks code quality metrics over time to visualize improvements or regressions.
"""

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .config import settings
from .logger import get_logger

logger = get_logger("quality_tracker")


@dataclass
class QualityEntry:
    timestamp: float
    date: str
    score: float
    issues_count: int
    commit_hash: Optional[str] = None
    context: str = ""  # e.g., "manual_verify", "ci", "judge"


class QualityTracker:
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self.brain_dir = self.project_root / settings.BRAIN_DIR
        self.history_file = self.brain_dir / "quality_history.json"
        self._ensure_dir()

    def _ensure_dir(self):
        self.brain_dir.mkdir(parents=True, exist_ok=True)

    def record(self, score: float, issues_count: int, context: str = "manual"):
        """Record a new quality snapshot."""
        entry = QualityEntry(
            timestamp=time.time(),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            score=round(score, 2),
            issues_count=issues_count,
            context=context,
        )

        history = self._load_history()
        history.append(asdict(entry))

        # Limit history size (keep last 100 entries)
        if len(history) > 100:
            history = history[-100:]

        self._save_history(history)
        logger.info(f"Recorded quality score: {score} (Issues: {issues_count})")

    def get_trend(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent quality history."""
        history = self._load_history()
        return history[-limit:]

    def render_ascii_chart(self, width: int = 60, height: int = 10) -> str:
        """Generate a simple ASCII chart of the quality score trend."""
        history = self.get_trend(width)
        if not history:
            return "No quality history available."

        scores = [entry["score"] for entry in history]

        # Normalize to chart height
        chart = []
        chart.append(f"Quality Trend (Last {len(scores)} checks)")
        chart.append(f"Score: {scores[-1]} | Issues: {history[-1]['issues_count']}")
        chart.append("-" * width)

        # Simple Sparkline-like representation
        canvas = [[" " for _ in range(width)] for _ in range(height)]

        for x, score in enumerate(scores):
            # Scale score 0-5 to 0-(height-1)
            if x >= width:
                break

            y = int((score / 5.0) * (height - 1))
            canvas[height - 1 - y][x] = "*"

        for row in canvas:
            chart.append("".join(row))

        chart.append("-" * width)
        chart.append(f"0.0 {' ' * (width - 8)} 5.0")

        return "\n".join(chart)

    def _load_history(self) -> list[dict[str, Any]]:
        if not self.history_file.exists():
            return []
        try:
            return json.loads(self.history_file.read_text(encoding="utf-8"))
        except:
            return []

    def _save_history(self, history: list[dict[str, Any]]):
        self.history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")
