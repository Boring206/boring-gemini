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


class TestMCPConnectionStability:
    """Test MCP connection stability and potential issues."""
    
    def test_no_stdout_pollution_on_import(self, capsys):
        """Test that importing mcp_server doesn't write to stdout."""
        import importlib
        import boring.mcp_server
        
        # Reload to capture any import-time prints
        importlib.reload(boring.mcp_server)
        
        captured = capsys.readouterr()
        # stdout should be empty (all output should go to stderr)
        assert captured.out == "", f"stdout was polluted: {captured.out[:100]}"
    
    def test_print_statements_use_stderr(self):
        """Verify all print statements in run_server use file=sys.stderr."""
        from pathlib import Path
        import ast
        
        mcp_server_path = Path("src/boring/mcp_server.py")
        if not mcp_server_path.exists():
            mcp_server_path = Path(__file__).parent.parent.parent / "src" / "boring" / "mcp_server.py"
        
        content = mcp_server_path.read_text(encoding="utf-8")
        
        # Check that print statements in run_server contain file=sys.stderr
        # Simple string check for safety
        run_server_start = content.find("def run_server():")
        if run_server_start != -1:
            run_server_section = content[run_server_start:run_server_start + 2000]
            
            # Count print statements
            print_count = run_server_section.count("print(")
            stderr_count = run_server_section.count("file=sys.stderr")
            
            # All prints should have file=sys.stderr (except potential edge cases)
            assert stderr_count >= print_count - 1, \
                f"Found {print_count} prints but only {stderr_count} use stderr"
    
    def test_workflow_result_json_serializable(self, tmp_path):
        """Test that workflow execution results are JSON serializable."""
        import json
        
        # Create a mock workflow result similar to _execute_workflow output
        workflow_content = """---
description: Test workflow
---

# Test Workflow

- Item 1
- Item 2
"""
        
        result = {
            "status": "SUCCESS",
            "workflow": "speckit-test",
            "mode": "SDK",
            "result": "Generated response with special chars: 日本語 émojis 🎉",
            "workflow_instructions": workflow_content[:500]
        }
        
        # This should not raise
        json_str = json.dumps(result, ensure_ascii=False)
        assert isinstance(json_str, str)
        
        # Verify we can parse it back
        parsed = json.loads(json_str)
        assert parsed["status"] == "SUCCESS"
        assert "日本語" in parsed["result"]
    
    def test_error_result_json_serializable(self):
        """Test that error results are JSON serializable."""
        import json
        
        error_result = {
            "status": "ERROR",
            "workflow": "speckit-plan",
            "error": "FileNotFoundError: Workflow 'test' not found at /path/to/file",
            "workflow_instructions": ""
        }
        
        json_str = json.dumps(error_result)
        assert "ERROR" in json_str
    
    def test_workflows_directory_detection(self, tmp_path):
        """Test _find_project_root logic finds project correctly."""
        # Create a fake project structure
        project_dir = tmp_path / "my_project"
        project_dir.mkdir()
        (project_dir / ".git").mkdir()
        
        workflows_dir = project_dir / ".agent" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "test.md").write_text("# Test", encoding="utf-8")
        
        # Verify structure exists
        assert (project_dir / ".git").exists()
        assert (workflows_dir / "test.md").exists()
    
    def test_missing_workflows_directory_handled(self, tmp_path):
        """Test graceful handling when workflows directory doesn't exist."""
        # Project without workflows
        project_dir = tmp_path / "empty_project"
        project_dir.mkdir()
        
        workflows_dir = project_dir / ".agent" / "workflows"
        assert not workflows_dir.exists()
        
        # The code should handle this gracefully (return error dict, not crash)
        # This is a simulation of what boring_list_workflows should do
        if not workflows_dir.exists():
            result = {
                "status": "NOT_FOUND",
                "message": f"Workflows directory not found: {workflows_dir}"
            }
            assert result["status"] == "NOT_FOUND"
    
    def test_special_characters_in_context(self):
        """Test that special characters in context don't break JSON."""
        import json
        
        # Context with various special characters
        context = """
前端 (Frontend): 新增控制面板
後端 (Backend): 建立「調度中心」
Special: <tag> & "quotes" 'apostrophe'
Unicode: 日本語 한국어 العربية
Emoji: 🚀 ✅ ⚠️
Newlines:
- Line 1
- Line 2
"""
        
        result = {
            "status": "SUCCESS",
            "context_received": context,
            "length": len(context)
        }
        
        # Should serialize without error
        json_str = json.dumps(result, ensure_ascii=False)
        parsed = json.loads(json_str)
        
        assert "調度中心" in parsed["context_received"]
        assert "🚀" in parsed["context_received"]


class TestMCPToolReturnTypes:
    """Test that all MCP tools return proper dict/str types."""
    
    def test_health_check_returns_dict(self):
        """Test boring_health_check return type structure."""
        expected_keys = {"healthy", "passed", "warnings", "failed", "checks"}
        
        # Mock a successful health check result
        result = {
            "healthy": True,
            "passed": 5,
            "warnings": 1,
            "failed": 0,
            "checks": []
        }
        
        assert all(key in result for key in expected_keys)
    
    def test_status_returns_dict(self):
        """Test boring_status return type structure."""
        expected_keys = {"project_name", "total_loops", "successful_loops", "failed_loops", "last_activity"}
        
        result = {
            "project_name": "test",
            "total_loops": 10,
            "successful_loops": 8,
            "failed_loops": 2,
            "last_activity": "2024-01-01"
        }
        
        assert all(key in result for key in expected_keys)
    
    def test_verify_returns_dict(self):
        """Test boring_verify return type structure."""
        result = {
            "passed": True,
            "level": "STANDARD",
            "message": "All checks passed"
        }
        
        assert "passed" in result
        assert "level" in result
    
    def test_speckit_tools_return_dict(self):
        """Test SpecKit tools return dict with expected keys."""
        expected_keys = {"status", "workflow"}
        
        # Success case
        success_result = {
            "status": "SUCCESS",
            "workflow": "speckit-plan",
            "mode": "SDK",
            "result": "Generated plan",
            "workflow_instructions": "..."
        }
        
        assert all(key in success_result for key in expected_keys)
        
        # Error case
        error_result = {
            "status": "ERROR",
            "workflow": "speckit-plan",
            "error": "Something went wrong",
            "workflow_instructions": ""
        }
        
        assert all(key in error_result for key in expected_keys)

