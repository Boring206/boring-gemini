"""
Predictive Analyzer - Error Prediction and Trend Analysis (V10.23 Enhanced)

Proactive intelligence features:
1. Predict likely errors before code execution
2. Detect error trends and patterns
3. Suggest preventive actions
4. Forecast project health metrics
5. 🆕 Code change impact prediction
6. 🆕 Session-based error correlation
7. 🆕 Multi-factor confidence scoring
8. 🆕 Proactive fix suggestions with code snippets

This transforms Boring from reactive to predictive.
"""

import sqlite3
import threading
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Thread-local connection
_local = threading.local()


@dataclass
class ErrorPrediction:
    """A predicted error with confidence."""

    error_type: str
    predicted_message: str
    confidence: float  # 0.0 - 1.0
    reason: str  # Why we predict this
    prevention_tip: str  # How to prevent
    historical_frequency: int
    # V10.23: Enhanced fields
    code_snippet: str = ""  # Example fix
    related_files: list = field(default_factory=list)  # Files with similar errors
    impact_score: float = 0.0  # How severe if occurs


@dataclass
class TrendData:
    """Trend analysis result."""

    metric_name: str
    current_value: float
    previous_value: float
    trend_direction: str  # "up", "down", "stable"
    change_percent: float
    prediction_next: float
    confidence: float
    # V10.23: Enhanced fields
    volatility: float = 0.0  # How much the metric fluctuates
    forecast_7d: list = field(default_factory=list)  # 7-day forecast


@dataclass
class HealthScore:
    """Project health assessment."""

    overall_score: float  # 0-100
    success_rate: float
    error_diversity: float  # Lower is better
    resolution_rate: float
    trend: str  # "improving", "declining", "stable"
    recommendations: list[str]
    # V10.23: Enhanced fields
    risk_areas: list = field(default_factory=list)  # High-risk file patterns
    momentum_score: float = 0.0  # Rate of improvement


@dataclass
class ChangeImpact:
    """V10.23: Predicted impact of code changes."""

    file_path: str
    predicted_errors: list[ErrorPrediction]
    risk_level: str  # "low", "medium", "high"
    affected_files: list[str]
    recommendation: str


class PredictiveAnalyzer:
    """
    Predictive analytics for Boring (V10.23 Enhanced).

    Analyzes historical patterns to:
    - Predict likely errors
    - Detect anomalies
    - Forecast project health
    - Suggest preventive actions
    - 🆕 Predict change impact
    - 🆕 Session-aware predictions
    - 🆕 Multi-factor confidence scoring
    - 🆕 Proactive fix suggestions

    Usage:
        analyzer = PredictiveAnalyzer(project_root)

        # Predict errors for a file
        predictions = analyzer.predict_errors("src/auth.py")

        # Get health trend
        health = analyzer.get_health_score()

        # V10.23: Predict change impact
        impact = analyzer.predict_change_impact("src/auth.py", changes)
    """

    # V10.23: Error severity weights
    ERROR_SEVERITY = {
        "SyntaxError": 0.9,
        "ImportError": 0.8,
        "TypeError": 0.7,
        "NameError": 0.7,
        "AttributeError": 0.6,
        "KeyError": 0.5,
        "ValueError": 0.5,
        "IndexError": 0.5,
        "RuntimeError": 0.8,
        "MemoryError": 0.95,
        "RecursionError": 0.85,
    }

    def __init__(self, project_root: Path, storage=None):
        self.project_root = Path(project_root)
        self.db_path = self.project_root / ".boring_memory" / "analytics.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage = storage  # SQLiteStorage for historical data
        self._init_db()

        # Cache for pattern analysis
        self._error_patterns: dict[str, list] = {}
        self._file_error_map: dict[str, Counter] = defaultdict(Counter)
        self._cache_lock = threading.RLock()
        self._patterns_loaded = False

        # V10.23: Session tracking
        self._session_errors: list[tuple[str, str, float]] = []  # (file, error_type, timestamp)
        self._session_start = datetime.now()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        conn = getattr(_local, f"predict_conn_{id(self)}", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            setattr(_local, f"predict_conn_{id(self)}", conn)
        return conn

    def _init_db(self):
        """Initialize analytics database (V10.23 Enhanced)."""
        conn = self._get_connection()
        conn.executescript("""
            -- Error correlations (file -> error type patterns)
            CREATE TABLE IF NOT EXISTS error_correlations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_pattern TEXT NOT NULL,
                error_type TEXT NOT NULL,
                occurrence_count INTEGER DEFAULT 1,
                last_seen TEXT,
                avg_fix_time_seconds REAL,
                UNIQUE(file_pattern, error_type)
            );

            -- Time series metrics for trend analysis
            CREATE TABLE IF NOT EXISTS metrics_timeseries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp TEXT NOT NULL,
                window TEXT DEFAULT 'day'  -- 'hour', 'day', 'week'
            );

            -- Anomaly detection baseline
            CREATE TABLE IF NOT EXISTS metric_baselines (
                metric_name TEXT PRIMARY KEY,
                mean_value REAL,
                std_value REAL,
                sample_count INTEGER,
                updated_at TEXT
            );

            -- Prevention tips learned
            CREATE TABLE IF NOT EXISTS prevention_tips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_type TEXT NOT NULL,
                tip TEXT NOT NULL,
                effectiveness_score REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0,
                created_at TEXT,
                UNIQUE(error_type, tip)
            );

            -- V10.23: Code snippets for fixes
            CREATE TABLE IF NOT EXISTS fix_snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_type TEXT NOT NULL,
                pattern TEXT NOT NULL,
                fix_code TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                created_at TEXT,
                UNIQUE(error_type, pattern)
            );

            -- V10.23: File change history for impact prediction
            CREATE TABLE IF NOT EXISTS file_change_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                change_type TEXT NOT NULL,
                error_within_1h INTEGER DEFAULT 0,
                timestamp TEXT NOT NULL
            );

            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_corr_file ON error_correlations(file_pattern);
            CREATE INDEX IF NOT EXISTS idx_ts_metric ON metrics_timeseries(metric_name, timestamp);
            CREATE INDEX IF NOT EXISTS idx_fix_error ON fix_snippets(error_type);
            CREATE INDEX IF NOT EXISTS idx_change_file ON file_change_history(file_path, timestamp);
        """)
        conn.commit()

    def _load_patterns(self):
        """Load error patterns into memory for fast prediction."""
        if self._patterns_loaded:
            return

        with self._cache_lock:
            if self._patterns_loaded:
                return

            conn = self._get_connection()
            rows = conn.execute("""
                SELECT file_pattern, error_type, occurrence_count
                FROM error_correlations
                ORDER BY occurrence_count DESC
            """).fetchall()

            for row in rows:
                pattern = row["file_pattern"]
                if pattern not in self._error_patterns:
                    self._error_patterns[pattern] = []
                self._error_patterns[pattern].append(
                    {"error_type": row["error_type"], "count": row["occurrence_count"]}
                )

            self._patterns_loaded = True

    def learn_error_correlation(self, file_path: str, error_type: str, fix_time_seconds: float = 0):
        """Learn that a file pattern tends to produce a certain error."""
        # Extract pattern from file path
        pattern = self._extract_file_pattern(file_path)
        timestamp = datetime.now().isoformat()

        conn = self._get_connection()

        # Upsert correlation
        conn.execute(
            """
            INSERT INTO error_correlations (file_pattern, error_type, last_seen, avg_fix_time_seconds)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(file_pattern, error_type) DO UPDATE SET
                occurrence_count = occurrence_count + 1,
                last_seen = excluded.last_seen,
                avg_fix_time_seconds = (avg_fix_time_seconds * occurrence_count + excluded.avg_fix_time_seconds) / (occurrence_count + 1)
        """,
            (pattern, error_type, timestamp, fix_time_seconds),
        )
        conn.commit()

        # Invalidate cache
        with self._cache_lock:
            self._patterns_loaded = False
            self._error_patterns.clear()

    def _extract_file_pattern(self, file_path: str) -> str:
        """Extract meaningful pattern from file path.

        Examples:
            "src/auth/login.py" -> "auth/*.py"
            "tests/test_user.py" -> "tests/test_*.py"
            "components/Button.tsx" -> "components/*.tsx"
        """
        path = Path(file_path)

        # Get parent directory and extension
        parent = path.parent.name if path.parent.name else ""
        ext = path.suffix
        name = path.stem

        # Check for common patterns
        if name.startswith("test_"):
            return f"{parent}/test_*{ext}" if parent else f"test_*{ext}"
        elif name.startswith("Test"):
            return f"{parent}/Test*{ext}" if parent else f"Test*{ext}"
        elif parent:
            return f"{parent}/*{ext}"
        else:
            return f"*{ext}"

    def predict_errors(self, file_path: str, limit: int = 5) -> list[ErrorPrediction]:
        """
        Predict likely errors for a file based on historical patterns.

        Args:
            file_path: Path to the file being worked on
            limit: Maximum predictions to return

        Returns:
            List of ErrorPrediction with confidence scores
        """
        self._load_patterns()

        pattern = self._extract_file_pattern(file_path)
        predictions = []

        # Direct pattern match
        if pattern in self._error_patterns:
            for err in self._error_patterns[pattern][:limit]:
                confidence = min(0.9, 0.3 + (err["count"] * 0.05))
                predictions.append(
                    ErrorPrediction(
                        error_type=err["error_type"],
                        predicted_message=f"Based on {err['count']} past occurrences in {pattern} files",
                        confidence=round(confidence, 2),
                        reason=f"Files matching '{pattern}' frequently produce this error",
                        prevention_tip=self._get_prevention_tip(err["error_type"]),
                        historical_frequency=err["count"],
                    )
                )

        # Also check broader patterns
        ext = Path(file_path).suffix
        broader_pattern = f"*{ext}"
        if broader_pattern in self._error_patterns and broader_pattern != pattern:
            for err in self._error_patterns[broader_pattern][:2]:
                if not any(p.error_type == err["error_type"] for p in predictions):
                    confidence = min(0.6, 0.2 + (err["count"] * 0.03))
                    predictions.append(
                        ErrorPrediction(
                            error_type=err["error_type"],
                            predicted_message=f"Common in {ext} files ({err['count']} occurrences)",
                            confidence=round(confidence, 2),
                            reason=f"Frequently seen in files with {ext} extension",
                            prevention_tip=self._get_prevention_tip(err["error_type"]),
                            historical_frequency=err["count"],
                        )
                    )

        # Sort by confidence
        predictions.sort(key=lambda x: x.confidence, reverse=True)
        return predictions[:limit]

    def _get_prevention_tip(self, error_type: str) -> str:
        """Get prevention tip for an error type."""
        conn = self._get_connection()
        row = conn.execute(
            "SELECT tip FROM prevention_tips WHERE error_type = ? ORDER BY effectiveness_score DESC LIMIT 1",
            (error_type,),
        ).fetchone()

        if row:
            return row["tip"]

        # Default tips based on common error types
        default_tips = {
            "SyntaxError": "Run syntax check before execution",
            "ImportError": "Verify all imports are installed",
            "TypeError": "Check function signatures and argument types",
            "NameError": "Ensure all variables are defined before use",
            "AttributeError": "Verify object has the expected attributes",
            "KeyError": "Use .get() with default for dict access",
            "IndexError": "Check list bounds before indexing",
            "ValueError": "Validate input data before processing",
        }

        return default_tips.get(error_type, "Review code carefully before running")

    def add_prevention_tip(self, error_type: str, tip: str, effectiveness: float = 0.5):
        """Add or update a prevention tip."""
        conn = self._get_connection()
        conn.execute(
            """
            INSERT INTO prevention_tips (error_type, tip, effectiveness_score, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(error_type, tip) DO UPDATE SET
                effectiveness_score = (effectiveness_score + excluded.effectiveness_score) / 2,
                usage_count = usage_count + 1
        """,
            (error_type, tip, effectiveness, datetime.now().isoformat()),
        )
        conn.commit()

    def record_metric(self, metric_name: str, value: float, window: str = "day"):
        """Record a metric for time series analysis."""
        conn = self._get_connection()
        conn.execute(
            "INSERT INTO metrics_timeseries (metric_name, metric_value, timestamp, window) VALUES (?, ?, ?, ?)",
            (metric_name, value, datetime.now().isoformat(), window),
        )
        conn.commit()

        # Update baseline
        self._update_baseline(metric_name, value)

    def _update_baseline(self, metric_name: str, new_value: float):
        """Update running baseline for anomaly detection."""
        conn = self._get_connection()

        row = conn.execute(
            "SELECT mean_value, std_value, sample_count FROM metric_baselines WHERE metric_name = ?",
            (metric_name,),
        ).fetchone()

        if row:
            # Welford's online algorithm for running mean/std
            n = row["sample_count"] + 1
            old_mean = row["mean_value"]
            old_std = row["std_value"]

            new_mean = old_mean + (new_value - old_mean) / n
            # Simplified std update
            new_std = ((old_std**2) * (n - 1) + (new_value - new_mean) * (new_value - old_mean)) / n
            new_std = new_std**0.5 if new_std > 0 else 0

            conn.execute(
                "UPDATE metric_baselines SET mean_value = ?, std_value = ?, sample_count = ?, updated_at = ? WHERE metric_name = ?",
                (new_mean, new_std, n, datetime.now().isoformat(), metric_name),
            )
        else:
            conn.execute(
                "INSERT INTO metric_baselines (metric_name, mean_value, std_value, sample_count, updated_at) VALUES (?, ?, 0, 1, ?)",
                (metric_name, new_value, datetime.now().isoformat()),
            )

        conn.commit()

    def get_trend(self, metric_name: str, days: int = 7) -> Optional[TrendData]:
        """Analyze trend for a metric over time."""
        conn = self._get_connection()

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        rows = conn.execute(
            """
            SELECT metric_value, timestamp
            FROM metrics_timeseries
            WHERE metric_name = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        """,
            (metric_name, cutoff),
        ).fetchall()

        if len(rows) < 2:
            return None

        values = [r["metric_value"] for r in rows]

        # Calculate trend
        midpoint = len(values) // 2
        first_half_avg = sum(values[:midpoint]) / midpoint if midpoint > 0 else 0
        second_half_avg = (
            sum(values[midpoint:]) / (len(values) - midpoint) if len(values) > midpoint else 0
        )

        current = values[-1]
        previous = values[0]

        if first_half_avg == 0:
            change_percent = 0
        else:
            change_percent = ((second_half_avg - first_half_avg) / first_half_avg) * 100

        if change_percent > 5:
            trend_dir = "up"
        elif change_percent < -5:
            trend_dir = "down"
        else:
            trend_dir = "stable"

        # Simple linear prediction
        avg_change = (values[-1] - values[0]) / len(values) if len(values) > 1 else 0
        prediction = values[-1] + avg_change

        return TrendData(
            metric_name=metric_name,
            current_value=current,
            previous_value=previous,
            trend_direction=trend_dir,
            change_percent=round(change_percent, 1),
            prediction_next=round(prediction, 2),
            confidence=min(0.9, len(rows) * 0.1),  # More data = higher confidence
        )

    def is_anomaly(self, metric_name: str, value: float, threshold: float = 2.0) -> bool:
        """Check if a value is anomalous (beyond threshold std from mean)."""
        conn = self._get_connection()
        row = conn.execute(
            "SELECT mean_value, std_value FROM metric_baselines WHERE metric_name = ?",
            (metric_name,),
        ).fetchone()

        if not row or row["std_value"] == 0:
            return False

        z_score = abs(value - row["mean_value"]) / row["std_value"]
        return z_score > threshold

    def get_health_score(self) -> HealthScore:
        """Calculate overall project health score."""
        recommendations = []

        # Get success rate trend
        success_trend = self.get_trend("success_rate", days=7)
        success_rate = success_trend.current_value if success_trend else 0.5

        # Count unique error types (diversity)
        conn = self._get_connection()
        error_count = conn.execute(
            "SELECT COUNT(DISTINCT error_type) FROM error_correlations"
        ).fetchone()[0]
        error_diversity = min(1.0, error_count / 10.0)  # Normalize to 0-1

        # Resolution rate (how many errors have prevention tips)
        tips_count = conn.execute(
            "SELECT COUNT(DISTINCT error_type) FROM prevention_tips"
        ).fetchone()[0]
        resolution_rate = tips_count / max(1, error_count)

        # Calculate overall score
        overall = (
            success_rate * 40  # 40% weight
            + (1 - error_diversity) * 30  # 30% weight (lower diversity is better)
            + resolution_rate * 30  # 30% weight
        )

        # Determine trend
        if success_trend and success_trend.trend_direction == "up":
            trend = "improving"
        elif success_trend and success_trend.trend_direction == "down":
            trend = "declining"
            recommendations.append("Success rate is declining. Review recent changes.")
        else:
            trend = "stable"

        # Add recommendations
        if error_diversity > 0.5:
            recommendations.append(
                f"High error diversity ({error_count} types). Consider adding type hints and tests."
            )
        if resolution_rate < 0.5:
            recommendations.append("Add more prevention tips to improve future predictions.")
        if success_rate < 0.7:
            recommendations.append("Success rate is low. Enable more quality gates.")

        return HealthScore(
            overall_score=round(overall, 1),
            success_rate=round(success_rate, 2),
            error_diversity=round(error_diversity, 2),
            resolution_rate=round(resolution_rate, 2),
            trend=trend,
            recommendations=recommendations,
        )

    def cleanup_old_data(self, days: int = 90):
        """Remove old analytics data."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        conn = self._get_connection()
        conn.execute("DELETE FROM metrics_timeseries WHERE timestamp < ?", (cutoff,))
        conn.commit()

    # ============================================================
    # V10.23: Enhanced Predictive Methods
    # ============================================================

    def predict_change_impact(self, file_path: str, change_type: str = "modify") -> ChangeImpact:
        """
        V10.23: Predict the impact of making changes to a file.

        Args:
            file_path: Path to the file being changed
            change_type: Type of change ("modify", "refactor", "delete")

        Returns:
            ChangeImpact with predicted errors and recommendations
        """
        # Get error predictions for this file
        predictions = self.predict_errors(file_path, limit=5)

        # Analyze historical change patterns
        conn = self._get_connection()
        pattern = self._extract_file_pattern(file_path)

        # Check if changes to similar files caused errors
        rows = conn.execute(
            """
            SELECT COUNT(*) as total, SUM(error_within_1h) as errors
            FROM file_change_history
            WHERE file_path LIKE ?
        """,
            (f"%{pattern}%",),
        ).fetchone()

        total_changes = rows["total"] if rows["total"] else 0
        error_changes = rows["errors"] if rows["errors"] else 0

        # Calculate risk level
        if total_changes < 3:
            risk_level = "low"  # Not enough data
        elif error_changes / max(1, total_changes) > 0.5:
            risk_level = "high"
        elif error_changes / max(1, total_changes) > 0.2:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Find affected files (files often changed together)
        affected = self._find_related_files(file_path)

        # Build recommendation
        recommendations = []
        if risk_level == "high":
            recommendations.append("⚠️ High-risk change. Consider incremental commits.")
        if predictions:
            top_error = predictions[0]
            recommendations.append(f"Watch for {top_error.error_type}: {top_error.prevention_tip}")
        if affected:
            recommendations.append(f"Also check: {', '.join(affected[:3])}")

        recommendation = (
            " ".join(recommendations) if recommendations else "Proceed with normal caution."
        )

        return ChangeImpact(
            file_path=file_path,
            predicted_errors=predictions,
            risk_level=risk_level,
            affected_files=affected,
            recommendation=recommendation,
        )

    def _find_related_files(self, file_path: str, limit: int = 5) -> list[str]:
        """V10.23: Find files that are often changed together."""
        # Simple heuristic: same directory, same extension
        path = Path(file_path)

        conn = self._get_connection()
        rows = conn.execute(
            """
            SELECT DISTINCT file_path FROM file_change_history
            WHERE file_path LIKE ? AND file_path != ?
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (f"%{path.parent.name}%", file_path, limit),
        ).fetchall()

        return [row["file_path"] for row in rows]

    def record_session_error(self, file_path: str, error_type: str):
        """V10.23: Record an error in the current session for correlation analysis."""
        with self._cache_lock:
            self._session_errors.append((file_path, error_type, datetime.now().timestamp()))

            # Keep only last 100 errors
            if len(self._session_errors) > 100:
                self._session_errors = self._session_errors[-100:]

    def get_session_insights(self) -> dict:
        """V10.23: Analyze error patterns in current session."""
        with self._cache_lock:
            if not self._session_errors:
                return {
                    "session_duration_minutes": self._get_session_duration(),
                    "total_errors": 0,
                    "error_rate_per_hour": 0.0,
                    "top_errors": [],
                    "problematic_files": [],
                    "pattern": "No errors yet! 🎉",
                }

            # Count errors by type
            error_counts = Counter(e[1] for e in self._session_errors)
            file_counts = Counter(e[0] for e in self._session_errors)

            duration_hours = max(0.1, self._get_session_duration() / 60)
            error_rate = len(self._session_errors) / duration_hours

            # Detect patterns
            if error_rate > 10:
                pattern = "⚠️ High error rate. Consider taking a break."
            elif len(error_counts) == 1:
                pattern = f"Focused on one error type: {list(error_counts.keys())[0]}"
            elif len(file_counts) == 1:
                pattern = f"All errors in one file: {list(file_counts.keys())[0]}"
            else:
                pattern = "Normal debugging session"

            return {
                "session_duration_minutes": round(self._get_session_duration(), 1),
                "total_errors": len(self._session_errors),
                "error_rate_per_hour": round(error_rate, 1),
                "top_errors": error_counts.most_common(3),
                "problematic_files": file_counts.most_common(3),
                "pattern": pattern,
            }

    def _get_session_duration(self) -> float:
        """Get session duration in minutes."""
        return (datetime.now() - self._session_start).total_seconds() / 60

    def _compute_multi_factor_confidence(
        self,
        base_confidence: float,
        historical_count: int,
        recency_days: float,
        session_match: bool,
    ) -> float:
        """
        V10.23: Compute confidence using multiple factors.

        Factors:
        - Historical frequency (more occurrences = higher confidence)
        - Recency (recent errors weighted higher)
        - Session correlation (if same error in current session)
        """
        # Historical factor: log scale, max 0.3 boost
        history_factor = min(0.3, historical_count * 0.03)

        # Recency factor: decay over time
        recency_factor = max(0.0, 0.2 - (recency_days * 0.01))

        # Session factor: boost if seen in current session
        session_factor = 0.15 if session_match else 0.0

        # Combine
        final_confidence = min(
            0.95, base_confidence + history_factor + recency_factor + session_factor
        )
        return round(final_confidence, 2)

    def learn_fix_snippet(self, error_type: str, pattern: str, fix_code: str):
        """V10.23: Learn a successful fix snippet for an error type."""
        conn = self._get_connection()
        conn.execute(
            """
            INSERT INTO fix_snippets (error_type, pattern, fix_code, success_count, created_at)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(error_type, pattern) DO UPDATE SET
                success_count = success_count + 1,
                fix_code = excluded.fix_code
        """,
            (error_type, pattern, fix_code, datetime.now().isoformat()),
        )
        conn.commit()

    def get_fix_snippet(self, error_type: str) -> Optional[str]:
        """V10.23: Get a learned fix snippet for an error type."""
        conn = self._get_connection()
        row = conn.execute(
            """
            SELECT fix_code FROM fix_snippets
            WHERE error_type = ?
            ORDER BY success_count DESC
            LIMIT 1
        """,
            (error_type,),
        ).fetchone()

        return row["fix_code"] if row else None

    def record_file_change(self, file_path: str, change_type: str = "modify"):
        """V10.23: Record a file change for impact analysis."""
        conn = self._get_connection()
        conn.execute(
            """
            INSERT INTO file_change_history (file_path, change_type, timestamp)
            VALUES (?, ?, ?)
        """,
            (file_path, change_type, datetime.now().isoformat()),
        )
        conn.commit()

    def mark_change_caused_error(self, file_path: str, window_hours: int = 1):
        """V10.23: Mark that a recent change to a file caused an error."""
        cutoff = (datetime.now() - timedelta(hours=window_hours)).isoformat()

        conn = self._get_connection()
        conn.execute(
            """
            UPDATE file_change_history
            SET error_within_1h = 1
            WHERE file_path = ? AND timestamp >= ?
        """,
            (file_path, cutoff),
        )
        conn.commit()

    def get_risk_areas(self, limit: int = 5) -> list[dict]:
        """V10.23: Identify high-risk file patterns."""
        conn = self._get_connection()
        rows = conn.execute(
            """
            SELECT file_pattern, error_type, occurrence_count, avg_fix_time_seconds
            FROM error_correlations
            ORDER BY occurrence_count DESC
            LIMIT ?
        """,
            (limit,),
        ).fetchall()

        return [
            {
                "pattern": row["file_pattern"],
                "error_type": row["error_type"],
                "occurrences": row["occurrence_count"],
                "avg_fix_time": round(row["avg_fix_time_seconds"] or 0, 1),
                "severity": self.ERROR_SEVERITY.get(row["error_type"], 0.5),
            }
            for row in rows
        ]

    def get_prediction_report(self, file_path: str) -> str:
        """V10.23: Get human-readable prediction report for a file."""
        predictions = self.predict_errors(file_path)
        impact = self.predict_change_impact(file_path)
        session = self.get_session_insights()

        report_lines = [
            f"🔮 Prediction Report for `{Path(file_path).name}`",
            "",
            f"📊 Risk Level: {impact.risk_level.upper()}",
            "",
        ]

        if predictions:
            report_lines.append("⚠️ Predicted Errors:")
            for i, pred in enumerate(predictions[:3], 1):
                report_lines.append(f"  {i}. {pred.error_type} ({pred.confidence:.0%} confidence)")
                report_lines.append(f"     💡 {pred.prevention_tip}")
        else:
            report_lines.append("✅ No specific errors predicted")

        report_lines.extend(
            [
                "",
                "📈 Session Stats:",
                f"  • Duration: {session['session_duration_minutes']:.0f} min",
                f"  • Errors: {session['total_errors']}",
                f"  • Pattern: {session['pattern']}",
            ]
        )

        if impact.affected_files:
            report_lines.extend(["", f"🔗 Related Files: {', '.join(impact.affected_files[:3])}"])

        return "\n".join(report_lines)
