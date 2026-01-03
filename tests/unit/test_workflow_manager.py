import pytest
from unittest.mock import MagicMock, patch, mock_open
import json
from pathlib import Path

from boring.workflow_manager import WorkflowManager, WorkflowPackage, WorkflowMetadata

class TestWorkflowPackage:
    def test_json_serialization(self):
        metadata = WorkflowMetadata(
            name="test-flow", 
            version="1.0.0", 
            description="Test",
            created_at=123.0
        )
        pkg = WorkflowPackage(metadata=metadata, content="# Content")
        json_str = pkg.to_json()
        
        data = json.loads(json_str)
        assert data["metadata"]["name"] == "test-flow"
        assert data["content"] == "# Content"

    def test_from_json_valid(self):
        json_str = json.dumps({
            "metadata": {
                "name": "test-flow",
                "version": "1.0.0",
                "description": "Test",
                "author": "Me"
            },
            "content": "# Markdown"
        })
        pkg = WorkflowPackage.from_json(json_str)
        assert pkg.metadata.name == "test-flow"
        assert pkg.content == "# Markdown"

    def test_from_json_invalid(self):
        with pytest.raises(ValueError, match="Missing required fields"):
            WorkflowPackage.from_json("{}")
            
        with pytest.raises(ValueError, match="Metadata missing 'name'"):
             WorkflowPackage.from_json('{"metadata": {}, "content": ""}')

class TestWorkflowManager:
    @pytest.fixture
    def manager(self, tmp_path):
        """Create manager with temp directory instead of /fake."""
        return WorkflowManager(tmp_path)

    def test_parse_frontmatter(self, manager):
        content = "---\nname: test\nversion: 1.0\n---\n# Body"
        meta = manager._parse_frontmatter(content)
        assert meta["name"] == "test"
        assert meta["version"] == "1.0"

    def test_list_local_workflows(self, manager):
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.glob") as mock_glob:
            
            mock_file = MagicMock()
            mock_file.stem = "flow1"
            mock_glob.return_value = [mock_file]
            
            flows = manager.list_local_workflows()
            assert "flow1" in flows

    def test_export_workflow_success(self, manager):
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value="---\ndescription: Test\n---\n# Content"), \
             patch("pathlib.Path.write_text") as mock_write:
            
            path, msg = manager.export_workflow("flow1")
            
            assert path is not None
            assert "Successfully exported" in msg
            mock_write.assert_called()

    def test_export_workflow_not_found(self, manager):
        with patch("pathlib.Path.exists", return_value=False):
            path, msg = manager.export_workflow("flow1")
            assert path is None
            assert "not found" in msg

    @patch("urllib.request.urlopen")
    def test_install_workflow_url(self, mock_urlopen, manager):
        # Mock URL response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "metadata": {"name": "remote-flow", "version": "1.0"},
            "content": "# Remote"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with patch("pathlib.Path.write_text") as mock_write, \
             patch("pathlib.Path.exists", return_value=False): # No backup needed
             
            success, msg = manager.install_workflow("http://example.com/flow.bwf.json")
            
            assert success is True
            mock_write.assert_called_with("# Remote", encoding="utf-8")

    def test_install_workflow_local_file(self, manager):
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.is_absolute", return_value=True), \
             patch("pathlib.Path.read_text") as mock_read, \
             patch("pathlib.Path.write_text") as mock_write, \
             patch("shutil.copy2"):
             
            mock_read.return_value = json.dumps({
                "metadata": {"name": "local-flow"},
                "content": "# Local"
            })
            
            success, msg = manager.install_workflow("/tmp/flow.bwf.json")
            
            assert success is True, f"Install failed with: {msg}"
            mock_write.assert_called()

    @patch("urllib.request.urlopen")
    def test_publish_workflow_success(self, mock_urlopen, manager):
        # Mock export first
        with patch.object(manager, "export_workflow") as mock_export, \
             patch("pathlib.Path.exists", return_value=True):
            
            mock_file = MagicMock()
            mock_file.read_text.return_value = "{}"
            mock_export.return_value = (mock_file, "Success")
            
            # Mock GitHub API response
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps({
                "html_url": "http://gist.github.com/123",
                "files": {"flow1.bwf.json": {"raw_url": "http://raw/..."}}
            }).encode("utf-8")
            mock_urlopen.return_value.__enter__.return_value = mock_response
            
            success, msg = manager.publish_workflow("flow1", "token")
            
            assert success is True, f"Publish failed with: {msg}"
            assert "Scan this to install" in msg
            mock_file.unlink.assert_called() # Cleanup check
