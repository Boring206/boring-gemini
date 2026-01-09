# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Bias Monitor Module - Advanced Evaluation V10.25

Monitors and detects systematic biases in LLM-as-a-Judge evaluation systems.
Based on the Advanced Evaluation skill framework.

Features:
1. Position bias detection (first-position preference)
2. Length bias detection (longer = higher scores)
3. Aggregate bias reporting over time
4. Bias mitigation recommendations
"""

import json
import logging
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .metrics import spearmans_rho

logger = logging.getLogger(__name__)

# Thread-local connection
_local = threading.local()


@dataclass
class PositionBiasResult:
    """Result of position bias analysis."""

    bias_detected: bool
    first_position_win_rate: float
    z_score: float
    sample_size: int
    interpretation: str = ""


@dataclass
class LengthBiasResult:
    """Result of length bias analysis."""

    bias_detected: bool
    correlation: float
    p_value: float
    sample_size: int
    interpretation: str = ""


@dataclass
class BiasReport:
    """Comprehensive bias report."""

    position_bias: Optional[PositionBiasResult] = None
    length_bias: Optional[LengthBiasResult] = None
    total_evaluations: int = 0
    evaluation_period_days: int = 30
    warnings: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    generated_at: str = ""


class BiasMonitor:
    """
    Monitors systematic biases in LLM evaluation over time.

    Features:
    - Track pairwise comparison outcomes
    - Detect position bias (first-position preference)
    - Detect length bias (longer responses get higher scores)
    - Generate bias reports with recommendations
    """

    def __init__(self, project_root: Path):
        """
        Initialize bias monitor.

        Args:
            project_root: Project root for database storage
        """
        self.project_root = Path(project_root)
        self.db_path = self.project_root / ".boring_memory" / "bias_monitor.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(_local, "bias_conn"):
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            _local.bias_conn = conn
        return _local.bias_conn

    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_connection()
        conn.executescript("""
            -- Pairwise comparison tracking
            CREATE TABLE IF NOT EXISTS pairwise_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evaluation_id TEXT UNIQUE,
                winner TEXT NOT NULL,  -- 'A', 'B', 'TIE'
                first_position TEXT NOT NULL,  -- Which was in first position
                first_position_won INTEGER,  -- 1 if first position won
                position_consistent INTEGER,  -- 1 if both passes agreed
                confidence REAL,
                response_a_length INTEGER,
                response_b_length INTEGER,
                created_at TEXT NOT NULL
            );

            -- Direct scoring tracking
            CREATE TABLE IF NOT EXISTS direct_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evaluation_id TEXT UNIQUE,
                score REAL NOT NULL,
                response_length INTEGER,
                dimension_scores TEXT,  -- JSON
                created_at TEXT NOT NULL
            );

            -- Indices
            CREATE INDEX IF NOT EXISTS idx_pairwise_created ON pairwise_evaluations(created_at);
            CREATE INDEX IF NOT EXISTS idx_direct_created ON direct_evaluations(created_at);
        """)
        conn.commit()

    def record_pairwise_evaluation(
        self,
        evaluation_id: str,
        winner: str,
        first_position: str,
        position_consistent: bool,
        confidence: float = 0.0,
        response_a_length: int = 0,
        response_b_length: int = 0,
    ):
        """
        Record a pairwise comparison result.

        Args:
            evaluation_id: Unique identifier for this evaluation
            winner: Winner of comparison ('A', 'B', 'TIE')
            first_position: Which response was in first position ('A' or 'B')
            position_consistent: Whether both position passes agreed
            confidence: Confidence score of the decision
            response_a_length: Length of response A
            response_b_length: Length of response B
        """
        winner = winner.upper()
        first_position = first_position.upper()

        # Determine if first position won
        first_position_won = 1 if winner == first_position and winner != "TIE" else 0

        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO pairwise_evaluations
                (evaluation_id, winner, first_position, first_position_won,
                 position_consistent, confidence, response_a_length,
                 response_b_length, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    evaluation_id,
                    winner,
                    first_position,
                    first_position_won,
                    1 if position_consistent else 0,
                    confidence,
                    response_a_length,
                    response_b_length,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            logger.debug(f"Recorded pairwise evaluation: {evaluation_id}")
        except Exception as e:
            logger.error(f"Failed to record pairwise evaluation: {e}")

    def record_direct_evaluation(
        self,
        evaluation_id: str,
        score: float,
        response_length: int,
        dimension_scores: Optional[dict] = None,
    ):
        """
        Record a direct scoring evaluation.

        Args:
            evaluation_id: Unique identifier for this evaluation
            score: Overall score
            response_length: Length of the response (characters or tokens)
            dimension_scores: Optional per-dimension scores
        """
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO direct_evaluations
                (evaluation_id, score, response_length, dimension_scores, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    evaluation_id,
                    score,
                    response_length,
                    json.dumps(dimension_scores or {}),
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            logger.debug(f"Recorded direct evaluation: {evaluation_id}")
        except Exception as e:
            logger.error(f"Failed to record direct evaluation: {e}")

    def detect_position_bias(self, days: int = 30) -> PositionBiasResult:
        """
        Detect position bias in pairwise comparisons.

        Checks if first-position responses win more often than expected (50%).

        Args:
            days: Number of days to analyze

        Returns:
            PositionBiasResult with bias analysis
        """
        conn = self._get_connection()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        # Get evaluations excluding ties
        rows = conn.execute(
            """
            SELECT first_position_won
            FROM pairwise_evaluations
            WHERE created_at >= ? AND winner != 'TIE'
        """,
            (cutoff,),
        ).fetchall()

        n = len(rows)
        if n < 10:
            return PositionBiasResult(
                bias_detected=False,
                first_position_win_rate=0.0,
                z_score=0.0,
                sample_size=n,
                interpretation="Insufficient data (need at least 10 non-tie comparisons)",
            )

        first_wins = sum(r["first_position_won"] for r in rows)
        expected = n * 0.5
        std_dev = (n * 0.5 * 0.5) ** 0.5

        win_rate = first_wins / n
        z_score = (first_wins - expected) / std_dev if std_dev > 0 else 0

        # Bias detected if z-score > 2 (95% confidence)
        bias_detected = abs(z_score) > 2

        if bias_detected:
            if z_score > 0:
                interpretation = (
                    f"First-position bias detected: {win_rate:.1%} win rate (expected 50%)"
                )
            else:
                interpretation = f"Second-position bias detected: {1 - win_rate:.1%} win rate for second position"
        else:
            interpretation = f"No significant position bias: {win_rate:.1%} first-position win rate"

        return PositionBiasResult(
            bias_detected=bias_detected,
            first_position_win_rate=win_rate,
            z_score=z_score,
            sample_size=n,
            interpretation=interpretation,
        )

    def detect_length_bias(self, days: int = 30) -> LengthBiasResult:
        """
        Detect length bias in direct evaluations.

        Checks if longer responses receive higher scores.

        Args:
            days: Number of days to analyze

        Returns:
            LengthBiasResult with bias analysis
        """
        conn = self._get_connection()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        rows = conn.execute(
            """
            SELECT score, response_length
            FROM direct_evaluations
            WHERE created_at >= ? AND response_length > 0
        """,
            (cutoff,),
        ).fetchall()

        n = len(rows)
        if n < 10:
            return LengthBiasResult(
                bias_detected=False,
                correlation=0.0,
                p_value=1.0,
                sample_size=n,
                interpretation="Insufficient data (need at least 10 evaluations)",
            )

        scores = [r["score"] for r in rows]
        lengths = [r["response_length"] for r in rows]

        # Calculate Spearman correlation between length and score
        rho, p_value = spearmans_rho(lengths, scores)

        # Bias detected if correlation > 0.3 and p < 0.05
        bias_detected = rho > 0.3 and p_value < 0.05

        if bias_detected:
            interpretation = f"Length bias detected: correlation = {rho:.2f} (p = {p_value:.3f})"
        elif rho > 0.2:
            interpretation = f"Weak length bias possible: correlation = {rho:.2f}"
        else:
            interpretation = f"No significant length bias: correlation = {rho:.2f}"

        return LengthBiasResult(
            bias_detected=bias_detected,
            correlation=rho,
            p_value=p_value,
            sample_size=n,
            interpretation=interpretation,
        )

    def get_bias_report(self, days: int = 30) -> BiasReport:
        """
        Generate comprehensive bias report.

        Args:
            days: Number of days to analyze

        Returns:
            BiasReport with all bias analyses and recommendations
        """
        position_bias = self.detect_position_bias(days)
        length_bias = self.detect_length_bias(days)

        conn = self._get_connection()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        # Get total evaluations
        pairwise_count = conn.execute(
            "SELECT COUNT(*) FROM pairwise_evaluations WHERE created_at >= ?", (cutoff,)
        ).fetchone()[0]
        direct_count = conn.execute(
            "SELECT COUNT(*) FROM direct_evaluations WHERE created_at >= ?", (cutoff,)
        ).fetchone()[0]

        total = pairwise_count + direct_count
        warnings = []
        recommendations = []

        # Analyze position bias
        if position_bias.bias_detected:
            warnings.append(f"⚠️ Position Bias: {position_bias.interpretation}")
            recommendations.append("Increase position swap passes or use multi-shuffle comparison")

        # Analyze length bias
        if length_bias.bias_detected:
            warnings.append(f"⚠️ Length Bias: {length_bias.interpretation}")
            recommendations.append("Add explicit length normalization or penalize verbosity")
            recommendations.append("Include 'conciseness' as a separate evaluation criterion")

        # Sample size warnings
        if total < 50:
            warnings.append(f"📊 Small sample size ({total}): metrics may be unreliable")
            recommendations.append("Collect more evaluation data for reliable bias detection")

        # Position consistency check
        consistency = conn.execute(
            """
            SELECT AVG(position_consistent) as avg_consistency
            FROM pairwise_evaluations
            WHERE created_at >= ?
        """,
            (cutoff,),
        ).fetchone()

        if consistency and consistency["avg_consistency"] is not None:
            avg_cons = consistency["avg_consistency"]
            if avg_cons < 0.8:
                warnings.append(f"⚠️ Low position consistency: {avg_cons:.1%}")
                recommendations.append("Review evaluation criteria for ambiguity")

        if not warnings:
            recommendations.append("✅ No significant biases detected!")

        return BiasReport(
            position_bias=position_bias,
            length_bias=length_bias,
            total_evaluations=total,
            evaluation_period_days=days,
            warnings=warnings,
            recommendations=recommendations,
            generated_at=datetime.now().isoformat(),
        )

    def clear_old_data(self, days: int = 90):
        """
        Clear evaluation data older than specified days.

        Args:
            days: Keep data from the last N days
        """
        conn = self._get_connection()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        conn.execute("DELETE FROM pairwise_evaluations WHERE created_at < ?", (cutoff,))
        conn.execute("DELETE FROM direct_evaluations WHERE created_at < ?", (cutoff,))
        conn.commit()
        logger.info(f"Cleared bias monitor data older than {days} days")


def format_bias_report(report: BiasReport) -> str:
    """Format bias report as markdown."""
    lines = ["# 🔍 Bias Monitoring Report", ""]

    lines.append(f"**Period**: Last {report.evaluation_period_days} days")
    lines.append(f"**Total Evaluations**: {report.total_evaluations}")
    lines.append(f"**Generated**: {report.generated_at[:19]}")
    lines.append("")

    # Position Bias
    if report.position_bias:
        pb = report.position_bias
        emoji = "🔴" if pb.bias_detected else "🟢"
        lines.append(f"## {emoji} Position Bias")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| First Position Win Rate | {pb.first_position_win_rate:.1%} |")
        lines.append(f"| Z-Score | {pb.z_score:.2f} |")
        lines.append(f"| Sample Size | {pb.sample_size} |")
        lines.append("")
        lines.append(f"**Analysis**: {pb.interpretation}")
        lines.append("")

    # Length Bias
    if report.length_bias:
        lb = report.length_bias
        emoji = "🔴" if lb.bias_detected else "🟢"
        lines.append(f"## {emoji} Length Bias")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Length-Score Correlation | {lb.correlation:.3f} |")
        lines.append(f"| P-Value | {lb.p_value:.4f} |")
        lines.append(f"| Sample Size | {lb.sample_size} |")
        lines.append("")
        lines.append(f"**Analysis**: {lb.interpretation}")
        lines.append("")

    # Warnings
    if report.warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in report.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    # Recommendations
    if report.recommendations:
        lines.append("## Recommendations")
        lines.append("")
        for rec in report.recommendations:
            lines.append(f"- {rec}")
        lines.append("")

    return "\n".join(lines)


# Singleton instance
_bias_monitor: Optional[BiasMonitor] = None


def get_bias_monitor(project_root: Path) -> BiasMonitor:
    """Get or create bias monitor singleton."""
    global _bias_monitor
    if _bias_monitor is None:
        _bias_monitor = BiasMonitor(project_root)
    return _bias_monitor
