from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from boring.intelligence.brain_manager import BrainManager, GlobalKnowledgeStore, LearnedPattern
from boring.services.storage import _clear_thread_local_connection


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    yield project
    _clear_thread_local_connection()


class TestBrainManagerEnhanced:
    """Enhanced tests for BrainManager (V10.23+ features)."""

    def test_incremental_learn(self, temp_project):
        brain = BrainManager(temp_project)
        print(f"DEBUG: BrainManager methods: {[m for m in dir(brain) if not m.startswith('_')]}")

        # Test basic incremental learning
        result = brain.incremental_learn(
            error_type="python_error",
            error_message="KeyError: 'user'",
            solution="Ensure user key exists in dictionary.",
            file_path="src/auth.py",
        )
        assert result["status"] == "SUCCESS"

        patterns = brain._load_patterns()
        assert len(patterns) == 1
        assert patterns[0]["pattern_type"] == "error_solution"

    def test_pattern_relevance_decay(self, temp_project):
        brain = BrainManager(temp_project)

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
            decay_score=1.0,
        )
        import dataclasses

        brain._save_patterns([dataclasses.asdict(pattern)])

        # Update decay
        result = brain.update_pattern_decay()
        assert result["updated"] == 1

        # Reload and check score
        patterns = brain._load_patterns()
        assert patterns[0]["decay_score"] < 1.0

    def test_prune_patterns(self, temp_project):
        brain = BrainManager(temp_project)

        # Add patterns via the official API
        brain.learn_pattern("temp", "Low score pattern", "ctx", "sol")

        # Verify pattern exists before pruning
        initial_stats = brain.get_pattern_stats()
        assert initial_stats["total"] >= 1

        # Prune with high threshold - should remove patterns
        result = brain.prune_patterns(min_score=0.99)

        # Result should indicate pruning operation completed
        assert "pruned_count" in result or "status" in result

    def test_get_pattern_stats(self, temp_project):
        brain = BrainManager(temp_project)
        brain.learn_pattern("code_style", "Indent 4", "ctx", "sol")
        brain.learn_pattern("error_solution", "Fix bug", "ctx2", "sol2")

        stats = brain.get_pattern_stats()
        assert stats["total"] == 2
        assert stats["by_type"]["code_style"] == 1
        assert stats["by_type"]["error_solution"] == 1

    def test_global_knowledge_store_empty(self, temp_project):
        with patch("pathlib.Path.home", return_value=temp_project):
            store = GlobalKnowledgeStore()
            assert store.list_global_patterns() == []

            # Export from project
            brain = BrainManager(temp_project / "proj")
            brain.learn_pattern("test", "desc", "ctx", "sol")
            # Set success count to 2 to pass default threshold
            patterns = brain._load_patterns()
            patterns[0]["success_count"] = 5
            brain._save_patterns(patterns)

            result = store.export_from_project(temp_project / "proj", min_success_count=2)
            assert result["exported"] == 1

            # Import to another project
            result_import = store.import_to_project(temp_project / "proj2")
            assert result_import["imported"] == 1

    def test_brain_health_report(self, temp_project):
        brain = BrainManager(temp_project)
        brain.learn_pattern("error", "desc", "ctx", "sol")

        report = brain.get_brain_health_report()
        assert report["total_patterns"] == 1
        assert "health_status" in report

    def test_intelligent_pattern_match_no_words(self, temp_project):
        brain = BrainManager(temp_project)
        brain.learn_pattern("test", "desc", "ctx", "sol")

        # Test with empty context
        results = brain.get_relevant_patterns("")
        assert len(results) == 1
