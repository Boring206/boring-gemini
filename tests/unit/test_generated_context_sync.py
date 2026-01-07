# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.context_sync module.
"""

from datetime import datetime

import pytest

from boring.context_sync import ContextSyncManager, ConversationContext

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "project"
    project.mkdir()
    return project


# =============================================================================
# CONVERSATION CONTEXT TESTS
# =============================================================================


class TestConversationContext:
    """Tests for ConversationContext dataclass."""

    def test_conversation_context_creation(self):
        """Test ConversationContext creation."""
        context = ConversationContext(
            context_id="ctx-123",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            project_path="/project",
            summary="Test context",
            messages=[{"role": "user", "content": "test"}],
            metadata={"key": "value"},
        )
        assert context.context_id == "ctx-123"
        assert len(context.messages) == 1

    def test_conversation_context_defaults(self):
        """Test ConversationContext with default values."""
        context = ConversationContext(
            context_id="ctx-123",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            project_path="/project",
            summary="Test",
        )
        assert context.messages == []
        assert context.metadata == {}


# =============================================================================
# CONTEXT SYNC MANAGER TESTS
# =============================================================================


class TestContextSyncManager:
    """Tests for ContextSyncManager class."""

    def test_context_sync_manager_init(self, temp_project):
        """Test ContextSyncManager initialization."""
        manager = ContextSyncManager(temp_project)
        assert manager.project_root == temp_project
        assert manager.context_dir == temp_project / ".boring_context"
        assert manager.context_dir.exists()

    def test_context_sync_manager_save_context(self, temp_project):
        """Test save_context method."""
        manager = ContextSyncManager(temp_project)
        result = manager.save_context(
            context_id="ctx-123",
            summary="Test context",
            messages=[{"role": "user", "content": "test"}],
        )

        assert result["status"] == "saved"
        assert result["context_id"] == "ctx-123"
        assert manager.context_dir.exists()

    def test_context_sync_manager_save_context_with_metadata(self, temp_project):
        """Test save_context with metadata."""
        manager = ContextSyncManager(temp_project)
        result = manager.save_context(
            context_id="ctx-123",
            summary="Test",
            metadata={"key": "value"},
        )

        assert result["status"] == "saved"
        # Verify file was created
        context_file = manager.context_dir / "ctx-123.json"
        assert context_file.exists()

    def test_context_sync_manager_load_context(self, temp_project):
        """Test load_context method."""
        manager = ContextSyncManager(temp_project)

        # Save context first
        manager.save_context(context_id="ctx-123", summary="Test context")

        # Load it
        context = manager.load_context("ctx-123")
        assert context["context_id"] == "ctx-123"
        assert context["summary"] == "Test context"

    def test_context_sync_manager_load_context_not_found(self, temp_project):
        """Test load_context with nonexistent context."""
        manager = ContextSyncManager(temp_project)
        context = manager.load_context("nonexistent")
        assert context["status"] == "not_found"

    def test_context_sync_manager_list_contexts(self, temp_project):
        """Test list_contexts method."""
        manager = ContextSyncManager(temp_project)

        # Save multiple contexts
        manager.save_context(context_id="ctx-1", summary="Context 1")
        manager.save_context(context_id="ctx-2", summary="Context 2")

        contexts = manager.list_contexts()
        assert len(contexts) >= 2

    def test_context_sync_manager_delete_context(self, temp_project):
        """Test delete_context method."""
        manager = ContextSyncManager(temp_project)

        # Save context
        manager.save_context(context_id="ctx-123", summary="Test")

        # Delete it
        result = manager.delete_context("ctx-123")
        assert result["status"] == "deleted"

        # Verify file was deleted
        context_file = manager.context_dir / "ctx-123.json"
        assert not context_file.exists()

    def test_context_sync_manager_delete_context_not_found(self, temp_project):
        """Test delete_context with nonexistent context."""
        manager = ContextSyncManager(temp_project)
        result = manager.delete_context("nonexistent")
        assert result["status"] == "not_found"
