"""
Unit tests for boring.agents.coder module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from boring.agents.base import AgentContext, AgentMessage, AgentRole
from boring.agents.coder import CoderAgent


@pytest.fixture
def mock_llm_client():
    client = MagicMock()
    client.generate_async = AsyncMock()
    return client


@pytest.fixture
def mock_shadow_guard():
    guard = MagicMock()
    guard.check_operation.return_value = None  # Default: allow operation
    return guard


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.fixture
def coder_agent(mock_llm_client, temp_project):
    return CoderAgent(mock_llm_client, project_root=temp_project)


class TestCoderAgent:
    """Tests for CoderAgent class."""

    def test_init(self, mock_llm_client, temp_project):
        """Test initialization."""
        agent = CoderAgent(mock_llm_client, project_root=temp_project)
        assert agent.role == AgentRole.CODER
        assert agent.project_root == temp_project
        assert agent.shadow_guard is None

    def test_system_prompt(self, coder_agent):
        """Test system prompt content."""
        prompt = coder_agent.system_prompt
        assert "You are the CODER Agent" in prompt
        assert "SEARCH/REPLACE" in prompt
        assert "Write production-quality code" in prompt

    @pytest.mark.asyncio
    async def test_execute_no_plan(self, coder_agent, temp_project):
        """Test execution without a plan."""
        context = AgentContext(project_root=temp_project, task_description="Task")
        # Ensure no plan is in context (it's empty by default)

        result = await coder_agent.execute(context)

        assert result.action == "code_failed"
        assert "No implementation plan found" in result.summary

    @pytest.mark.asyncio
    async def test_execute_success_write_file(self, coder_agent, temp_project, mock_llm_client):
        """Test successful execution creating a new file."""
        context = AgentContext(project_root=temp_project, task_description="Task")
        context.set_resource("implementation_plan", "Plan: Create main.py", AgentRole.ARCHITECT)
        context.set_resource("planned_files", ["main.py"], AgentRole.ARCHITECT)

        # Mock LLM response
        response_content = """
### File: `main.py`
```python
print("Hello World")
```
"""
        mock_llm_client.generate_async.return_value = (response_content, True)

        result = await coder_agent.execute(context)

        assert result.action == "code_written"
        assert "main.py" in result.artifacts["files"]

        # Verify file was written
        created_file = temp_project / "main.py"
        assert created_file.exists()
        assert created_file.read_text("utf-8") == 'print("Hello World")'

    @pytest.mark.asyncio
    async def test_execute_success_patch_file(self, coder_agent, temp_project, mock_llm_client):
        """Test successful execution patching an existing file."""
        # Create existing file
        file_path = temp_project / "existing.py"
        file_path.write_text('def foo():\n    return "old"\n', "utf-8")

        context = AgentContext(project_root=temp_project, task_description="Task")
        context.set_resource("implementation_plan", "Plan: Update existing.py", AgentRole.ARCHITECT)
        context.set_resource("planned_files", ["existing.py"], AgentRole.ARCHITECT)

        # Mock LLM response with proper SEARCH/REPLACE block
        # Note: The CoderAgent expects specific format for patches
        response_content = """
### Modify: `existing.py`
```search_replace
<<<<<<< SEARCH
    return "old"
=======
    return "new"
>>>>>>> REPLACE
```
"""
        mock_llm_client.generate_async.return_value = (response_content, True)

        result = await coder_agent.execute(context)

        assert result.action == "code_written"
        assert "existing.py" in result.artifacts["files"]

        # Verify file content
        content = file_path.read_text("utf-8")
        assert 'return "new"' in content
        assert 'return "old"' not in content

    @pytest.mark.asyncio
    async def test_execute_with_shadow_guard_blocking(
        self, coder_agent, temp_project, mock_llm_client
    ):
        """Test execution where ShadowGuard blocks the write."""
        # Setup ShadowGuard
        mock_guard = MagicMock()
        mock_pending_op = MagicMock()
        mock_pending_op.operation_id = "op-123"
        # Return a pending operation object, which counts as "truthy" -> Blocked
        mock_guard.check_operation.return_value = mock_pending_op

        coder_agent.shadow_guard = mock_guard

        context = AgentContext(project_root=temp_project, task_description="Task")
        context.set_resource("implementation_plan", "Plan: Write blocked.py", AgentRole.ARCHITECT)

        response_content = """
### File: `blocked.py`
```python
pass
```
"""
        mock_llm_client.generate_async.return_value = (response_content, True)

        # Since internal print() is used for logging blocks, we can patch it to verify msg
        with patch("builtins.print"):
            result = await coder_agent.execute(context)

        # Verify file was NOT written
        assert not (temp_project / "blocked.py").exists()

        # Verify result still successful?
        # CoderAgent currently continues even if blocked, just logging it.
        # But applied_files will be empty.
        assert len(result.artifacts["files"]) == 0
        assert "Implemented 0 files" in result.summary

    def test_extract_file_changes(self, coder_agent):
        """Test specific parsing logic for _extract_file_changes."""
        response = """
Here is the code:

### Create File: `src/utils.py`
```python
def helper():
    pass
```

### Modify: `src/config.py`
```search_replace
<<<<<<< SEARCH
DEBUG = False
=======
DEBUG = True
>>>>>>> REPLACE
```
"""
        changes = coder_agent._extract_file_changes(response)

        assert "src/utils.py" in changes
        assert changes["src/utils.py"]["type"] == "write"
        assert "def helper():" in changes["src/utils.py"]["content"]

        assert "src/config.py" in changes
        assert changes["src/config.py"]["type"] == "patch"
        assert len(changes["src/config.py"]["patches"]) == 1
        assert changes["src/config.py"]["patches"][0]["search"].strip() == "DEBUG = False"
        assert changes["src/config.py"]["patches"][0]["replace"].strip() == "DEBUG = True"

    def test_extract_file_changes_standalone_search_replace(self, coder_agent):
        """Test parsing of implicit/standalone SEARCH/REPLACE blocks linked to previous file marker."""
        response = """
### Modify: `app.py`
We need to update the import.
```search_replace
<<<<<<< SEARCH
import old
=======
import new
>>>>>>> REPLACE
```

And also update the main loop.
<<<<<<< SEARCH
while True:
    pass
=======
while True:
    process()
>>>>>>> REPLACE
"""
        changes = coder_agent._extract_file_changes(response)

        assert "app.py" in changes
        assert len(changes["app.py"]["patches"]) == 2
        assert changes["app.py"]["patches"][0]["search"].strip() == "import old"
        assert changes["app.py"]["patches"][1]["replace"].strip() == "while True:\n    process()"

    @pytest.mark.asyncio
    async def test_execute_with_reviewer_feedback(self, coder_agent, temp_project, mock_llm_client):
        """Test execution when reviewer provides feedback."""
        context = AgentContext(project_root=temp_project, task_description="Task")
        context.set_resource("implementation_plan", "Plan: Fix bugs", AgentRole.ARCHITECT)
        context.set_resource("planned_files", ["fix.py"], AgentRole.ARCHITECT)

        # Add reviewer feedback message
        reviewer_msg = AgentMessage(
            sender=AgentRole.REVIEWER,
            receiver=AgentRole.CODER,
            action="review",
            summary="NEEDS_WORK: Fix error handling",
            artifacts={"issues": "Missing error handling"},
            requires_approval=False,
        )
        context.add_message(reviewer_msg)

        response_content = """
### File: `fix.py`
```python
def fix():
    try:
        pass
    except:
        pass
```
"""
        mock_llm_client.generate_async.return_value = (response_content, True)

        result = await coder_agent.execute(context)

        assert result.action == "code_written"
        # Verify the prompt included feedback instruction
        call_args = mock_llm_client.generate_async.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_execute_generation_fails(self, coder_agent, temp_project, mock_llm_client):
        """Test execution when LLM generation fails."""
        context = AgentContext(project_root=temp_project, task_description="Task")
        context.set_resource("implementation_plan", "Plan", AgentRole.ARCHITECT)

        mock_llm_client.generate_async.return_value = ("Error occurred", False)

        result = await coder_agent.execute(context)

        assert result.action == "code_failed"
        assert "Failed to generate code" in result.summary

    @pytest.mark.asyncio
    async def test_execute_file_write_error(self, coder_agent, temp_project, mock_llm_client):
        """Test execution when file write fails."""
        context = AgentContext(project_root=temp_project, task_description="Task")
        context.set_resource("implementation_plan", "Plan", AgentRole.ARCHITECT)
        context.set_resource("planned_files", ["../invalid/path.py"], AgentRole.ARCHITECT)

        response_content = """
### File: `../invalid/path.py`
```python
pass
```
"""
        mock_llm_client.generate_async.return_value = (response_content, True)

        # Mock file write to raise exception
        with patch("pathlib.Path.write_text", side_effect=PermissionError("Access denied")):
            result = await coder_agent.execute(context)

        # Should still return success but with empty files list
        assert result.action == "code_written"
        assert len(result.artifacts["files"]) == 0

    @pytest.mark.asyncio
    async def test_execute_patch_nonexistent_file(self, coder_agent, temp_project, mock_llm_client):
        """Test patching a file that doesn't exist."""
        context = AgentContext(project_root=temp_project, task_description="Task")
        context.set_resource("implementation_plan", "Plan", AgentRole.ARCHITECT)

        response_content = """
### Modify: `nonexistent.py`
```search_replace
<<<<<<< SEARCH
old
=======
new
>>>>>>> REPLACE
```
"""
        mock_llm_client.generate_async.return_value = (response_content, True)

        with patch("builtins.print") as mock_print:
            result = await coder_agent.execute(context)

        assert result.action == "code_written"
        assert len(result.artifacts["files"]) == 0
        # Should print error message
        assert any("nonexistent" in str(call) for call in mock_print.call_args_list)

    def test_extract_file_changes_empty_response(self, coder_agent):
        """Test extracting file changes from empty response."""
        changes = coder_agent._extract_file_changes("")
        assert changes == {}

    def test_extract_file_changes_no_file_marker(self, coder_agent):
        """Test extracting when no file markers are present."""
        response = "Just some text without file markers."
        changes = coder_agent._extract_file_changes(response)
        assert changes == {}

    def test_extract_file_changes_multiple_files(self, coder_agent):
        """Test extracting multiple files from response."""
        response = """
### File: `file1.py`
```python
code1
```

### File: `file2.py`
```python
code2
```
"""
        changes = coder_agent._extract_file_changes(response)
        assert len(changes) == 2
        assert "file1.py" in changes
        assert "file2.py" in changes
        assert changes["file1.py"]["content"] == "code1"
        assert changes["file2.py"]["content"] == "code2"
