import json

from boring.workspace import WorkspaceManager, get_workspace_manager


class TestWorkspaceStrict:
    """Strict testing for workspace.py uncovered lines."""

    def test_load_cache_hit(self, tmp_path):
        """Test cache hit in _load."""
        config_dir = tmp_path / ".boring"
        config_dir.mkdir()
        config_file = config_dir / "workspace.json"

        data = {"projects": {}, "active_project": None}
        config_file.write_text(json.dumps(data), encoding="utf-8")

        # First load to fill cache
        _ = WorkspaceManager(config_dir=config_dir)

        # Second load should hit cache
        manager2 = WorkspaceManager(config_dir=config_dir)
        assert manager2.projects == {}

    def test_load_exception_handling(self, tmp_path):
        """Test exception handling in _load (lines 113-115)."""
        config_dir = tmp_path / ".boring"
        config_dir.mkdir()
        config_file = config_dir / "workspace.json"

        # Write invalid JSON
        config_file.write_text("{invalid json", encoding="utf-8")

        manager = WorkspaceManager(config_dir=config_dir)
        assert manager.projects == {}
        assert manager.active_project is None

    def test_flush_dirty(self, tmp_path):
        """Test flush with dirty flag (line 142)."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir=config_dir)

        # Mocking debounce to allow save
        manager._last_save_time = 0

        manager._dirty = True
        manager.flush()
        assert manager._dirty is False

    def test_add_project_duplicate(self, tmp_path):
        """Test adding duplicate project (line 164)."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir=config_dir)

        p_path = tmp_path / "proj"
        p_path.mkdir()

        manager.add_project("p1", str(p_path))
        result = manager.add_project("p1", str(p_path))

        assert result["status"] == "ERROR"
        assert "already exists" in result["message"]

    def test_remove_project_not_found(self, tmp_path):
        """Test removing non-existent project (line 180)."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir=config_dir)

        result = manager.remove_project("nonexistent")
        assert result["status"] == "ERROR"
        assert "not found" in result["message"]

    def test_switch_project_not_found(self, tmp_path):
        """Test switching to non-existent project (line 194)."""
        config_dir = tmp_path / ".boring"
        manager = WorkspaceManager(config_dir=config_dir)

        result = manager.switch_project("nonexistent")
        assert result["status"] == "ERROR"
        assert "not found" in result["message"]

    def test_get_workspace_manager_singleton(self):
        """Test global singleton initialization (lines 250-252)."""
        import boring.workspace

        boring.workspace._workspace = None

        manager1 = get_workspace_manager()
        manager2 = get_workspace_manager()

        assert manager1 is manager2
        assert manager1 is not None

    def test_get_project_path_fallback(self, tmp_path):
        """Test get_project_path fallbacks."""
        manager = WorkspaceManager(config_dir=tmp_path)

        # Case 1: active is None
        assert manager.get_project_path(None) is None

        # Case 2: specify name not in projects
        assert manager.get_project_path("missing") is None

        # Case 3: valid project
        p_path = tmp_path / "valid"
        p_path.mkdir()
        manager.add_project("v1", str(p_path))
        assert manager.get_project_path("v1") == p_path.resolve()
