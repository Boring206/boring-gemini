
from unittest.mock import MagicMock, patch

import pytest

from boring.intelligence.usage_tracker import UsageTracker
from boring.mcp.tool_profiles import LITE_TOOLS, get_profile


@pytest.fixture
def temp_usage_file(tmp_path):
    return tmp_path / "usage.json"

@pytest.mark.unit
def test_usage_tracking_and_persistence(temp_usage_file):
    """Test tracking saves to file correctly."""
    tracker = UsageTracker(persistence_path=temp_usage_file)

    # Track some tools
    tracker.track("tool_a")
    tracker.track("tool_a")
    tracker.track("tool_b")

    # Verify stats in memory
    assert tracker.stats.tools["tool_a"].count == 2
    assert tracker.stats.tools["tool_b"].count == 1

    # Flush before persistence check (debounced writes defer actual I/O)
    tracker.flush()

    # Verify persistence
    tracker2 = UsageTracker(persistence_path=temp_usage_file)
    assert tracker2.stats.tools["tool_a"].count == 2

def test_get_top_tools(temp_usage_file):
    tracker = UsageTracker(persistence_path=temp_usage_file)
    tracker.track("tool_a")
    tracker.track("tool_a")
    tracker.track("tool_b")
    tracker.track("tool_c")

    top = tracker.get_top_tools(limit=2)
    assert top == ["tool_a", "tool_b"] # c is 1 count, b is 1, a is 2. Sort might vary for equal, but likely insertion order or stable.

@pytest.fixture
def mock_tracker_module():
    with patch("boring.mcp.tool_profiles.get_tracker") as mock: # Patch where it's USED
        # Actually it's imported inside the function, so we need to patch boring.intelligence.usage_tracker.get_tracker?
        # No, in tool_profiles.py it does: from ..intelligence.usage_tracker import get_tracker
        # So it's a local import. Patching sys.modules or similar is needed?
        # Or patch where it's defined: boring.intelligence.usage_tracker.get_tracker
        yield mock

@pytest.mark.unit
def test_adaptive_profile_generation():
    """Test generating an adaptive profile."""
    # We need to patch the usage tracker used by tool_profiles
    # Since it does a local import `from ..intelligence.usage_tracker import get_tracker`
    # We should patch the source function

    with patch("boring.intelligence.usage_tracker.get_tracker") as mock_get:
        mock_tracker = MagicMock()
        mock_tracker.get_top_tools.return_value = ["my_custom_tool", "boring_test_gen"]
        mock_get.return_value = mock_tracker

        # Call get_profile with adaptive
        profile = get_profile("adaptive")

        assert profile.name == "adaptive"
        # Must include LITE tools
        assert set(LITE_TOOLS).issubset(set(profile.tools))
        # Must include usage tools
        assert "my_custom_tool" in profile.tools
        assert "boring_test_gen" in profile.tools

@pytest.mark.unit
def test_adaptive_fallback():
    """Test fallback if tracker fails."""
    with patch("boring.intelligence.usage_tracker.get_tracker") as mock_get:
        mock_get.side_effect = Exception("Tracker broken")

        profile = get_profile("adaptive")

        # Should fallback to LITE (but name might be adaptive? No, implementation returns adaptive config with just lite tools)
        assert profile.name == "adaptive"
        assert len(profile.tools) == len(set(LITE_TOOLS))
