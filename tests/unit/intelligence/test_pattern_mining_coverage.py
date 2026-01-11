
import json
from unittest.mock import patch

import pytest

from boring.intelligence.pattern_mining import (
    PatternMiner,
    clear_pattern_miner_cache,
    get_pattern_miner,
)


@pytest.fixture
def brain_dir(tmp_path):
    d = tmp_path / ".boring_brain"
    d.mkdir()
    (d / "learned_patterns").mkdir()
    return d

@pytest.fixture
def pattern_miner(brain_dir):
    clear_pattern_miner_cache()
    return PatternMiner(brain_dir)

class TestPatternMiner:

    def test_initialization(self, pattern_miner):
        # Should load default patterns if no custom ones
        assert len(pattern_miner.patterns) > 0
        assert any(p.id == "new_project" for p in pattern_miner.patterns)

    def test_load_custom_patterns(self, brain_dir):
        # Create a custom pattern file
        custom_pattern = {
            "id": "custom_01",
            "name": "Custom Pattern",
            "description": "A test pattern",
            "trigger_conditions": ["always"],
            "suggested_actions": ["do something"],
            "success_rate": 0.99,
            "usage_count": 10,
            "last_used": "2025-01-01T12:00:00"
        }

        p_file = brain_dir / "learned_patterns" / "p1.json"
        p_file.write_text(json.dumps(custom_pattern), encoding="utf-8")

        miner = PatternMiner(brain_dir)
        # Should have defaults + custom
        assert any(p.id == "custom_01" for p in miner.patterns)
        loaded = next(p for p in miner.patterns if p.id == "custom_01")
        assert loaded.success_rate == 0.99
        assert loaded.last_used.year == 2025

    def test_analyze_project_state_empty(self, pattern_miner, tmp_path):
        state = pattern_miner.analyze_project_state(tmp_path)
        assert state["has_code"] is False
        assert state["has_tests"] is False
        assert state["has_git"] is False
        assert state["code_count"] == 0

    def test_analyze_project_state_with_files(self, pattern_miner, tmp_path):
        # Create structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").touch()
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").touch()
        (tmp_path / "task.md").write_text("- [x] Task 1\n- [ ] Task 2")
        (tmp_path / ".git").mkdir()
        (tmp_path / "PRD.md").touch()

        state = pattern_miner.analyze_project_state(tmp_path)

        assert state["has_code"] is True
        assert state["code_count"] == 1
        assert state["has_tests"] is True
        assert state["has_git"] is True
        assert state["has_spec"] is True
        assert state["task_completion"] == 0.5

    def test_analyze_project_state_errors(self, pattern_miner, tmp_path):
        exit_signals = tmp_path / ".exit_signals"
        exit_signals.write_text('{"verification_failed": true}')

        state = pattern_miner.analyze_project_state(tmp_path)
        assert state["has_errors"] is True

    def test_caching(self, pattern_miner, tmp_path):
        # First call caches
        state1 = pattern_miner.analyze_project_state(tmp_path)

        # Modify system (should be ignored due to cache)
        (tmp_path / "new_file.py").touch()

        state2 = pattern_miner.analyze_project_state(tmp_path)
        assert state2["code_count"] == state1["code_count"]  # Assuming "new_file.py" isn't counted yet

        # Clear cache and retry
        clear_pattern_miner_cache(tmp_path)
        state3 = pattern_miner.analyze_project_state(tmp_path)
        # Note: analyze_impl looks for .py in root too, so now it should update
        # Depending on where the file is created, if it's in root, analyze_impl picks it up
        assert state3["code_count"] != state1["code_count"]

    def test_state_cache_ttl(self, pattern_miner, tmp_path):
        # We need to mock time.time in the module where it is used
        with patch("boring.intelligence.pattern_mining.time") as mock_time_mod:
            # First call: time is 1000
            mock_time_mod.time.return_value = 1000.0

            with patch.object(pattern_miner, '_analyze_project_state_impl', wraps=pattern_miner._analyze_project_state_impl) as mock_impl:
                pattern_miner.analyze_project_state(tmp_path)
                assert mock_impl.call_count == 1

                # Second call: time is 1000.05 (still valid, TTL is 0.1 in patch below?)
                # Wait, we need to patch the TTL constant in the module too

                with patch("boring.intelligence.pattern_mining._STATE_CACHE_TTL", 0.1):
                    # Immediate subsequent call - should use cache
                    mock_time_mod.time.return_value = 1000.05
                    pattern_miner.analyze_project_state(tmp_path)
                    assert mock_impl.call_count == 1  # Still 1

                    # Later call - should look up again
                    mock_time_mod.time.return_value = 1000.2
                    pattern_miner.analyze_project_state(tmp_path)
                    assert mock_impl.call_count == 2

    def test_match_patterns(self, pattern_miner, tmp_path):
        # Case 1: New Project
        state_new = {
            "has_code": False,
            "code_count": 0,
            "has_errors": False,
            "task_completion": 0.0,
            "has_spec": False
        }
        matches = pattern_miner.match_patterns(state_new)
        # "new_project" pattern checks for 'new' or 'empty' and !has_code
        assert any(p.id == "new_project" for p in matches)

        # Case 2: Failed Verification
        state_fail = {
            "has_code": True,
            "has_errors": True,
            "task_completion": 0.5
        }
        matches = pattern_miner.match_patterns(state_fail)
        assert any(p.id == "verification_failed" for p in matches)
        assert any(p.id == "stuck_debugging" for p in matches)

        # Case 3: Feature Complete
        state_done = {
            "has_code": True,
            "has_tests": True,
            "has_errors": False,
            "task_completion": 0.9
        }
        matches = pattern_miner.match_patterns(state_done)
        assert any(p.id == "feature_complete" for p in matches)

    def test_suggest_next(self, pattern_miner, tmp_path):
        # Setup empty project
        suggestions = pattern_miner.suggest_next(tmp_path, limit=1)

        assert len(suggestions) == 1
        assert suggestions[0]["pattern"] == "New Project Setup"
        assert "context" in suggestions[0]

    def test_suggest_next_fallback(self, pattern_miner, tmp_path):
        # Empty patterns list
        pattern_miner.patterns = []
        suggestions = pattern_miner.suggest_next(tmp_path)

        assert len(suggestions) == 1
        assert suggestions[0]["pattern"] == "Getting Started"

    def test_git_activity(self, pattern_miner, tmp_path):
        (tmp_path / ".git").mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "2 hours ago"

            state = pattern_miner.analyze_project_state(tmp_path)
            assert state["recent_activity"] == "2 hours ago"

    def test_get_pattern_miner_singleton(self, brain_dir):
        m1 = get_pattern_miner(brain_dir)
        m2 = get_pattern_miner(brain_dir)
        assert m1 is m2

        clear_pattern_miner_cache()
        m3 = get_pattern_miner(brain_dir)
        assert m3 is not m1
