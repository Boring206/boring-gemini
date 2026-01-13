
import pytest

from boring.intelligence.usage_tracker import AnomalyDetectedError, UsageTracker


@pytest.mark.unit
def test_anomaly_detection_logic(tmp_path):
    """Test standard valid usage."""
    tracker = UsageTracker(persistence_path=tmp_path / "usage.json")
    tracker.ANOMALY_THRESHOLD = 5  # Lower for testing

    # Valid usage: alternating calls
    for _ in range(10):
        tracker.track("tool_a", tool_args={"arg": 1})
        tracker.track("tool_b", tool_args={"arg": 2})

    assert tracker.repeat_count == 1
    assert tracker.stats.tools["tool_a"].count == 10

@pytest.mark.unit
def test_anomaly_detection_loop(tmp_path):
    """Test identical call loop triggers error."""
    tracker = UsageTracker(persistence_path=tmp_path / "usage.json")
    tracker.ANOMALY_THRESHOLD = 5

    # Fill up to threshold
    for _ in range(5):
        tracker.track("tool_stuck", tool_args={"file": "A"})

    assert tracker.repeat_count == 5

    # Next call triggers error
    with pytest.raises(AnomalyDetectedError) as exc:
        tracker.track("tool_stuck", tool_args={"file": "A"})

    assert "detected: tool_stuck called 6 times" in str(exc.value)

@pytest.mark.unit
def test_anomaly_detection_batch_processing(tmp_path):
    """Test that same tool with DIFFERENT args is allowed (Batch Processing)."""
    tracker = UsageTracker(persistence_path=tmp_path / "usage.json")
    tracker.ANOMALY_THRESHOLD = 5

    # Batch process 20 files
    for i in range(20):
        tracker.track("read_file", tool_args={"file": f"file_{i}.txt"})

    # Should NOT raise error because args changed
    assert tracker.repeat_count == 1
    assert tracker.stats.tools["read_file"].count == 20
