import json
from unittest.mock import patch

import pytest

from boring.intelligence.prediction_tracker import PredictionTracker, _local, get_prediction_tracker


@pytest.fixture
def temp_root(tmp_path):
    return tmp_path


@pytest.fixture
def tracker(temp_root):
    # Ensure fresh tracker and connection for each test
    if hasattr(_local, "prediction_conn"):
        try:
            _local.prediction_conn.close()
        except:
            pass
        del _local.prediction_conn

    t = PredictionTracker(temp_root)
    yield t

    if hasattr(_local, "prediction_conn"):
        try:
            _local.prediction_conn.close()
        except:
            pass
        del _local.prediction_conn


class TestPredictionTracker:
    def test_init(self, tracker, temp_root):
        assert tracker.project_root == temp_root
        # The file is created during _init_db
        assert tracker.db_path.exists()

        # Verify tables exist
        conn = tracker._get_connection()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        assert "predictions" in table_names
        assert "ab_tests" in table_names
        assert "calibration_data" in table_names

    def test_record_prediction(self, tracker):
        ctx = {"file": "test.py"}
        tracker.record_prediction(
            prediction_id="p1",
            prediction_type="error",
            predicted_value="SyntaxError",
            confidence=0.8,
            context=ctx,
        )

        conn = tracker._get_connection()
        row = conn.execute("SELECT * FROM predictions WHERE prediction_id='p1'").fetchone()
        assert row["prediction_type"] == "error"
        assert row["confidence"] == 0.8
        assert json.loads(row["context_json"]) == ctx

    def test_resolve_prediction(self, tracker):
        tracker.record_prediction("p1", "error", "v1", 0.9)
        tracker.resolve_prediction("p1", "v1", True)

        conn = tracker._get_connection()
        row = conn.execute("SELECT * FROM predictions WHERE prediction_id='p1'").fetchone()
        assert row["was_correct"] == 1
        assert row["actual_outcome"] == "v1"
        assert row["resolved_at"] is not None

        # Check calibration update
        cal = conn.execute("SELECT * FROM calibration_data WHERE bucket=0.9").fetchone()
        assert cal["total_count"] == 1
        assert cal["correct_count"] == 1

    def test_get_accuracy_metrics(self, tracker):
        # Setup data
        tracker.record_prediction("p1", "error", "v1", 0.9)
        tracker.resolve_prediction("p1", "v1", True)
        tracker.record_prediction("p2", "error", "v1", 0.8)
        tracker.resolve_prediction("p2", "v2", False)
        tracker.record_prediction("p3", "impact", "high", 0.5)
        # p3 is unresolved

        metrics = tracker.get_accuracy_metrics()
        assert metrics.total_predictions == 3
        assert metrics.resolved_predictions == 2
        assert metrics.correct_predictions == 1
        assert metrics.accuracy_rate == 0.5
        assert "error" in metrics.by_type
        assert metrics.by_type["error"]["total"] == 2

    def test_ab_test_workflow(self, tracker):
        test_id = tracker.start_ab_test("Strategy Comparison", "variant_a", "variant_b")
        assert test_id is not None

        # Record some predictions for variant_a
        tracker.record_prediction("pa1", "error", "v1", 0.9, strategy="variant_a")
        tracker.resolve_prediction("pa1", "v1", True)

        # Record for variant_b (failed)
        tracker.record_prediction("pb1", "error", "v1", 0.9, strategy="variant_b")
        tracker.resolve_prediction("pb1", "v2", False)

        result = tracker.end_ab_test(test_id)
        assert result.variant_a == "variant_a"
        assert result.accuracy_a == 1.0
        assert result.accuracy_b == 0.0
        assert result.winner == "variant_a"

    def test_get_calibration_chart_data(self, tracker):
        tracker.record_prediction("p1", "error", "v1", 0.9)
        tracker.resolve_prediction("p1", "v1", True)

        data = tracker.get_calibration_chart_data()
        assert 0.9 in data["buckets"]
        assert 1.0 in data["actual_accuracy"]

    def test_get_improvement_suggestions(self, tracker):
        # Good accuracy setup
        # We need enough samples to trigger specific suggestions
        for i in range(10):
            pid = f"good_{i}"
            tracker.record_prediction(pid, "error", "v", 1.0)
            tracker.resolve_prediction(pid, "v", True)

        suggestions = tracker.get_improvement_suggestions()
        assert any(
            "Accuracy looks good" in s or "Need more resolved predictions" in s for s in suggestions
        )

    def test_singleton(self, temp_root):
        with patch("boring.intelligence.prediction_tracker._prediction_tracker", None):
            t1 = get_prediction_tracker(temp_root)
            t2 = get_prediction_tracker(temp_root)
            assert t1 is t2

    def test_compute_ece(self, tracker):
        by_bucket = {
            0.9: {"total": 10, "correct": 9, "avg_confidence": 0.9, "accuracy": 0.9},
            0.1: {"total": 10, "correct": 5, "avg_confidence": 0.1, "accuracy": 0.5},
        }
        # ECE = (10/20)*|0.9-0.9| + (10/20)*|0.5-0.1| = 0.5 * 0.4 = 0.2
        ece = tracker._compute_ece(by_bucket)
        assert pytest.approx(ece) == 0.2
