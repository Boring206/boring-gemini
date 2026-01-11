
from dataclasses import asdict
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from boring.intelligence.brain_manager import (
    BrainManager,
    GlobalKnowledgeStore,
    LearnedPattern,
    Rubric,
)


class TestBrainManagerCoverage:
    def test_rubric_instantiation(self):
        r = Rubric(
            name="test",
            description="desc",
            criteria=[],
            created_at="2026-01-11"
        )
        assert r.name == "test"

    def test_brain_manager_init_paths(self, tmp_path):
        brain = BrainManager(tmp_path)
        assert brain.project_root == tmp_path
        assert brain.brain_dir.exists()
        assert brain.patterns_dir.exists()

    def test_get_brain_summary(self, tmp_path):
        brain = BrainManager(tmp_path)
        brain.learn_pattern("test", "desc", "ctx", "sol")
        (brain.rubrics_dir / "test_rubric.json").write_text("{}")
        (brain.adaptations_dir / "test_adapt.json").write_text("{}")

        summary = brain.get_brain_summary()
        assert summary["patterns_count"] == 1
        assert "test_rubric" in summary["rubrics"]
        assert "test_adapt" in summary["adaptations"]

    def test_learn_from_memory_success(self, tmp_path):
        brain = BrainManager(tmp_path)
        mock_storage = MagicMock()
        mock_storage.get_recent_loops.return_value = [{"status": "SUCCESS"}]
        mock_storage.get_top_errors.return_value = [
            {"error_type": "ValueError", "error_message": "msg", "solution": "fix", "occurrence_count": 5}
        ]

        result = brain.learn_from_memory(mock_storage)
        assert result["status"] == "SUCCESS"
        assert result["new_patterns"] == 1

        # Test update existing
        result2 = brain.learn_from_memory(mock_storage)
        assert result2["new_patterns"] == 0
        assert result2["total_patterns"] == 1

    def test_learn_from_memory_exception(self, tmp_path):
        brain = BrainManager(tmp_path)
        mock_storage = MagicMock()
        mock_storage.get_recent_loops.side_effect = Exception("DB Error")
        result = brain.learn_from_memory(mock_storage)
        assert result["status"] == "ERROR"

    def test_brain_manager_incremental_learn(self, tmp_path):
        brain = BrainManager(tmp_path)
        res1 = brain.incremental_learn("Err", "msg", "sol1")
        assert res1["status"] == "SUCCESS"

        # Update with better solution
        res2 = brain.incremental_learn("Err", "msg", "solution_longer_than_sol1")
        assert res2["status"] == "UPDATED"

        patterns = brain._load_patterns()
        assert patterns[0]["solution"] == "solution_longer_than_sol1"

    def test_rubric_management(self, tmp_path):
        brain = BrainManager(tmp_path)
        brain.create_rubric("test_r", "desc", [{"name": "c1", "weight": 10}])
        assert brain.get_rubric("test_r")["name"] == "test_r"
        assert brain.get_rubric("non_existent") is None

    def test_create_default_rubrics(self, tmp_path):
        brain = BrainManager(tmp_path)
        res = brain.create_default_rubrics()
        assert res["status"] == "SUCCESS"
        assert "implementation_plan" in res["rubrics_created"]

    def test_intelligent_pattern_match_tf_idf(self, tmp_path):
        brain = BrainManager(tmp_path)
        patterns = [
            {"context": "apple banana", "description": "fruits", "solution": "eat"},
            {"context": "carrot potato", "description": "veggies", "solution": "cook"}
        ]
        results = brain._intelligent_pattern_match("apple", patterns, limit=5)
        assert results[0]["context"] == "apple banana"

        # Test exception fallback
        with patch("collections.Counter", side_effect=Exception("TF Error")):
            fallback = brain._intelligent_pattern_match("apple", patterns, limit=5)
            assert fallback[0]["context"] == "apple banana"

    def test_intelligent_pattern_match_fallback(self, tmp_path):
        """Test fallback logic in intelligent matching by forcing exception."""
        brain_manager = BrainManager(tmp_path)
        patterns = [
            {"context": "foo bar", "description": "some foo", "solution": "fix", "success_count": 5}
        ]

        # Mocking math to raise Exception to trigger fallback block
        with patch("math.sqrt", side_effect=Exception("Trigger Fallback")):
            # Fallback checks:
            # 1. context in p['context']
            # 2. p['context'] in context (if len > 5)
            # 3. context in p['description']

            # Case A: context in p['context']
            res = brain_manager._intelligent_pattern_match("foo", patterns, 5)
            assert len(res) == 1

            # Case B: p['context'] in context (if len > 5)
            patterns[0]["context"] = "longer_context"
            res = brain_manager._intelligent_pattern_match("contains longer_context here", patterns, 5)
            assert len(res) == 1

    def test_update_pattern_decay_edge_cases(self, tmp_path):
        """Test decay with invalid dates and no-ops."""
        brain_manager = BrainManager(tmp_path)
        # 1. Invalid date format
        patterns = [
            {"id": "p1", "last_used": "invalid-date", "decay_score": 1.0},
            {"id": "p2", "last_used": None, "decay_score": 1.0},
            {"id": "p3", "last_used": datetime.now().isoformat(), "decay_score": 1.0}
        ]

        with patch.object(brain_manager, '_load_patterns', return_value=patterns):
            with patch.object(brain_manager, '_save_patterns') as mock_save:
                res = brain_manager.update_pattern_decay()
                # Should handle invalid date gracefully (continue)
                # Should skip None
                # Should not update if 0 days passed (p3)

                assert res["updated"] == 0
                mock_save.assert_not_called()

    def test_prune_patterns_keep_min(self, tmp_path):
        """Test prune logic respecting keep_min."""
        brain_manager = BrainManager(tmp_path)
        patterns = []
        for i in range(10):
            patterns.append({"id": f"p{i}", "success_count": 0, "decay_score": 0.01}) # Low score

        with patch.object(brain_manager, '_load_patterns', return_value=patterns):
            with patch.object(brain_manager, '_save_patterns'):
                # Max 5, but keep_min 10 -> keep all?
                # Logic: if i < keep_min: keep.

                res = brain_manager.prune_patterns(min_score=0.9, keep_min=10)
                assert res["remaining"] == 10
                assert res["pruned_count"] == 0

                # Verify keep_min priority
                res = brain_manager.prune_patterns(min_score=0.9, keep_min=5)
                # First 5 kept by index (keep_min), rest checked against min_score (fail)
                assert res["remaining"] == 5
                assert res["pruned_count"] == 5

    def test_global_knowledge_store_decay(self, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            store = GlobalKnowledgeStore()
            # Add old pattern
            old_date = (datetime.now() - timedelta(days=60)).isoformat()
            pattern = LearnedPattern(
                pattern_id="OLD_1",
                pattern_type="fix",
                description="desc",
                context="ctx",
                solution="sol",
                last_used=old_date,
                created_at=old_date,
                success_count=1
            )
            store._save_global_patterns([asdict(pattern)])

            res = store.update_pattern_decay()
            assert res["updated"] == 1

            patterns = store._load_global_patterns()
            assert patterns[0]["decay_score"] < 1.0

    def test_global_knowledge_store_session_boost(self, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            store = GlobalKnowledgeStore()
            store.incremental_learn("GlobalErr", "special context", "fix")

            # Boost via keywords
            boosted = store.apply_session_boost(["special"])
            assert boosted == 1

            patterns = store._load_global_patterns()
            assert patterns[0]["session_boost"] > 0

            # Boost with no keywords
            assert store.apply_session_boost([]) == 0

            # Clear boosts
            cleared = store.clear_session_boosts()
            assert cleared == 1
            assert store._load_global_patterns()[0]["session_boost"] == 0

    def test_global_knowledge_store_prune_logic(self, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            store = GlobalKnowledgeStore()
            # Case: original <= keep_min
            res = store.prune_patterns(keep_min=100)
            assert res["status"] == "SKIPPED"

            # Add some patterns
            patterns = []
            for i in range(110):
                patterns.append({
                    "pattern_id": f"P{i}",
                    "decay_score": 0.1 if i > 100 else 1.0,
                    "success_count": 1,
                    "session_boost": 0.0
                })
            store._save_global_patterns(patterns)
            res2 = store.prune_patterns(keep_min=100)
            assert res2["status"] == "SUCCESS"
            # 110 total. 101 have high score, 9 have low score.
            # keep_min=100 -> top 100 kept.
            # Remaining 10: 1 high score (kept), 9 low score (removed).
            assert res2["removed"] == 9

    def test_global_knowledge_store_stats(self, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            store = GlobalKnowledgeStore()
            # Empty stats
            assert store.get_pattern_stats()["total"] == 0

            # Non-empty stats
            store.incremental_learn("A", "B", "C")
            stats = store.get_pattern_stats()
            assert stats["total"] == 1
            assert stats["avg_success"] == 1.0

    def test_brain_health_report_issues(self, tmp_path):
        brain = BrainManager(tmp_path)
        # 1. Empty brain
        report1 = brain.get_brain_health_report()
        assert "No patterns learned yet" in report1["issues"]

        # 2. Stale brain
        brain.learn_pattern("t", "d", "c", "s")
        patterns = brain._load_patterns()
        patterns[0]["decay_score"] = 0.1
        brain._save_patterns(patterns)
        report2 = brain.get_brain_health_report()
        assert "Stale patterns detected" in report2["issues"]

    def test_brain_manager_init_legacy_fallback(self, tmp_path):
        # Create legacy directory
        legacy_dir = tmp_path / ".boring_brain"
        legacy_dir.mkdir()

        with patch("boring.paths.get_boring_path", return_value=legacy_dir):
            brain = BrainManager(tmp_path)
            # Should have initialized in legacy_dir
            assert brain.brain_dir == legacy_dir
