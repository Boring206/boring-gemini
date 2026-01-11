import json
from unittest.mock import MagicMock, patch

import pytest

from boring.loop.workflow_manager import WorkflowManager, WorkflowMetadata, WorkflowPackage


class TestWorkflowManager:
    @pytest.fixture
    def manager(self, tmp_path):
        return WorkflowManager(project_root=tmp_path)

    @pytest.fixture
    def sample_workflow_md(self):
        return """---
description: Test Workflow
---
# Step 1
Do something.
"""

    def test_workflow_package_json_serialization(self):
        meta = WorkflowMetadata(name="test", version="1.0.0", description="desc")
        pkg = WorkflowPackage(metadata=meta, content="content")
        json_str = pkg.to_json()
        data = json.loads(json_str)
        assert data["metadata"]["name"] == "test"
        assert data["content"] == "content"

    def test_workflow_package_from_json(self):
        json_data = {
            "metadata": {"name": "test", "version": "1.1.0", "description": "d"},
            "content": "some content",
        }
        pkg = WorkflowPackage.from_json(json.dumps(json_data))
        assert pkg.metadata.name == "test"
        assert pkg.content == "some content"

    def test_list_local_workflows(self, manager):
        (manager.workflows_dir / "flow1.md").touch()
        (manager.workflows_dir / "flow2.md").touch()
        flows = manager.list_local_workflows()
        assert "flow1" in flows
        assert "flow2" in flows

    def test_export_workflow(self, manager, sample_workflow_md):
        name = "test_flow"
        (manager.workflows_dir / f"{name}.md").write_text(sample_workflow_md)

        path, msg = manager.export_workflow(name)
        assert path.exists()
        assert f"{name}.bwf.json" in str(path)

        # Verify content
        data = json.loads(path.read_text())
        assert data["metadata"]["description"] == "Test Workflow"

    def test_install_workflow_local(self, manager):
        name = "imported_flow"
        pkg_data = {
            "metadata": {"name": name, "version": "1.0.0", "description": "desc"},
            "content": "# New Flow Content",
        }
        pkg_file = manager.project_root / "pkg.json"
        pkg_file.write_text(json.dumps(pkg_data))

        success, msg = manager.install_workflow(str(pkg_file))
        assert success
        assert (manager.workflows_dir / f"{name}.md").exists()
        assert (manager.workflows_dir / f"{name}.md").read_text() == "# New Flow Content"

    def test_install_workflow_url(self, manager):
        name = "url_flow"
        pkg_data = {
            "metadata": {"name": name, "version": "1.0.0", "description": "desc"},
            "content": "# URL Flow Content",
        }

        with patch("urllib.request.urlopen") as mock_url:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(pkg_data).encode("utf-8")
            mock_response.__enter__.return_value = mock_response
            mock_url.return_value = mock_response

            success, msg = manager.install_workflow("https://example.com/flow.json")
            assert success
            assert (manager.workflows_dir / f"{name}.md").exists()

    def test_publish_workflow_gist(self, manager, sample_workflow_md):
        name = "pub_flow"
        (manager.workflows_dir / f"{name}.md").write_text(sample_workflow_md)

        with patch("urllib.request.urlopen") as mock_url:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(
                {
                    "html_url": "https://gist.github.com/123",
                    "files": {f"{name}.bwf.json": {"raw_url": "https://gist.github.com/raw/123"}},
                }
            ).encode("utf-8")
            mock_response.__enter__.return_value = mock_response
            mock_url.return_value = mock_response

            success, url_msg = manager.publish_workflow(name, "fake_token")
            assert success
            assert "https://gist.github.com/raw/123" in url_msg

    def test_parse_frontmatter_complex(self, manager):
        content = """---
key1: value1
key2: value 2 with spaces
---
Body content"""
        meta = manager._parse_frontmatter(content)
        assert meta["key1"] == "value1"
        assert meta["key2"] == "value 2 with spaces"
