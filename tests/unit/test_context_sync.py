# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0


import pytest

from boring.context_sync import ContextSyncManager, UserProfileManager


@pytest.fixture
def sync_manager(tmp_path):
    return ContextSyncManager(tmp_path)


def test_save_load_context(sync_manager):
    """Test saving and loading context."""
    cid = "test-ctx-1"
    summary = "Working on tests"

    # Save
    result = sync_manager.save_context(cid, summary, messages=[{"role": "user", "content": "hi"}])
    assert result["status"] == "saved"

    # Load
    loaded = sync_manager.load_context(cid)
    assert loaded["status"] == "loaded"
    assert loaded["summary"] == summary
    assert len(loaded["messages"]) == 1


def test_list_contexts(sync_manager):
    """Test listing contexts."""
    sync_manager.save_context("c1", "s1")
    sync_manager.save_context("c2", "s2")

    contexts = sync_manager.list_contexts()
    assert len(contexts) == 2
    ids = [c["context_id"] for c in contexts]
    assert "c1" in ids
    assert "c2" in ids


def test_user_profile_manager(tmp_path):
    """Test user profile persistence."""
    # Mock home dir by patching Path.home()?
    # Or just use the class directly pointing to tmp

    manager = UserProfileManager()
    manager.profile_dir = tmp_path / ".boring_brain"
    manager.profile_dir.mkdir()
    manager.profile_file = manager.profile_dir / "user_profile.json"

    # Test update style
    manager.update_style("indent", 4)
    profile = manager.load_profile()
    assert profile.coding_style["indent"] == 4

    # Test learn fix
    manager.add_learned_fix("ImportError", "pip install package")
    profile = manager.load_profile()
    assert len(profile.learned_fixes) == 1
    assert profile.learned_fixes[0]["error"] == "ImportError"
