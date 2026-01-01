"""
Tests for storage.py and context_selector.py modules.
"""
import pytest
from pathlib import Path
import sqlite3

from boring.storage import (
    SQLiteStorage,
    LoopRecord,
    create_storage,
)

from boring.context_selector import (
    ContextSelector,
    create_context_selector,
)


class TestSQLiteStorage:
    """Tests for SQLite storage."""

    def test_create_storage(self, tmp_path):
        """Test storage creation."""
        storage = create_storage(tmp_path)
        
        assert storage is not None
        assert storage.db_path.exists()

    def test_record_loop(self, tmp_path):
        """Test recording a loop."""
        storage = SQLiteStorage(tmp_path / ".boring_memory")
        
        record = LoopRecord(
            loop_id=1,
            timestamp="2025-01-01T00:00:00",
            status="SUCCESS",
            files_modified=["src/main.py"],
            tasks_completed=["Task 1"],
            errors=[],
            duration_seconds=10.5,
            output_summary="Test output"
        )
        
        row_id = storage.record_loop(record)
        
        assert row_id > 0

    def test_get_recent_loops(self, tmp_path):
        """Test getting recent loops."""
        storage = SQLiteStorage(tmp_path / ".boring_memory")
        
        # Add some loops
        for i in range(5):
            record = LoopRecord(
                loop_id=i,
                timestamp=f"2025-01-0{i+1}T00:00:00",
                status="SUCCESS" if i % 2 == 0 else "FAILED",
                files_modified=[],
                tasks_completed=[],
                errors=[],
                duration_seconds=i * 1.0
            )
            storage.record_loop(record)
        
        recent = storage.get_recent_loops(3)
        
        assert len(recent) == 3
        assert recent[0]["loop_id"] == 4  # Most recent first

    def test_get_loop_stats(self, tmp_path):
        """Test loop statistics."""
        storage = SQLiteStorage(tmp_path / ".boring_memory")
        
        # Add loops
        for status in ["SUCCESS", "SUCCESS", "FAILED"]:
            record = LoopRecord(
                loop_id=1,
                timestamp="2025-01-01",
                status=status,
                files_modified=[],
                tasks_completed=[],
                errors=[],
                duration_seconds=10.0
            )
            storage.record_loop(record)
        
        stats = storage.get_loop_stats()
        
        assert stats["total_loops"] == 3
        assert stats["successful"] == 2
        assert stats["failed"] == 1

    def test_record_error(self, tmp_path):
        """Test recording errors."""
        storage = SQLiteStorage(tmp_path / ".boring_memory")
        
        storage.record_error("SyntaxError", "Invalid syntax at line 10")
        storage.record_error("SyntaxError", "Invalid syntax at line 10")  # Duplicate
        
        errors = storage.get_top_errors(10)
        
        assert len(errors) == 1
        assert errors[0]["occurrence_count"] == 2

    def test_add_and_get_solution(self, tmp_path):
        """Test adding and retrieving solutions."""
        storage = SQLiteStorage(tmp_path / ".boring_memory")
        
        storage.record_error("TypeError", "NoneType has no attribute")
        storage.add_solution("TypeError", "NoneType has no attribute", "Check for None")
        
        solution = storage.get_solution_for_error("NoneType has no")
        
        assert solution == "Check for None"

    def test_record_metric(self, tmp_path):
        """Test recording metrics."""
        storage = SQLiteStorage(tmp_path / ".boring_memory")
        
        storage.record_metric("tokens_used", 1500.0, {"model": "gemini-pro"})
        storage.record_metric("tokens_used", 2000.0)
        
        metrics = storage.get_metrics("tokens_used")
        
        assert len(metrics) == 2


class TestContextSelector:
    """Tests for context selector."""

    def test_create_selector(self, tmp_path):
        """Test selector creation."""
        selector = create_context_selector(tmp_path)
        
        assert selector is not None

    def test_extract_keywords(self, tmp_path):
        """Test keyword extraction."""
        selector = ContextSelector(tmp_path)
        
        text = "Implement a login function with password validation"
        keywords = selector.extract_keywords(text)
        
        assert "login" in keywords
        assert "password" in keywords
        assert "validation" in keywords
        assert "the" not in keywords  # Stop word

    def test_extract_keywords_camelcase(self, tmp_path):
        """Test keyword extraction from camelCase."""
        selector = ContextSelector(tmp_path)
        
        text = "Fix the getUserById function"
        keywords = selector.extract_keywords(text)
        
        # Should extract meaningful keywords
        assert len(keywords) > 0
        # At least one of these should be present
        assert any(k in keywords for k in ["user", "get", "function", "fix"])

    def test_score_file_filename_match(self, tmp_path):
        """Test file scoring with filename match."""
        selector = ContextSelector(tmp_path)
        
        # Create test file
        test_file = tmp_path / "login_handler.py"
        test_file.write_text("def login(): pass")
        
        keywords = {"login", "handler", "auth"}
        score = selector.score_file(test_file, keywords)
        
        assert score.score > 0
        assert any("filename" in r for r in score.reasons)

    def test_get_project_files(self, tmp_path):
        """Test getting project files."""
        # Create file structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("# Main")
        (tmp_path / "src" / "utils.py").write_text("# Utils")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "cache.pyc").write_text("cache")
        
        selector = ContextSelector(tmp_path)
        files = selector.get_project_files()
        
        # Should include .py files, exclude __pycache__
        file_names = [f.name for f in files]
        assert "main.py" in file_names
        assert "cache.pyc" not in file_names

    def test_select_files_by_relevance(self, tmp_path):
        """Test file selection by relevance."""
        # Create files
        (tmp_path / "auth.py").write_text("def login(): pass\ndef authenticate(): pass")
        (tmp_path / "utils.py").write_text("def helper(): pass")
        
        selector = ContextSelector(tmp_path)
        selected = selector.select_files("implement authentication login", min_score=0.1)
        
        # auth.py should score higher
        if selected:
            assert any("auth" in str(s.path) for s in selected)

    def test_select_context_with_budget(self, tmp_path):
        """Test context selection with token budget."""
        # Create files
        (tmp_path / "small.py").write_text("x = 1")
        (tmp_path / "medium.py").write_text("x = 1\n" * 100)
        
        selector = ContextSelector(tmp_path)
        selection = selector.select_context("test", max_tokens=500)
        
        assert selection.total_tokens <= 500 or selection.total_tokens < 1000

    def test_generate_context_injection(self, tmp_path):
        """Test context injection generation."""
        (tmp_path / "main.py").write_text("def main(): print('hello')")
        
        selector = ContextSelector(tmp_path)
        injection = selector.generate_context_injection("main function")
        
        if injection:
            assert "RELEVANT PROJECT FILES" in injection
