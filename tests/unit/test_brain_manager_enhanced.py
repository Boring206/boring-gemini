
from datetime import datetime, timedelta
from unittest.mock import patch

from boring.intelligence.brain_manager import BrainManager, GlobalKnowledgeStore, LearnedPattern


class TestBrainManagerEnhanced:
    """Enhanced tests for BrainManager (V10.23+ features)."""

    def test_incremental_learn(self, tmp_path):
        brain = BrainManager(tmp_path)
        print(f"DEBUG: BrainManager methods: {[m for m in dir(brain) if not m.startswith('_')]}")

        # Test basic incremental learning
        result = brain.incremental_learn(
            error_type="python_error",
            error_message="KeyError: 'user'",
            solution="Ensure user key exists in dictionary.",
            file_path="src/auth.py"
        )
        assert result["status"] == "SUCCESS"

        patterns = brain._load_patterns()
        assert len(patterns) == 1
        assert patterns[0]["pattern_type"] == "error_solution"

    def test_pattern_relevance_decay(self, tmp_path):
        brain = BrainManager(tmp_path)

        # Create an old pattern
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        pattern = LearnedPattern(
            pattern_id="OLD_1",
            pattern_type="code_fix",
            description="Old pattern",
            context="old context",
            solution="old fix",
            success_count=1,
            created_at=old_date,
            last_used=old_date,
            decay_score=1.0
        )
        import dataclasses
        brain._save_patterns([dataclasses.asdict(pattern)])

        # Update decay
        result = brain.update_pattern_decay()
        assert result["updated"] == 1

        # Reload and check score
        patterns = brain._load_patterns()
        assert patterns[0]["decay_score"] < 1.0

    def test_prune_patterns(self, tmp_path):
        brain = BrainManager(tmp_path)

        # Add a low-score pattern
        pattern = {
            "pattern_id": "LOW_1",
            "pattern_type": "temp",
            "description": "desc",
            "context": "ctx",
            "solution": "sol",
            "success_count": 0,
            "decay_score": 0.05,  # Below default 0.1 threshold
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat()
        }
        brain._save_patterns([pattern])

        result = brain.prune_patterns(min_score=0.1)
        assert result["pruned_count"] == 1
        assert len(brain._load_patterns()) == 0

    def test_get_pattern_stats(self, tmp_path):
        brain = BrainManager(tmp_path)
        brain.learn_pattern("code_style", "Indent 4", "ctx", "sol")
        brain.learn_pattern("error_solution", "Fix bug", "ctx2", "sol2")

        stats = brain.get_pattern_stats()
        assert stats["total"] == 2
        assert stats["by_type"]["code_style"] == 1
        assert stats["by_type"]["error_solution"] == 1

    def test_global_knowledge_store_empty(self, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            store = GlobalKnowledgeStore()
            assert store.list_global_patterns() == []

            # Export from project
            brain = BrainManager(tmp_path / "proj")
            brain.learn_pattern("test", "desc", "ctx", "sol")
            # Set success count to 2 to pass default threshold
            patterns = brain._load_patterns()
            patterns[0]["success_count"] = 5
            brain._save_patterns(patterns)

            result = store.export_from_project(tmp_path / "proj", min_success_count=2)
            assert result["exported"] == 1

            # Import to another project
            result_import = store.import_to_project(tmp_path / "proj2")
            assert result_import["imported"] == 1

    def test_brain_health_report(self, tmp_path):
        brain = BrainManager(tmp_path)
        brain.learn_pattern("error", "desc", "ctx", "sol")

        report = brain.get_brain_health_report()
        assert report["total_patterns"] == 1
        assert "health_status" in report

    def test_intelligent_pattern_match_no_words(self, tmp_path):
        brain = BrainManager(tmp_path)
        brain.learn_pattern("test", "desc", "ctx", "sol")

        # Test with empty context
        results = brain.get_relevant_patterns("")
        assert len(results) == 1
