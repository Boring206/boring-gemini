"""
Integration Test Fixtures for Boring

Provides shared fixtures for simulated end-to-end testing.
Only the Gemini API is mocked - all other components (filesystem, SQLite, logger) run for real.
"""

from pathlib import Path
from typing import Any

import pytest

from boring.memory import MemoryManager

# Import boring modules
from boring.storage import SQLiteStorage

# =============================================================================
# TEMP PROJECT FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """
    Create a temporary project directory with minimal structure.

    This is a REAL filesystem directory, not mocked.
    """
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    # Create essential directories
    (project_root / "src").mkdir()
    (project_root / "logs").mkdir()
    (project_root / ".boring_memory").mkdir()

    # Create minimal PROMPT.md
    (project_root / "PROMPT.md").write_text(
        "# Test Project\nCreate a simple hello world file.", encoding="utf-8"
    )

    # Create @fix_plan.md with unchecked items
    (project_root / "@fix_plan.md").write_text(
        "# Tasks\n- [ ] Create hello.py\n- [ ] Add greeting function", encoding="utf-8"
    )

    return project_root


@pytest.fixture
def temp_project_complete(temp_project: Path) -> Path:
    """
    Temporary project with all tasks marked complete.
    """
    (temp_project / "@fix_plan.md").write_text(
        "# Tasks\n- [x] Create hello.py\n- [x] Add greeting function", encoding="utf-8"
    )
    return temp_project


# =============================================================================
# SQLITE STORAGE FIXTURES
# =============================================================================


@pytest.fixture
def sqlite_storage(temp_project: Path) -> SQLiteStorage:
    """
    Create a real SQLite storage instance using the temp project directory.

    This is a REAL database, not mocked.
    """
    memory_dir = temp_project / ".boring_memory"
    storage = SQLiteStorage(memory_dir)
    yield storage
    # Cleanup happens automatically when tmp_path is cleaned


@pytest.fixture
def memory_manager(temp_project: Path) -> MemoryManager:
    """
    Create a real MemoryManager instance.
    """
    return MemoryManager(temp_project)


# =============================================================================
# MOCK GEMINI CLIENT FIXTURES
# =============================================================================


def create_function_call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Helper to create a function call dict."""
    return {"name": name, "args": args}


def create_write_file_call(file_path: str, content: str) -> dict[str, Any]:
    """Create a write_file function call."""
    return create_function_call("write_file", {"file_path": file_path, "content": content})


def create_search_replace_call(file_path: str, search: str, replace: str) -> dict[str, Any]:
    """Create a search_replace function call."""
    return create_function_call(
        "search_replace", {"file_path": file_path, "search": search, "replace": replace}
    )


def create_report_status_call(
    status: str = "IN_PROGRESS",
    tasks_completed: list[str] | None = None,
    files_modified: list[str] | None = None,
    exit_signal: bool = False,
) -> dict[str, Any]:
    """Create a report_status function call."""
    return create_function_call(
        "report_status",
        {
            "status": status,
            "tasks_completed": tasks_completed or [],
            "files_modified": files_modified or [],
            "exit_signal": exit_signal,
        },
    )


@pytest.fixture
def mock_gemini_success_response():
    """
    Mock response for a successful file creation scenario.

    Returns function calls for:
    - write_file: creates src/hello.py
    - report_status: signals task completion
    """
    return (
        "I'll create a hello.py file with a greeting function.",  # text response
        [
            create_write_file_call(
                "src/hello.py",
                'def greet(name: str) -> str:\n    """Return a greeting message."""\n    return f"Hello, {name}!"\n\nif __name__ == "__main__":\n    print(greet("World"))\n',
            ),
            create_report_status_call(
                status="COMPLETE",
                tasks_completed=["Create hello.py", "Add greeting function"],
                files_modified=["src/hello.py"],
                exit_signal=True,
            ),
        ],
        True,  # success flag
    )


@pytest.fixture
def mock_gemini_no_function_calls():
    """Mock response with no function calls (format error scenario)."""
    return (
        "Here's what I would create:\n```python\nprint('hello')\n```",
        [],  # No function calls
        True,
    )


@pytest.fixture
def mock_gemini_partial_response():
    """Mock response with only file write but no exit signal."""
    return (
        "Creating the file...",
        [create_write_file_call("src/hello.py", 'print("hello")\n')],
        True,
    )


class MockGeminiClient:
    """
    Mock Gemini client that returns predefined responses.

    Usage:
        client = MockGeminiClient()
        client.set_response(text, function_calls, success)
        result = client.generate_with_tools(prompt, context)
    """

    def __init__(self):
        self.responses = []
        self.call_count = 0
        self.last_prompt = None
        self.last_context = None

    def set_response(self, text: str, function_calls: list[dict], success: bool):
        """Set a single response or queue multiple."""
        self.responses.append((text, function_calls, success))

    def set_responses(self, *responses):
        """Queue multiple responses for sequential calls."""
        for r in responses:
            self.responses.append(r)

    def generate_with_tools(self, prompt: str, context: str = "") -> tuple:
        """Simulate generate_with_tools call."""
        self.call_count += 1
        self.last_prompt = prompt
        self.last_context = context

        if self.responses:
            # Return and remove first response (FIFO)
            return self.responses.pop(0)

        # Default empty response
        return ("No response configured", [], True)

    def is_available(self) -> bool:
        return True


@pytest.fixture
def mock_gemini_client(mock_gemini_success_response) -> MockGeminiClient:
    """
    Create a mock Gemini client pre-configured with success response.
    """
    client = MockGeminiClient()
    client.set_response(*mock_gemini_success_response)
    return client


# =============================================================================
# LOG VERIFICATION HELPERS
# =============================================================================


def get_log_contents(log_dir: Path) -> str:
    """Read all log file contents from directory."""
    contents = []
    for log_file in log_dir.glob("*.log"):
        try:
            contents.append(log_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return "\n".join(contents)


def assert_log_contains(log_dir: Path, expected: str):
    """Assert that logs contain expected string."""
    contents = get_log_contents(log_dir)
    assert expected in contents, f"Expected '{expected}' not found in logs:\n{contents[:500]}"


# =============================================================================
# DATABASE VERIFICATION HELPERS
# =============================================================================


def query_loops_table(storage: SQLiteStorage, limit: int = 10) -> list[dict]:
    """Query the loops table directly."""
    return storage.get_recent_loops(limit)


def query_project_state(storage: SQLiteStorage) -> dict:
    """Query the project_state table."""
    return storage.get_project_state()


def assert_loop_recorded(
    storage: SQLiteStorage, expected_status: str, expected_file: str | None = None
):
    """Assert that a loop was recorded with expected values."""
    loops = query_loops_table(storage, limit=1)
    assert len(loops) > 0, "No loops recorded in database"

    latest = loops[0]
    assert latest.get("status") == expected_status, (
        f"Expected status {expected_status}, got {latest.get('status')}"
    )

    if expected_file:
        files_modified = latest.get("files_modified", [])
        # Handle JSON string or list
        if isinstance(files_modified, str):
            import json

            files_modified = json.loads(files_modified)
        assert expected_file in files_modified, (
            f"Expected file {expected_file} not in {files_modified}"
        )
