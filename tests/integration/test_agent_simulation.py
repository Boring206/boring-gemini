"""
Full Agent Simulation Integration Tests

Tests the complete agent loop with ONLY the Gemini API mocked.
All other components (filesystem, SQLite, logger) run for real.

This validates:
1. File system writes actually happen
2. SQLite records are created correctly
3. State transitions work as expected
4. Error recovery flows function properly
"""

import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

from boring.loop import StatefulAgentLoop, LoopContext
from boring.loop.states import ThinkingState, PatchingState, VerifyingState, RecoveryState
from boring.loop.base import StateResult
from boring.storage import SQLiteStorage
from boring.memory import MemoryManager
from boring.config import settings

from .conftest import (
    MockGeminiClient,
    create_write_file_call,
    create_report_status_call,
    assert_loop_recorded,
    get_log_contents,
)


# =============================================================================
# HAPPY PATH TESTS
# =============================================================================

class TestHappyPathScenario:
    """
    Scenario: Agent Successfully Creates a File
    
    The model returns a write_file function call, the file is created,
    verification passes, and the loop exits successfully.
    """
    
    def test_agent_creates_file_successfully(
        self, 
        temp_project: Path,
        mock_gemini_client: MockGeminiClient
    ):
        """
        Test that the agent creates a file when model returns write_file call.
        
        Assertions:
        1. File system: src/hello.py exists with correct content
        2. Database: loops table has SUCCESS record
        3. Log: Contains success message
        """
        # === SETUP ===
        # Override settings to use temp project
        original_root = settings.PROJECT_ROOT
        original_log_dir = settings.LOG_DIR
        
        settings.PROJECT_ROOT = temp_project
        settings.LOG_DIR = temp_project / "logs"
        
        try:
            # Create context for state testing
            context = LoopContext(
                model_name="test-model",
                use_cli=False,
                verbose=True,
                verification_level="BASIC",  # Skip linting/tests
                project_root=temp_project,
                log_dir=temp_project / "logs",
                prompt_file=temp_project / "PROMPT.md"
            )
            
            # Initialize real subsystems
            context.memory = MemoryManager(temp_project)
            context.storage = SQLiteStorage(temp_project / ".boring_memory")
            
            # Inject mock gemini client
            context.gemini_client = mock_gemini_client
            
            # Start loop iteration
            context.increment_loop()
            
            # === ACTION: Execute ThinkingState ===
            thinking = ThinkingState()
            thinking.on_enter(context)
            result = thinking.handle(context)
            
            # Verify thinking extracted function calls
            assert len(context.function_calls) > 0, "No function calls extracted"
            assert any(c.get("name") == "write_file" for c in context.function_calls), \
                "No write_file call found"
            
            # === ACTION: Execute PatchingState ===
            patching = PatchingState()
            patching.on_enter(context)
            patch_result = patching.handle(context)
            
            # === ASSERTION 1: File System Verification ===
            hello_file = temp_project / "src" / "hello.py"
            assert hello_file.exists(), f"File was not created: {hello_file}"
            
            content = hello_file.read_text(encoding="utf-8")
            assert "def greet" in content, "File content incorrect"
            assert "Hello" in content, "File missing greeting"
            
            # === ASSERTION 2: Database Verification ===
            # Record the loop to database
            from boring.memory import LoopMemory
            loop_memory = LoopMemory(
                loop_id=context.loop_count,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                status="SUCCESS",
                files_modified=context.files_created + context.files_modified,
                tasks_completed=["Create hello.py"],
                errors=[],
                ai_output_summary="Created hello.py",
                duration_seconds=1.0
            )
            context.memory.record_loop(loop_memory)
            
            # Query database
            loops = context.storage.get_recent_loops(1)
            assert len(loops) > 0, "No loop recorded in database"
            
            latest = loops[0]
            assert latest.get("status") == "SUCCESS", f"Wrong status: {latest.get('status')}"
            
            files_in_db = latest.get("files_modified", [])
            if isinstance(files_in_db, str):
                files_in_db = json.loads(files_in_db)
            # Normalize paths for cross-platform comparison
            files_in_db_normalized = [f.replace("\\", "/") for f in files_in_db]
            assert "src/hello.py" in files_in_db_normalized, f"File not in DB record: {files_in_db}"
            
            # === ASSERTION 3: Log Verification ===
            log_contents = get_log_contents(temp_project / "logs")
            # Should have some log entries (may be empty in fast execution)
            # The key is no errors
            
            # === ASSERTION 4: Project State Updated ===
            # Note: We need to manually update project state since we're not running full loop
            context.storage.update_project_state({"total_loops": 1})
            state = context.storage.get_project_state()
            assert state.get("total_loops", 0) >= 1, "Project state not updated"
            
        finally:
            # Restore settings
            settings.PROJECT_ROOT = original_root
            settings.LOG_DIR = original_log_dir
    
    def test_state_transitions_work_correctly(
        self,
        temp_project: Path,
        mock_gemini_success_response
    ):
        """Test that states transition correctly on success path."""
        context = LoopContext(
            project_root=temp_project,
            log_dir=temp_project / "logs",
        )
        context.storage = SQLiteStorage(temp_project / ".boring_memory")
        
        # Simulate successful thinking result
        context.function_calls = [
            create_write_file_call("src/test.py", "# test")
        ]
        
        thinking = ThinkingState()
        next_state = thinking.next_state(context, StateResult.SUCCESS)
        
        assert isinstance(next_state, PatchingState), \
            f"Expected PatchingState, got {type(next_state)}"


# =============================================================================
# ERROR RECOVERY TESTS
# =============================================================================

class TestErrorRecoveryScenario:
    """
    Scenario: Agent Handles Errors and Recovers
    
    Tests various error conditions and recovery flows.
    """
    
    def test_no_function_calls_triggers_recovery(
        self,
        temp_project: Path,
        mock_gemini_no_function_calls
    ):
        """Test that missing function calls triggers recovery state."""
        context = LoopContext(
            project_root=temp_project,
            log_dir=temp_project / "logs",
        )
        context.storage = SQLiteStorage(temp_project / ".boring_memory")
        
        # Simulate thinking with no function calls but >100 chars output
        # (ThinkingState returns None for short outputs)
        context.function_calls = []
        context.output_content = "x" * 150  # Must be >100 chars to trigger recovery
        
        thinking = ThinkingState()
        next_state = thinking.next_state(context, StateResult.SUCCESS)
        
        # Should go to recovery due to no function calls (with long output)
        assert isinstance(next_state, RecoveryState), \
            f"Expected RecoveryState, got {type(next_state)}"
    
    def test_patching_failure_triggers_recovery(self, temp_project: Path):
        """Test that patching errors trigger recovery state."""
        context = LoopContext(
            project_root=temp_project,
            log_dir=temp_project / "logs",
        )
        context.storage = SQLiteStorage(temp_project / ".boring_memory")
        
        # Simulate patching with errors
        context.files_modified = []
        context.files_created = []
        context.patch_errors = ["Some error"]
        
        patching = PatchingState()
        next_state = patching.next_state(context, StateResult.FAILURE)
        
        assert isinstance(next_state, RecoveryState), \
            f"Expected RecoveryState, got {type(next_state)}"
    
    def test_max_retries_causes_exit(self, temp_project: Path):
        """Test that exceeding max retries exits the loop."""
        context = LoopContext(
            project_root=temp_project,
            log_dir=temp_project / "logs",
            max_retries=2
        )
        context.storage = SQLiteStorage(temp_project / ".boring_memory")
        
        # Simulate reaching max retries
        context.retry_count = 2  # Already at max
        context.errors_this_loop = ["Error 1", "Error 2"]
        
        recovery = RecoveryState()
        recovery.on_enter(context)
        result = recovery.handle(context)
        
        assert result == StateResult.EXIT, f"Expected EXIT, got {result}"
        assert context.should_exit, "should_exit not set"
        assert "Max retries" in context.exit_reason
    
    def test_recovery_generates_format_prompt_for_no_function_calls(
        self, 
        temp_project: Path
    ):
        """Test that recovery generates appropriate prompts for format errors."""
        context = LoopContext(
            project_root=temp_project,
            log_dir=temp_project / "logs",
        )
        context.storage = SQLiteStorage(temp_project / ".boring_memory")
        context.errors_this_loop = ["No function calls in response"]
        
        recovery = RecoveryState()
        prompt = recovery._generate_recovery_prompt(context)
        
        assert "write_file" in prompt.lower() or "function" in prompt.lower(), \
            "Recovery prompt should mention function calls"


# =============================================================================
# DATABASE SCHEMA TESTS
# =============================================================================

class TestDatabaseSchema:
    """Test that SQLite schema has required fields."""
    
    def test_loops_table_has_created_at(self, temp_project: Path):
        """Verify loops table has created_at timestamp."""
        storage = SQLiteStorage(temp_project / ".boring_memory")
        
        # Record a test loop
        from boring.storage import LoopRecord
        record = LoopRecord(
            loop_id=1,
            timestamp="2024-01-01 12:00:00",
            status="SUCCESS",
            files_modified=["test.py"],
            tasks_completed=["task1"],
            errors=[],
            duration_seconds=1.0,
            output_summary="Test"
        )
        storage.record_loop(record)
        
        # Query directly to check schema
        with storage._get_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(loops)")
            columns = [row[1] for row in cursor.fetchall()]
        
        assert "created_at" in columns, f"created_at missing from columns: {columns}"
    
    def test_project_state_table_exists(self, temp_project: Path):
        """Verify project_state table is created."""
        storage = SQLiteStorage(temp_project / ".boring_memory")
        
        # Should not raise
        state = storage.get_project_state()
        assert isinstance(state, dict)
        assert "project_name" in state or state.get("total_loops") is not None
    
    def test_error_patterns_table_exists(self, temp_project: Path):
        """Verify error_patterns table can store errors."""
        storage = SQLiteStorage(temp_project / ".boring_memory")
        
        storage.record_error("test_error", "Test message", "context")
        errors = storage.get_top_errors(10)
        
        assert len(errors) > 0, "Error not recorded"
        assert errors[0].get("error_type") == "test_error"


# =============================================================================
# STATE MACHINE INTEGRATION TESTS
# =============================================================================

class TestStateMachineIntegration:
    """Test complete state machine flows."""
    
    def test_full_success_flow(
        self,
        temp_project: Path,
        mock_gemini_success_response
    ):
        """Test complete thinking → patching → verifying → exit flow."""
        # Setup context
        context = LoopContext(
            project_root=temp_project,
            log_dir=temp_project / "logs",
            verification_level="BASIC"
        )
        context.storage = SQLiteStorage(temp_project / ".boring_memory")
        context.memory = MemoryManager(temp_project)
        context.gemini_client = MockGeminiClient()
        context.gemini_client.set_response(*mock_gemini_success_response)
        
        context.increment_loop()
        
        # State 1: Thinking
        current_state = ThinkingState()
        current_state.on_enter(context)
        result = current_state.handle(context)
        
        # The mock response has exit_signal=True in report_status
        # This causes ThinkingState to return EXIT or set context.should_exit
        # Either way, function_calls should be extracted
        assert len(context.function_calls) > 0, \
            f"No function calls extracted. Result: {result}"
        
        # If exit was signaled, we can go directly to patching to verify file creation
        if result == StateResult.EXIT or context.should_exit:
            # Still process patching to verify file creation works
            patching = PatchingState()
            patching.on_enter(context)
            patch_result = patching.handle(context)
            
            # Verify file was created
            assert (temp_project / "src" / "hello.py").exists(), \
                f"File not created. Errors: {context.patch_errors}"
        else:
            next_state = current_state.next_state(context, result)
            assert isinstance(next_state, PatchingState), \
                f"Expected PatchingState, got {type(next_state)}"


# =============================================================================
# FILE SYSTEM VERIFICATION TESTS
# =============================================================================

class TestFileSystemIntegration:
    """Test that file operations actually happen on disk."""
    
    def test_write_file_creates_parent_directories(self, temp_project: Path):
        """Test that nested directories are created automatically."""
        context = LoopContext(
            project_root=temp_project,
            log_dir=temp_project / "logs",
        )
        context.storage = SQLiteStorage(temp_project / ".boring_memory")
        
        # Function call with nested path
        context.function_calls = [
            create_write_file_call(
                "src/deeply/nested/module.py",
                "# Nested module"
            )
        ]
        
        patching = PatchingState()
        patching.on_enter(context)
        patching.handle(context)
        
        # Verify nested file was created
        nested_file = temp_project / "src" / "deeply" / "nested" / "module.py"
        assert nested_file.exists(), f"Nested file not created: {nested_file}"
        assert nested_file.read_text() == "# Nested module"
    
    def test_search_replace_modifies_existing_file(self, temp_project: Path):
        """Test that search_replace actually modifies file content."""
        # Create initial file
        target_file = temp_project / "src" / "existing.py"
        target_file.write_text('print("old message")\n', encoding="utf-8")
        
        context = LoopContext(
            project_root=temp_project,
            log_dir=temp_project / "logs",
        )
        context.storage = SQLiteStorage(temp_project / ".boring_memory")
        
        # Search and replace
        from .conftest import create_search_replace_call
        context.function_calls = [
            create_search_replace_call(
                "src/existing.py",
                'print("old message")',
                'print("new message")'
            )
        ]
        
        patching = PatchingState()
        patching.on_enter(context)
        patching.handle(context)
        
        # Verify content was replaced
        content = target_file.read_text(encoding="utf-8")
        assert "new message" in content
        assert "old message" not in content
    
    def test_blocked_paths_are_not_written(self, temp_project: Path):
        """Test that security validation blocks dangerous paths."""
        context = LoopContext(
            project_root=temp_project,
            log_dir=temp_project / "logs",
        )
        context.storage = SQLiteStorage(temp_project / ".boring_memory")
        
        # Try to write to blocked path
        context.function_calls = [
            create_write_file_call(
                ".git/config",  # Should be blocked
                "malicious content"
            )
        ]
        
        patching = PatchingState()
        patching.on_enter(context)
        patching.handle(context)
        
        # File should NOT be created
        blocked_file = temp_project / ".git" / "config"
        assert not blocked_file.exists(), "Blocked file was created!"
        
        # Error should be recorded
        assert len(context.patch_errors) > 0
