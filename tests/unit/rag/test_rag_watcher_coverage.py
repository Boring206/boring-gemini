import time
from unittest.mock import MagicMock, patch

import pytest

from boring.rag.rag_watcher import RAGWatcher, get_rag_watcher, start_rag_watch, stop_rag_watch


class TestRAGWatcher:
    @pytest.fixture
    def mock_thread(self):
        with patch("threading.Thread") as mock:
            yield mock

    def test_init(self, tmp_path):
        watcher = RAGWatcher(tmp_path)
        assert not watcher.is_running
        assert watcher.project_root == tmp_path

    def test_should_watch(self, tmp_path):
        watcher = RAGWatcher(tmp_path)

        # Valid extensions
        assert watcher._should_watch(tmp_path / "test.py")
        assert watcher._should_watch(tmp_path / "doc.md")

        # Invalid extensions
        assert not watcher._should_watch(tmp_path / "test.pyc")
        assert not watcher._should_watch(tmp_path / "image.png")

        # Ignored dirs
        assert not watcher._should_watch(tmp_path / "node_modules" / "file.js")
        assert not watcher._should_watch(tmp_path / ".git" / "config")

    def test_start_stop(self, tmp_path, mock_thread):
        watcher = RAGWatcher(tmp_path)

        # Start
        assert watcher.start() is True
        assert watcher.is_running
        mock_thread.return_value.start.assert_called_once()

        # Start again should fail
        assert watcher.start() is False

        # Stop
        assert watcher.stop() is True
        assert not watcher.is_running

        # Stop again should fail
        assert watcher.stop() is False

    def test_detect_changes(self, tmp_path):
        watcher = RAGWatcher(tmp_path)

        # Initial state
        current = {"file1.py": 100.0, "file2.py": 100.0}
        watcher._file_mtimes = current

        # No change
        assert not watcher._detect_changes(current)

        # Modified
        modified = {"file1.py": 101.0, "file2.py": 100.0}
        diff = watcher._detect_changes(modified)
        assert "file1.py" in diff

        # New
        new_files = {"file1.py": 101.0, "file2.py": 100.0, "new.py": 100.0}
        diff = watcher._detect_changes(new_files)
        assert "new.py" in diff

        # Deleted
        deleted = {"file2.py": 100.0}  # file1 and new gone
        # Note: input to detect_changes is compared AGAINST self._file_mtimes
        # So if I pass 'deleted' which lacks file1, it should detect file1 as deleted

        # Reset state to 'current'
        watcher._file_mtimes = current
        diff = watcher._detect_changes(deleted)
        # file1.py is in _file_mtimes but not in deleted -> changed (deleted)
        assert "file1.py" in diff

    def test_trigger_debounced(self, tmp_path):
        # We need to simulate the loop logic somewhat or test the trigger directly
        watcher = RAGWatcher(tmp_path, debounce_seconds=0.1)
        watcher._on_change_callback = MagicMock()

        watcher._pending_reindex = True
        watcher._last_change_time = time.time() - 0.2  # Past debounce window

        # Manually invoke the check logic that would run in loop
        if watcher._pending_reindex and (
            time.time() - watcher._last_change_time >= watcher.debounce_seconds
        ):
            watcher._trigger_reindex()
            watcher._pending_reindex = False

        watcher._on_change_callback.assert_called_once()
        assert watcher._pending_reindex is False

    def test_singleton(self, tmp_path):
        w1 = get_rag_watcher(tmp_path)
        w2 = get_rag_watcher(tmp_path)
        assert w1 is w2

        w3 = get_rag_watcher(tmp_path / "sub")
        assert w1 is not w3

    def test_start_helper(self, tmp_path, mock_thread):
        res = start_rag_watch(tmp_path)
        assert res["status"] == "STARTED"

        res2 = start_rag_watch(tmp_path)
        assert res2["status"] == "ALREADY_RUNNING"

        with patch("boring.rag.rag_watcher.RAGWatcher.stop", return_value=True):
            res_stop = stop_rag_watch(tmp_path)
            assert res_stop["status"] == "STOPPED"
