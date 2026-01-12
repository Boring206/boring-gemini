# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Prediction Accuracy Tracker - V10.24

Tracks and evaluates prediction accuracy for continuous improvement.
Enables data-driven optimization of prediction algorithms.

Features:
1. Prediction vs Actual outcome tracking
2. Accuracy metrics computation
3. Confidence calibration analysis
4. A/B testing framework for strategies
"""

import json
import logging
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Thread-local connection
_local = threading.local()


@dataclass
class PredictionRecord:
    """A recorded prediction with outcome."""

    prediction_id: str
    prediction_type: str  # "error", "impact", "risk"
    predicted_value: str
    confidence: float
    actual_outcome: Optional[str] = None
    was_correct: Optional[bool] = None
    created_at: str = ""
    resolved_at: Optional[str] = None
    context: dict = field(default_factory=dict)


@dataclass
class AccuracyMetrics:
    """Accuracy metrics for predictions."""

    total_predictions: int
    resolved_predictions: int
    correct_predictions: int
    accuracy_rate: float
    avg_confidence: float
    calibration_error: float  # ECE (Expected Calibration Error)
    by_type: dict = field(default_factory=dict)
    by_confidence_bucket: dict = field(default_factory=dict)


@dataclass
class ABTestResult:
    """Result from A/B test comparison."""

    test_name: str
    variant_a: str
    variant_b: str
    samples_a: int
    samples_b: int
    accuracy_a: float
    accuracy_b: float
    winner: str
    confidence_interval: float
    p_value: float


class PredictionTracker:
    """
    Tracks prediction accuracy and enables continuous improvement.

    Use cases:
    1. Track error predictions vs actual errors
    2. Measure impact prediction accuracy
    3. Calibrate confidence scores
    4. Compare prediction strategies via A/B testing
    """

    def __init__(self, project_root: Path):
        """
        Initialize prediction tracker.

        Args:
            project_root: Project root for database storage
        """
        self.project_root = Path(project_root)
        self.db_path = self.project_root / ".boring_memory" / "prediction_tracking.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(_local, "prediction_conn"):
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            _local.prediction_conn = conn
        return _local.prediction_conn

    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS predictions (
                prediction_id TEXT PRIMARY KEY,
                prediction_type TEXT NOT NULL,
                predicted_value TEXT NOT NULL,
                confidence REAL NOT NULL,
                actual_outcome TEXT,
                was_correct INTEGER,
                strategy TEXT DEFAULT 'default',
                context_json TEXT,
                created_at TEXT NOT NULL,
                resolved_at TEXT
            );

            CREATE TABLE IF NOT EXISTS ab_tests (
                test_id TEXT PRIMARY KEY,
                test_name TEXT NOT NULL,
                variant_a TEXT NOT NULL,
                variant_b TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                winner TEXT,
                status TEXT DEFAULT 'running'
            );

            CREATE TABLE IF NOT EXISTS calibration_data (
                bucket REAL,
                prediction_type TEXT,
                total_count INTEGER,
                correct_count INTEGER,
                avg_confidence REAL,
                last_updated TEXT,
                PRIMARY KEY (bucket, prediction_type)
            );

            CREATE INDEX IF NOT EXISTS idx_pred_type ON predictions(prediction_type);
            CREATE INDEX IF NOT EXISTS idx_pred_resolved ON predictions(was_correct);
            CREATE INDEX IF NOT EXISTS idx_pred_strategy ON predictions(strategy);
        """)
        conn.commit()

    def record_prediction(
        self,
        prediction_id: str,
        prediction_type: str,
        predicted_value: str,
        confidence: float,
        strategy: str = "default",
        context: Optional[dict] = None,
    ):
        """
        Record a new prediction.

        Args:
            prediction_id: Unique identifier for this prediction
            prediction_type: Type of prediction (error, impact, risk)
            predicted_value: The predicted outcome
            confidence: Confidence score (0-1)
            strategy: Strategy/variant used for A/B testing
            context: Additional context (file, query, etc.)
        """
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO predictions
            (prediction_id, prediction_type, predicted_value, confidence,
             strategy, context_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                prediction_id,
                prediction_type,
                predicted_value,
                confidence,
                strategy,
                json.dumps(context or {}),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        logger.debug(f"Recorded prediction: {prediction_id} ({prediction_type})")

    def resolve_prediction(self, prediction_id: str, actual_outcome: str, was_correct: bool):
        """
        Resolve a prediction with actual outcome.

        Args:
            prediction_id: ID of the prediction to resolve
            actual_outcome: What actually happened
            was_correct: Whether the prediction was correct
        """
        conn = self._get_connection()
        conn.execute(
            """
            UPDATE predictions
            SET actual_outcome = ?, was_correct = ?, resolved_at = ?
            WHERE prediction_id = ?
        """,
            (actual_outcome, 1 if was_correct else 0, datetime.now().isoformat(), prediction_id),
        )
        conn.commit()

        # Update calibration data
        row = conn.execute(
            "SELECT confidence, prediction_type FROM predictions WHERE prediction_id = ?",
            (prediction_id,),
        ).fetchone()

        if row:
            self._update_calibration(row["prediction_type"], row["confidence"], was_correct)

        logger.debug(f"Resolved prediction: {prediction_id} = {was_correct}")

    def _update_calibration(self, prediction_type: str, confidence: float, was_correct: bool):
        """Update calibration buckets."""
        # Round confidence to nearest 0.1 for bucketing
        bucket = round(confidence, 1)

        conn = self._get_connection()

        # Get current bucket data
        row = conn.execute(
            """
            SELECT total_count, correct_count, avg_confidence
            FROM calibration_data
            WHERE bucket = ? AND prediction_type = ?
        """,
            (bucket, prediction_type),
        ).fetchone()

        if row:
            total = row["total_count"] + 1
            correct = row["correct_count"] + (1 if was_correct else 0)
            avg_conf = (row["avg_confidence"] * row["total_count"] + confidence) / total
        else:
            total = 1
            correct = 1 if was_correct else 0
            avg_conf = confidence

        conn.execute(
            """
            INSERT OR REPLACE INTO calibration_data
            (bucket, prediction_type, total_count, correct_count, avg_confidence, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (bucket, prediction_type, total, correct, avg_conf, datetime.now().isoformat()),
        )
        conn.commit()

    def get_accuracy_metrics(
        self, prediction_type: Optional[str] = None, days: int = 30
    ) -> AccuracyMetrics:
        """
        Compute accuracy metrics.

        Args:
            prediction_type: Filter by type (None for all)
            days: Number of days to include

        Returns:
            AccuracyMetrics with detailed breakdown
        """
        conn = self._get_connection()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        # Build query
        where_clause = "created_at >= ?"
        params = [cutoff]
        if prediction_type:
            where_clause += " AND prediction_type = ?"
            params.append(prediction_type)

        # Get totals
        query_total = (
            "SELECT COUNT(*) as total, SUM(CASE WHEN was_correct IS NOT NULL THEN 1 ELSE 0 END) as resolved, "
            f"SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct, AVG(confidence) as avg_conf FROM predictions WHERE {where_clause}"  # nosec B608
        )
        row = conn.execute(query_total, params).fetchone()

        total = row["total"] or 0
        resolved = row["resolved"] or 0
        correct = row["correct"] or 0
        avg_conf = row["avg_conf"] or 0

        accuracy = correct / resolved if resolved > 0 else 0

        # Get by type
        by_type = {}
        query = (
            "SELECT prediction_type, COUNT(*) as total, SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct "
            f"FROM predictions WHERE {where_clause} AND was_correct IS NOT NULL GROUP BY prediction_type"  # nosec B608
        )
        for type_row in conn.execute(query, params):
            t_total = type_row["total"]
            t_correct = type_row["correct"]
            by_type[type_row["prediction_type"]] = {
                "total": t_total,
                "correct": t_correct,
                "accuracy": t_correct / t_total if t_total > 0 else 0,
            }

        # Get by confidence bucket
        by_bucket = {}
        for bucket_row in conn.execute(
            """
            SELECT bucket, total_count, correct_count, avg_confidence
            FROM calibration_data
            WHERE prediction_type = ? OR ? IS NULL
        """,
            (prediction_type, prediction_type),
        ):
            bucket = bucket_row["bucket"]
            by_bucket[bucket] = {
                "total": bucket_row["total_count"],
                "correct": bucket_row["correct_count"],
                "avg_confidence": bucket_row["avg_confidence"],
                "accuracy": bucket_row["correct_count"] / bucket_row["total_count"]
                if bucket_row["total_count"] > 0
                else 0,
            }

        # Compute ECE (Expected Calibration Error)
        ece = self._compute_ece(by_bucket)

        return AccuracyMetrics(
            total_predictions=total,
            resolved_predictions=resolved,
            correct_predictions=correct,
            accuracy_rate=accuracy,
            avg_confidence=avg_conf,
            calibration_error=ece,
            by_type=by_type,
            by_confidence_bucket=by_bucket,
        )

    def _compute_ece(self, by_bucket: dict) -> float:
        """Compute Expected Calibration Error."""
        total_samples = sum(b.get("total", 0) for b in by_bucket.values())
        if total_samples == 0:
            return 0.0

        ece = 0.0
        for bucket, data in by_bucket.items():
            n = data.get("total", 0)
            if n == 0:
                continue

            avg_conf = data.get("avg_confidence", bucket)
            accuracy = data.get("accuracy", 0)

            # |accuracy - confidence| weighted by bucket size
            ece += (n / total_samples) * abs(accuracy - avg_conf)

        return ece

    def start_ab_test(self, test_name: str, variant_a: str, variant_b: str) -> str:
        """
        Start an A/B test between two prediction strategies.

        Args:
            test_name: Name of the test
            variant_a: Name/ID of variant A
            variant_b: Name/ID of variant B

        Returns:
            test_id for tracking
        """
        import uuid

        test_id = str(uuid.uuid4())[:8]

        conn = self._get_connection()
        conn.execute(
            """
            INSERT INTO ab_tests
            (test_id, test_name, variant_a, variant_b, started_at, status)
            VALUES (?, ?, ?, ?, ?, 'running')
        """,
            (test_id, test_name, variant_a, variant_b, datetime.now().isoformat()),
        )
        conn.commit()

        logger.info(f"Started A/B test: {test_name} ({variant_a} vs {variant_b})")
        return test_id

    def end_ab_test(self, test_id: str) -> ABTestResult:
        """
        End an A/B test and compute results.

        Args:
            test_id: ID of the test to end

        Returns:
            ABTestResult with winner and statistics
        """
        conn = self._get_connection()

        # Get test info
        test = conn.execute("SELECT * FROM ab_tests WHERE test_id = ?", (test_id,)).fetchone()

        if not test:
            raise ValueError(f"Test not found: {test_id}")

        variant_a = test["variant_a"]
        variant_b = test["variant_b"]
        started = test["started_at"]

        # Get results for each variant
        def get_variant_stats(variant):
            row = conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct
                FROM predictions
                WHERE strategy = ? AND created_at >= ? AND was_correct IS NOT NULL
            """,
                (variant, started),
            ).fetchone()
            return row["total"] or 0, row["correct"] or 0

        samples_a, correct_a = get_variant_stats(variant_a)
        samples_b, correct_b = get_variant_stats(variant_b)

        accuracy_a = correct_a / samples_a if samples_a > 0 else 0
        accuracy_b = correct_b / samples_b if samples_b > 0 else 0

        # Determine winner
        winner = variant_a if accuracy_a > accuracy_b else variant_b
        if abs(accuracy_a - accuracy_b) < 0.02:  # Within 2%
            winner = "tie"

        # Simple confidence interval (Wilson score for binomial)
        import math

        def wilson_interval(correct, total, z=1.96):
            if total == 0:
                return 0
            p = correct / total
            denominator = 1 + z**2 / total
            (p + z**2 / (2 * total)) / denominator
            margin = (z / denominator) * math.sqrt((p * (1 - p) / total) + (z**2 / (4 * total**2)))
            return margin

        confidence_interval = max(
            wilson_interval(correct_a, samples_a), wilson_interval(correct_b, samples_b)
        )

        # Simple p-value approximation (chi-squared)
        p_value = 0.05  # Placeholder - would need proper statistical test

        # Update test record
        conn.execute(
            """
            UPDATE ab_tests
            SET ended_at = ?, winner = ?, status = 'completed'
            WHERE test_id = ?
        """,
            (datetime.now().isoformat(), winner, test_id),
        )
        conn.commit()

        return ABTestResult(
            test_name=test["test_name"],
            variant_a=variant_a,
            variant_b=variant_b,
            samples_a=samples_a,
            samples_b=samples_b,
            accuracy_a=accuracy_a,
            accuracy_b=accuracy_b,
            winner=winner,
            confidence_interval=confidence_interval,
            p_value=p_value,
        )

    def get_calibration_chart_data(self, prediction_type: Optional[str] = None) -> dict:
        """
        Get data for a calibration chart (reliability diagram).

        Returns:
            Dict with bucket data for plotting
        """
        conn = self._get_connection()

        where = "1=1"
        params = []
        if prediction_type:
            where = "prediction_type = ?"
            params = [prediction_type]

        query = f"SELECT bucket, total_count, correct_count, avg_confidence FROM calibration_data WHERE {where} ORDER BY bucket"  # nosec B608
        rows = conn.execute(query, params).fetchall()

        buckets = []
        expected = []
        actual = []

        for row in rows:
            buckets.append(row["bucket"])
            expected.append(row["avg_confidence"])
            actual.append(
                row["correct_count"] / row["total_count"] if row["total_count"] > 0 else 0
            )

        return {
            "buckets": buckets,
            "expected_accuracy": expected,
            "actual_accuracy": actual,
            "perfect_calibration": buckets,  # Reference line
        }

    def get_improvement_suggestions(self) -> list[str]:
        """Get suggestions for improving predictions based on metrics."""
        metrics = self.get_accuracy_metrics()
        suggestions = []

        # Check overall accuracy
        if metrics.accuracy_rate < 0.6:
            suggestions.append(
                "⚠️ Overall accuracy is below 60%. Consider reviewing prediction logic."
            )

        # Check calibration
        if metrics.calibration_error > 0.15:
            suggestions.append(
                "📊 Calibration error is high. Confidence scores don't match actual accuracy."
            )

        # Check by type
        for pred_type, data in metrics.by_type.items():
            if data.get("accuracy", 0) < 0.5 and data.get("total", 0) > 10:
                suggestions.append(
                    f"🔍 {pred_type} predictions have low accuracy ({data['accuracy']:.1%})"
                )

        # Check sample size
        if metrics.resolved_predictions < 50:
            suggestions.append("📈 Need more resolved predictions for reliable metrics.")

        if not suggestions:
            suggestions.append("✅ Prediction accuracy looks good!")

        return suggestions


# Singleton instance
_prediction_tracker: Optional[PredictionTracker] = None


def get_prediction_tracker(project_root: Path) -> PredictionTracker:
    """Get or create prediction tracker singleton."""
    global _prediction_tracker
    if _prediction_tracker is None:
        _prediction_tracker = PredictionTracker(project_root)
    return _prediction_tracker
