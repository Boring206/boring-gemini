
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boring.flow.state_serializer import StateSerializer
from boring.flow.nodes.base import FlowContext


class TestStateSerializer:
    @pytest.fixture
    def serializer(self, tmp_path):
        return StateSerializer(tmp_path)

    @pytest.fixture
    def mock_context(self, tmp_path):
        context = MagicMock(spec=FlowContext)
        context.project_root = tmp_path
        context.user_goal = "Test Goal"
        context.memory = {"key": "value"}
        context.errors = []
        context.auto_mode = True
        return context

    def test_save_checkpoint_success(self, serializer, mock_context):
        """Test successful checkpoint save."""
        result = serializer.save_checkpoint(mock_context, 1, "start")

        assert result is not None
        assert result.exists()
        assert result.name == "latest.json"

        with open(result, encoding="utf-8") as f:
            data = json.load(f)

        assert data["user_goal"] == "Test Goal"
        assert data["memory"] == {"key": "value"}
        assert data["metadata"]["step_count"] == 1
        assert data["metadata"]["current_node"] == "start"
        assert data["auto_mode"] is True

    def test_save_checkpoint_complex_memory(self, serializer, mock_context):
        """Test saving with non-JSON serializable memory (should be stringified)."""
        mock_context.memory = object()  # Not serializable
        
        result = serializer.save_checkpoint(mock_context, 1, "start")
        
        with open(result, encoding="utf-8") as f:
            data = json.load(f)
            
        assert isinstance(data["memory"], str)
        assert "object" in data["memory"]

    def test_save_checkpoint_failure(self, serializer, mock_context):
        """Test handling of save failures."""
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            result = serializer.save_checkpoint(mock_context, 1, "start")
        
        assert result is None

    def test_load_checkpoint_success(self, serializer, mock_context):
        """Test successful loading."""
        # Save first
        serializer.save_checkpoint(mock_context, 1, "start")
        
        data = serializer.load_checkpoint()
        
        assert data is not None
        assert data["user_goal"] == "Test Goal"

    def test_load_checkpoint_no_file(self, serializer):
        """Test loading when no checkpoint exists."""
        data = serializer.load_checkpoint()
        assert data is None

    def test_load_checkpoint_failure(self, serializer):
        """Test failure during load (e.g. bad json)."""
        # Create invalid file
        checkpoint_file = serializer.checkpoint_dir / "latest.json"
        serializer.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_file.write_text("{invalid json", encoding="utf-8")
        
        with patch("boring.flow.state_serializer.logger") as mock_logger:
            data = serializer.load_checkpoint()
            assert data is None
            mock_logger.error.assert_called()
