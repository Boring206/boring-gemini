from unittest.mock import patch

import pytest

from boring.mcp.tools.quality import boring_quality_trend
from boring.quality_tracker import QualityTracker


@pytest.fixture
def mock_settings(tmp_path):
    with patch("boring.quality_tracker.settings") as mock:
        mock.PROJECT_ROOT = tmp_path
        mock.BRAIN_DIR = ".boring_brain"
        # Ensure brain dir exists in tmp path
        (tmp_path / ".boring_brain").mkdir(parents=True, exist_ok=True)
        yield mock


def test_quality_tracker_record(mock_settings, tmp_path):
    tracker = QualityTracker(project_root=tmp_path)
    tracker.record(score=4.5, issues_count=2, context="test")

    history = tracker.get_trend()
    assert len(history) == 1
    assert history[0]["score"] == 4.5
    assert history[0]["issues_count"] == 2
    assert history[0]["context"] == "test"

    # Add another entry
    tracker.record(score=4.8, issues_count=0)
    history = tracker.get_trend()
    assert len(history) == 2
    assert history[1]["score"] == 4.8


def test_quality_history_limit(mock_settings, tmp_path):
    tracker = QualityTracker(project_root=tmp_path)
    # Record 110 entries
    for i in range(110):
        tracker.record(score=float(i % 5), issues_count=0)

    history = tracker.get_trend(limit=200)
    assert len(history) == 100  # Should be capped at 100


def test_ascii_chart(mock_settings, tmp_path):
    tracker = QualityTracker(project_root=tmp_path)
    tracker.record(score=1.0, issues_count=10)
    tracker.record(score=2.0, issues_count=8)
    tracker.record(score=3.0, issues_count=5)
    tracker.record(score=5.0, issues_count=0)

    chart = tracker.render_ascii_chart(width=20, height=5)
    assert "Quality Trend" in chart
    assert "Score: 5.0" in chart
    assert "*" in chart  # Bars should be present


@patch("boring.mcp.tools.quality.QualityTracker")
def test_boring_quality_trend_tool(MockTracker):
    # Setup mock
    mock_instance = MockTracker.return_value
    mock_instance.render_ascii_chart.return_value = "||| Chart |||"
    mock_instance.get_trend.return_value = [{"score": 4.2, "issues_count": 3, "date": "2026-01-05"}]

    result = boring_quality_trend(days=30)

    assert "Quality Trend Report" in result["message"]
    assert "4.2/5.0" in result["message"]
    assert "||| Chart |||" in result["message"]
    assert "**Open Issues**: 3" in result["message"]
