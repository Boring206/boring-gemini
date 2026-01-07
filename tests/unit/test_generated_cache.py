# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.cache module.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from boring.cache import VerificationCache
from boring.models import VerificationResult

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.fixture
def cache(temp_project):
    """Create a VerificationCache instance."""
    with patch("boring.cache.settings") as mock_settings:
        mock_settings.PROJECT_ROOT = temp_project
        mock_settings.CACHE_DIR = temp_project / ".cache"
        return VerificationCache(temp_project)


# =============================================================================
# VERIFICATION CACHE TESTS
# =============================================================================


class TestVerificationCache:
    """Tests for VerificationCache class."""

    def test_cache_init(self, temp_project):
        """Test VerificationCache initialization."""
        with patch("boring.cache.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.CACHE_DIR = temp_project / ".cache"
            cache = VerificationCache(temp_project)
            assert cache.project_root == temp_project
            assert isinstance(cache.cache, dict)

    def test_cache_init_default_root(self):
        """Test VerificationCache with default project root."""
        with patch("boring.cache.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = Path("/default")
            mock_settings.CACHE_DIR = Path("/default/.cache")
            cache = VerificationCache()
            assert cache.project_root == Path("/default")

    def test_cache_file_hash(self, cache, temp_project):
        """Test _file_hash method."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        hash1 = cache._file_hash(test_file)
        assert isinstance(hash1, str)
        assert len(hash1) > 0

        # Same content should produce same hash
        hash2 = cache._file_hash(test_file)
        assert hash1 == hash2

    def test_cache_file_hash_nonexistent(self, cache):
        """Test _file_hash with nonexistent file."""
        nonexistent = Path("/nonexistent/file.py")
        hash_val = cache._file_hash(nonexistent)
        assert hash_val == ""

    def test_cache_file_hash_error(self, cache, temp_project):
        """Test _file_hash error handling."""
        test_file = temp_project / "test.py"
        test_file.write_text("test")

        with patch.object(Path, "read_bytes", side_effect=PermissionError("Access denied")):
            hash_val = cache._file_hash(test_file)
            assert hash_val == ""

    def test_cache_get_rel_path(self, cache, temp_project):
        """Test _get_rel_path method."""
        test_file = temp_project / "src" / "test.py"
        test_file.parent.mkdir()
        test_file.write_text("test")

        rel_path = cache._get_rel_path(test_file)
        assert "test.py" in rel_path

    def test_cache_get_rel_path_outside_root(self, cache):
        """Test _get_rel_path with file outside project root."""
        outside_file = Path("/outside/file.py")
        rel_path = cache._get_rel_path(outside_file)
        assert rel_path == str(outside_file)

    def test_cache_get_not_cached(self, cache, temp_project):
        """Test get with no cached entry."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        result = cache.get(test_file)
        assert result is None

    def test_cache_get_cached_match(self, cache, temp_project):
        """Test get with matching cache entry."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        # Set cache entry
        result = VerificationResult(
            passed=True, check_type="syntax", message="OK", details=[], suggestions=[]
        )
        cache.set(test_file, result)

        # Get should return cached result
        cached = cache.get(test_file)
        assert cached is not None
        assert cached.passed is True

    def test_cache_get_cached_mismatch(self, cache, temp_project):
        """Test get with hash mismatch."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        # Set cache entry
        result = VerificationResult(
            passed=True, check_type="syntax", message="OK", details=[], suggestions=[]
        )
        cache.set(test_file, result)

        # Modify file
        test_file.write_text("print('modified')")

        # Get should return None (hash mismatch)
        cached = cache.get(test_file)
        assert cached is None

    def test_cache_set(self, cache, temp_project):
        """Test set method."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        result = VerificationResult(
            passed=True, check_type="syntax", message="OK", details=[], suggestions=[]
        )
        cache.set(test_file, result)

        # Verify cache was saved
        assert cache.cache_path.exists() or len(cache.cache) > 0

    def test_cache_bulk_update(self, cache, temp_project):
        """Test bulk_update method."""
        files = []
        for i in range(3):
            test_file = temp_project / f"test{i}.py"
            test_file.write_text(f"print('test{i}')")
            files.append(test_file)

        updates = {
            file: VerificationResult(
                passed=True, check_type="syntax", message="OK", details=[], suggestions=[]
            )
            for file in files
        }

        cache.bulk_update(updates)
        assert len(cache.cache) == 3

    def test_cache_bulk_update_empty(self, cache):
        """Test bulk_update with empty dict."""
        cache.bulk_update({})
        # Should not raise exception

    def test_cache_load_nonexistent(self, temp_project):
        """Test _load when cache file doesn't exist."""
        with patch("boring.cache.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.CACHE_DIR = temp_project / ".cache"
            cache = VerificationCache(temp_project)
            assert cache.cache == {}

    def test_cache_load_existing(self, temp_project):
        """Test _load with existing cache file."""
        cache_dir = temp_project / ".cache"
        cache_dir.mkdir()
        cache_file = cache_dir / "verification.json"
        cache_file.write_text('{"test.py": {"hash": "abc123", "result": {"passed": true}}}')

        with patch("boring.cache.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.CACHE_DIR = cache_dir
            cache = VerificationCache(temp_project)
            assert "test.py" in cache.cache

    def test_cache_load_invalid_json(self, temp_project):
        """Test _load with invalid JSON."""
        cache_dir = temp_project / ".cache"
        cache_dir.mkdir()
        cache_file = cache_dir / "verification.json"
        cache_file.write_text("invalid json{")

        with patch("boring.cache.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.CACHE_DIR = cache_dir
            cache = VerificationCache(temp_project)
            # Should handle gracefully
            assert cache.cache == {}

    def test_cache_save(self, cache, temp_project):
        """Test _save method."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        result = VerificationResult(
            passed=True, check_type="syntax", message="OK", details=[], suggestions=[]
        )
        cache.set(test_file, result)

        # Verify file was created
        assert cache.cache_path.exists() or len(cache.cache) > 0

    def test_cache_save_error(self, cache, temp_project):
        """Test _save error handling."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        VerificationResult(
            passed=True, check_type="syntax", message="OK", details=[], suggestions=[]
        )
        cache.cache["test.py"] = {"hash": "abc", "result": {"passed": True}}

        with patch.object(Path, "write_text", side_effect=OSError("Write error")):
            cache._save()
            # Should handle gracefully
