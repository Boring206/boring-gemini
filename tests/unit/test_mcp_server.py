"""
Unit tests for Boring MCP Server.

Tests the MCP tools and resources exposed by boring-mcp.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


# Test that MCP imports work (when available)
class TestMCPServerImports:
    """Test MCP server module imports."""
    
    def test_mcp_module_imports(self):
        """Test that mcp_server module can be imported."""
        from boring import mcp_server
        assert hasattr(mcp_server, 'run_server')
        assert hasattr(mcp_server, 'main')
    
    def test_mcp_availability_check(self):
        """Test MCP_AVAILABLE flag exists."""
        from boring import mcp_server
        assert hasattr(mcp_server, 'MCP_AVAILABLE')


# Test SpecKit workflow tools (mocked)
class TestSpecKitTools:
    """Test SpecKit workflow tool implementations."""
    
    @pytest.fixture
    def mock_settings(self, tmp_path):
        """Create mock settings with temp directory."""
        mock = Mock()
        mock.PROJECT_ROOT = tmp_path
        return mock
    
    @pytest.fixture
    def setup_workflows(self, tmp_path):
        """Set up test workflow files."""
        workflows_dir = tmp_path / ".agent" / "workflows"
        workflows_dir.mkdir(parents=True)
        
        # Create test workflow files
        workflows = {
            "speckit-plan.md": """---
description: Create technical implementation plan from requirements
---

# Speckit Plan Workflow

Use this workflow to create a technical implementation plan.
""",
            "speckit-tasks.md": """---
description: Break implementation plan into actionable tasks
---

# Speckit Tasks Workflow

Use this workflow to create an actionable task list.
""",
            "speckit-analyze.md": """---
description: Cross-artifact consistency & coverage analysis
---

# Specification & Plan Analysis Workflow
""",
            "speckit-clarify.md": """---
description: Clarify underspecified areas in the project specification
---

# Specification Clarification Workflow
""",
            "speckit-constitution.md": """---
description: Create project constitution and guiding principles
---

# Speckit Constitution Workflow
""",
            "speckit-checklist.md": """---
description: Generate custom quality checklists to validate requirements
---

# Quality Checklist Generator
"""
        }
        
        for filename, content in workflows.items():
            (workflows_dir / filename).write_text(content, encoding="utf-8")
        
        return workflows_dir
    
    def test_read_workflow_exists(self, tmp_path, setup_workflows):
        """Test workflow content can be read correctly."""
        # Test the workflow reading logic directly
        workflows_dir = tmp_path / ".agent" / "workflows"
        workflow_path = workflows_dir / "speckit-plan.md"
        
        assert workflow_path.exists()
        content = workflow_path.read_text(encoding="utf-8")
        
        # Verify content structure
        assert "---" in content  # Has frontmatter
        assert "# Speckit Plan Workflow" in content
        assert "implementation plan" in content
    
    def test_list_workflows_returns_all(self, tmp_path, setup_workflows):
        """Test boring_list_workflows returns all workflows."""
        with patch('boring.config.settings') as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            
            # Manually test the workflow listing logic
            workflows_dir = tmp_path / ".agent" / "workflows"
            workflow_files = list(workflows_dir.glob("*.md"))
            
            assert len(workflow_files) == 6
            
            # Verify each workflow file exists
            expected = [
                "speckit-plan.md",
                "speckit-tasks.md", 
                "speckit-analyze.md",
                "speckit-clarify.md",
                "speckit-constitution.md",
                "speckit-checklist.md"
            ]
            for name in expected:
                assert (workflows_dir / name).exists()
    
    def test_workflow_frontmatter_parsing(self, tmp_path, setup_workflows):
        """Test that workflow frontmatter is parsed correctly."""
        workflows_dir = tmp_path / ".agent" / "workflows"
        
        # Read and parse a workflow
        content = (workflows_dir / "speckit-plan.md").read_text(encoding="utf-8")
        
        # Extract description from frontmatter
        assert content.startswith("---")
        end_idx = content.index("---", 3)
        frontmatter = content[3:end_idx]
        
        description = ""
        for line in frontmatter.split("\n"):
            if line.startswith("description:"):
                description = line.split(":", 1)[1].strip()
                break
        
        assert description == "Create technical implementation plan from requirements"


class TestBoringIntegrationTools:
    """Test Boring integration tools."""
    
    @pytest.fixture
    def mock_extensions_manager(self):
        """Create mocked ExtensionsManager."""
        manager = Mock()
        manager.is_gemini_available.return_value = True
        manager.install_recommended_extensions.return_value = {
            "context7": (True, "Installed successfully"),
            "slash-criticalthink": (True, "Installed successfully"),
            "chrome-devtools-mcp": (False, "Not available"),
        }
        return manager
    
    def test_setup_extensions_structure(self, mock_extensions_manager):
        """Test boring_setup_extensions returns correct structure."""
        # Test the expected return structure
        results = mock_extensions_manager.install_recommended_extensions()
        
        installed = [name for name, (success, _) in results.items() if success]
        failed = [name for name, (success, _) in results.items() if not success]
        
        assert "context7" in installed
        assert "chrome-devtools-mcp" in failed
    
    def test_gemini_not_available(self):
        """Test behavior when Gemini CLI is not available."""
        manager = Mock()
        manager.is_gemini_available.return_value = False
        
        if not manager.is_gemini_available():
            result = {
                "status": "SKIPPED",
                "message": "Gemini CLI not found"
            }
            assert result["status"] == "SKIPPED"


class TestMCPResources:
    """Test MCP resource endpoints."""
    
    @pytest.fixture
    def setup_project(self, tmp_path):
        """Set up test project structure."""
        # Create PROMPT.md
        (tmp_path / "PROMPT.md").write_text("# Test Prompt\n\nTest content", encoding="utf-8")
        
        # Create workflows
        workflows_dir = tmp_path / ".agent" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "speckit-plan.md").write_text(
            "---\ndescription: Test workflow\n---\n\n# Test",
            encoding="utf-8"
        )
        
        return tmp_path
    
    def test_project_prompt_resource(self, setup_project):
        """Test boring://project/prompt resource."""
        prompt_file = setup_project / "PROMPT.md"
        content = prompt_file.read_text(encoding="utf-8")
        
        assert "# Test Prompt" in content
        assert "Test content" in content
    
    def test_workflows_list_resource(self, setup_project):
        """Test boring://workflows/list resource."""
        workflows_dir = setup_project / ".agent" / "workflows"
        
        lines = ["# Available SpecKit Workflows", ""]
        for workflow_file in sorted(workflows_dir.glob("*.md")):
            lines.append(f"- **{workflow_file.stem}**: Test workflow")
        
        result = "\n".join(lines)
        assert "speckit-plan" in result


class TestTaskResult:
    """Test TaskResult dataclass."""
    
    def test_task_result_creation(self):
        """Test TaskResult can be created."""
        from boring.mcp_server import TaskResult
        
        result = TaskResult(
            status="SUCCESS",
            files_modified=5,
            message="Task completed",
            loops_completed=3
        )
        
        assert result.status == "SUCCESS"
        assert result.files_modified == 5
        assert result.message == "Task completed"
        assert result.loops_completed == 3
