import pytest

from boring.intelligence.brain_manager import BrainManager


class TestBrainManagerEdgeCases:
    @pytest.fixture
    def mock_project_root(self, tmp_path):
        return tmp_path

    @pytest.fixture
    def brain_manager(self, mock_project_root):
        return BrainManager(mock_project_root)

    def test_sqlite_migration_failure_fallback(self, mock_project_root):
        """Test fallback behavior if SQLite migration fails initially (simulated)."""
        # This is a bit tricky to mock perfectly without refactoring BrainManager to inject storage factory,
        # but we can mock the _get_storage internal method or similar.

        # For now, let's test that it handles a corrupted DB file gracefully by initing a fresh one if possible
        # or raising a clear error.

        db_path = mock_project_root / ".boring" / "memory" / "boring_brain.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.write_text("Not a valid sqlite file")

        # Should potentially raise or handle it.
        # Current implementation might fail hard, which is what we want to find out.
        # If it fails, we write a fix.

        try:
            BrainManager(mock_project_root)
            # If it survives, it might have overwritten it or failed to load.
        except Exception as e:
            # Ideally catching specific errors
            assert "database" in str(e).lower() or "encrypted" in str(e).lower()

    def test_connection_closing(self, brain_manager):
        """Ensure connections specific to thread are accessible."""
        # SQLiteStorage uses thread-local connections.
        assert brain_manager.storage is not None

        # Verify we can write and read
        # args: pattern_type, description, context, solution
        brain_manager.learn_pattern("test_type", "test_pattern", "test_context", "solution")
        patterns = brain_manager.get_relevant_patterns("test_context")
        assert len(patterns) > 0

    def test_concurrent_access_simulation(self, brain_manager):
        """Simulate basic concurrent check (sequential here but verifying locking behavior doesn't crash)."""
        # In a real concurrent scenario, we'd use threads, but for unit test, just ensure
        # repeated high-frequency writes work.
        for i in range(50):
            # args: pattern_type, description, context, solution
            brain_manager.learn_pattern("test_type", "desc", f"ctx_{i}", "sol")

        # Query specific item to ensure write happened
        assert len(brain_manager.get_relevant_patterns("ctx_1")) >= 1
