"""
Tests for TokenTracker.
"""

import json

import pytest

from boring.metrics.token_tracker import TokenTracker


@pytest.fixture
def tracker(tmp_path):
    return TokenTracker(tmp_path)


def test_estimate_tokens(tracker):
    text = "Hello world"
    # 11 chars / 4 = 2.75 -> ceil 3
    assert tracker.estimate_tokens(text) == 3
    assert tracker.estimate_tokens("") == 0


def test_calculate_cost(tracker):
    # Gemini 1.5 Flash: input 0.35, output 1.05
    cost = tracker.calculate_cost("gemini-1.5-flash", 1_000_000, 0)
    assert abs(cost - 0.35) < 0.0001

    cost = tracker.calculate_cost("gemini-1.5-flash", 0, 1_000_000)
    assert abs(cost - 1.05) < 0.0001


def test_track_usage_persistence(tracker, tmp_path):
    tracker.track_usage("gemini-1.5-flash", 1000, 500)

    stats_file = tmp_path / ".boring" / "usage_stats.json"
    assert stats_file.exists()

    data = json.loads(stats_file.read_text())
    assert data["total_input_tokens"] == 1000
    assert data["total_output_tokens"] == 500
    assert "gemini-1.5-flash" in data["breakdown"]
