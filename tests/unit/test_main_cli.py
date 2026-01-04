
import pytest
from typer.testing import CliRunner
from pathlib import Path
import sys
from unittest.mock import patch

from boring.main import app
from boring.config import settings

runner = CliRunner()

@pytest.fixture
def mock_dependencies(mocker):
    # Setup mocks using pytest-mock
    # Global imports in main.py
    mock_loop = mocker.patch("boring.main.AgentLoop")
    mock_settings = mocker.patch("boring.main.settings")
    mock_show_circuit = mocker.patch("boring.main.show_circuit_status")
    mock_reset_circuit = mocker.patch("boring.main.reset_circuit_breaker")
    mock_subprocess = mocker.patch("subprocess.run")

    # Local imports - must patch at source
    mock_loop_local = mocker.patch("boring.loop.legacy.AgentLoop")
    # Also patch boring.loop.AgentLoop directly to be safe for importers
    mock_loop_direct = mocker.patch("boring.loop.AgentLoop")
    mock_stateful_loop = mocker.patch("boring.loop.StatefulAgentLoop")
    mock_debugger = mocker.patch("boring.debugger.BoringDebugger")
    # ... (rest of fixture)

# ... (End of fixture)

# Add new tests at the end


    mock_memory = mocker.patch("boring.memory.MemoryManager")
    
    mock_setup_ext = mocker.patch("boring.extensions.setup_project_extensions")
    mock_create_ct = mocker.patch("boring.extensions.create_criticalthink_command")
    mock_create_sk = mocker.patch("boring.extensions.create_speckit_command")
    
    mock_health_check = mocker.patch("boring.health.run_health_check")
    mock_print_health = mocker.patch("boring.health.print_health_report")
    
    mock_version = mocker.patch("importlib.metadata.version")
    
    mock_workflow_mgr = mocker.patch("boring.workflow_manager.WorkflowManager")
    
    mock_judge = mocker.patch("boring.judge.LLMJudge")
    mock_gemini_client = mocker.patch("boring.gemini_client.GeminiClient")
    mock_gemini_cli = mocker.patch("boring.cli_client.GeminiCLIAdapter")
    
    mock_autofix = mocker.patch("boring.auto_fix.AutoFixPipeline")
    mock_verifier = mocker.patch("boring.verification.CodeVerifier")
    
    mock_hooks_mgr = mocker.patch("boring.hooks.HooksManager")
    
    # Setup common mock behaviors
    mock_settings.PROJECT_ROOT = Path("/mock/root")
    mock_settings.DEFAULT_MODEL = "mock-model"
    mock_settings.MAX_HOURLY_CALLS = 50
    mock_settings.TIMEOUT_MINUTES = 30
    
    return {
        "loop": mock_loop,
        "stateful_loop": mock_stateful_loop,
        "debugger": mock_debugger,
        "memory": mock_memory,
        "show_circuit": mock_show_circuit,
        "reset_circuit": mock_reset_circuit,
        "settings": mock_settings,
        "setup_ext": mock_setup_ext,
        "create_ct": mock_create_ct,
        "create_sk": mock_create_sk,
        "health_check": mock_health_check,
        "print_health": mock_print_health,
        "version": mock_version,
        "workflow_mgr": mock_workflow_mgr,
        "judge": mock_judge,
        "gemini_client": mock_gemini_client,
        "gemini_cli": mock_gemini_cli,
        "subprocess": mock_subprocess,
        "autofix": mock_autofix,
        "verifier": mock_verifier,
        "hooks_mgr": mock_hooks_mgr,
        "mock_loop_local": mock_loop_local,
        "loop_direct": mock_loop_direct
    }
 
def test_hooks_uninstall_failure(mock_dependencies):
    mock_mgr = mock_dependencies["hooks_mgr"].return_value
    mock_mgr.uninstall_all.return_value = (False, "Commit hook locked")
    
    result = runner.invoke(app, ["hooks", "uninstall"])
    
    assert result.exit_code == 1
    assert "Error: Commit hook locked" in result.stdout

def test_auto_fix_run_boring_exception(mock_dependencies, tmp_path):
    target = tmp_path / "broken.py"
    target.touch()
    
    # Mock pipeline
    mock_pipeline_cls = mock_dependencies["autofix"]
    mock_pipeline_instance = mock_pipeline_cls.return_value
    
    # Configure run_boring_wrapper to simulate exception during loop setup/run
    def side_effect(run_boring_func, verify_func):
        # We invoke run_boring_func and verify it returns ERROR status
        # Simulate exception in AgentLoop init or run
        mock_dependencies["loop"].side_effect = Exception("Simulated Loop Crash")
        # ALSO simulate for local loop (direct import)
        mock_dependencies["loop_direct"].side_effect = Exception("Simulated Loop Crash")
        
        # Call the wrapper (which calls AgentLoop)
        task_desc = "Fix issues"
        res = run_boring_func(task_desc, "STANDARD", 2, str(tmp_path))
        
        assert res["status"] == "ERROR"
        assert "Simulated Loop Crash" in res["message"]
        
        return {"status": "SUCCESS", "iterations": 1} # Pipeline handles it
        
    mock_pipeline_instance.run.side_effect = side_effect
    
    result = runner.invoke(app, ["auto-fix", str(target)])
    assert result.exit_code == 0

def test_start_command_api_backend(mock_dependencies):
    mocks = mock_dependencies
    mocks["loop"].return_value.run.return_value = None
    
    result = runner.invoke(app, ["start", "--backend", "api"])
    
    assert result.exit_code == 0
    assert "API Mode: Using Gemini SDK" in result.stdout
    mocks["loop"].assert_called_once()
    mocks["debugger"].return_value.run_with_healing.assert_called_once()

def test_start_command_cli_backend_privacy_mode(mock_dependencies):
    mocks = mock_dependencies
    
    result = runner.invoke(app, ["start", "--backend", "cli"])
    
    assert result.exit_code == 0
    assert "Privacy Mode: Using local Gemini CLI" in result.stdout
    # Check if use_cli=True was passed
    call_args = mocks["loop"].call_args
    assert call_args.kwargs["use_cli"] is True

def test_start_command_invalid_backend(mock_dependencies):
    result = runner.invoke(app, ["start", "--backend", "invalid"])

# ==============================================================================
# V10.7 Coverage Tests
# ==============================================================================
@patch("boring.main.AgentLoop")
def test_start_cli_backend_coverage(mock_loop):
    """Test boring start command with CLI backend (Coverage)."""
    runner = CliRunner()
    mock_instance = mock_loop.return_value
    result = runner.invoke(app, ["start", "--backend", "cli", "--timeout", "10"])
    assert result.exit_code == 0
    mock_loop.assert_called_once()
    assert mock_loop.call_args[1]["use_cli"] is True

@patch("boring.main.AgentLoop")
def test_start_api_backend_coverage(mock_loop):
    """Test boring start command with API backend (Coverage)."""
    runner = CliRunner()
    result = runner.invoke(app, ["start", "--backend", "api"])
    assert result.exit_code == 0
    assert mock_loop.call_args[1]["use_cli"] is False

@patch("boring.main.MemoryManager")
def test_status_coverage(mock_memory):
    """Test boring status command (Coverage)."""
    runner = CliRunner()
    mock_instance = mock_memory.return_value
    mock_instance.get_project_state.return_value = {"project_name": "Test", "total_loops": 5}
    mock_instance.get_loop_history.return_value = []
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "Test" in result.stdout

@patch("boring.main.CodeVerifier")
def test_verify_command_coverage(mock_verifier):
    """Test verify command (Coverage)."""
    runner = CliRunner()
    mock_instance = mock_verifier.return_value
    mock_instance.verify_project.return_value = (True, "Pass")
    result = runner.invoke(app, ["verify", "--level", "FULL"])
    assert result.exit_code == 0
    assert "Passed" in result.stdout

def test_start_command_experimental_stateful(mock_dependencies):
    mocks = mock_dependencies
    
    result = runner.invoke(app, ["start", "--experimental"])
    
    assert result.exit_code == 0
    assert "Experimental: Using State Pattern Architecture" in result.stdout
    mocks["stateful_loop"].assert_called_once()

def test_start_command_with_custom_prompt(mock_dependencies):
    mocks = mock_dependencies
    
    result = runner.invoke(app, ["start", "--prompt", "custom_prompt.md"])
    
    assert result.exit_code == 0
    assert mocks["settings"].PROMPT_FILE == "custom_prompt.md"

def test_start_command_exception_handling(mock_dependencies):
    mocks = mock_dependencies
    mocks["loop"].side_effect = Exception("Crash Boom")
    
    result = runner.invoke(app, ["start"])
    
    assert result.exit_code == 1
    assert "Fatal Error" in result.stdout
    assert "Crash Boom" in result.stdout

def test_start_self_heal(mock_dependencies):
    mocks = mock_dependencies
    result = runner.invoke(app, ["start", "--self-heal"])
    assert result.exit_code == 0
    assert "Self-Healing Enabled" in result.stdout

def test_start_exception_self_heal(mock_dependencies):
    mocks = mock_dependencies
    mocks["loop"].side_effect = Exception("Crash")
    result = runner.invoke(app, ["start", "--self-heal"])
    assert result.exit_code == 1
    assert "Debugger failed to heal" in result.stdout

def test_dashboard_missing_deps(mock_dependencies, mocker):
    mocker.patch.dict("sys.modules", {"streamlit": None}) # Simulate missing
    # Need to make import fail.
    # mocker.patch.dict doesn't remove from sys.modules if set to None?
    # Better to patch builtins.__import__ or modify sys.modules to raise ImportError?
    # Or just patch sys.modules and ensure 'streamlit' key is missing? 
    # But pytest startup might have loaded it.
    
    # Simpler: patch import statement in dashboard.py? No, it's inside function.
    # Use side_effect on a method that checks for it?
    # The code does `import streamlit`. 
    # If I mock `sys.modules` and REMOVE streamlit from it?
    # mocker.patch.dict("sys.modules") with clear=False?
    # Actually, verify logic: `try: import streamlit`.
    
    # We can use sys.modules to fail import if we map it to None?
    # Python 3.12: setting sys.modules['streamlit'] = None causes ModuleNotFoundError.
    mocker.patch.dict("sys.modules", {"streamlit": None})

    result = runner.invoke(app, ["dashboard"])
    assert result.exit_code == 1
    assert "Dashboard dependencies not found" in result.stdout

def test_auto_fix_target_not_found(mock_dependencies, tmp_path):
    result = runner.invoke(app, ["auto-fix", "nonexistent.py"])
    assert result.exit_code == 1
    assert "Error: Target 'nonexistent.py' not found" in result.stdout

def test_status_command(mock_dependencies):
    mocks = mock_dependencies
    mock_mem_instance = mocks["memory"].return_value
    mock_mem_instance.get_project_state.return_value = {
        "project_name": "Test Project",
        "total_loops": 10
    }
    mock_mem_instance.get_loop_history.return_value = [
        {"loop_id": 1, "status": "SUCCESS"}
    ]
    
    result = runner.invoke(app, ["status"])
    
    assert result.exit_code == 0
    assert "Boring Project Status" in result.stdout
    assert "Test Project" in result.stdout
    assert "Loop #1: SUCCESS" in result.stdout

def test_circuit_commands(mock_dependencies):
    mocks = mock_dependencies
    
    # Status
    runner.invoke(app, ["circuit-status"])
    mocks["show_circuit"].assert_called_once()
    
    # Reset
    result = runner.invoke(app, ["reset-circuit"])
    assert result.exit_code == 0
    mocks["reset_circuit"].assert_called_with("Manual reset via CLI")

def test_setup_extensions(mock_dependencies):
    mocks = mock_dependencies
    
    result = runner.invoke(app, ["setup-extensions"])
    
    assert result.exit_code == 0
    mocks["setup_ext"].assert_called_once()
    mocks["create_ct"].assert_called_once()
    mocks["create_sk"].assert_called_once()

def test_memory_clear_exists(mock_dependencies, tmp_path, mocker):
    # Check logic where directory exists
    mocker.patch("pathlib.Path.exists", return_value=True)
    mock_rmtree = mocker.patch("shutil.rmtree")
    
    result = runner.invoke(app, ["memory-clear"])
    assert result.exit_code == 0
    assert "Memory cleared" in result.stdout
    mock_rmtree.assert_called_once()

def test_memory_clear_not_exists(mock_dependencies, mocker):
    mocker.patch("pathlib.Path.exists", return_value=False)
    result = runner.invoke(app, ["memory-clear"])
    assert result.exit_code == 0
    assert "No memory to clear" in result.stdout

def test_health_check_healthy(mock_dependencies):
    mocks = mock_dependencies
    mocks["print_health"].return_value = True
    
    result = runner.invoke(app, ["health"])
    
    assert result.exit_code == 0
    mocks["health_check"].assert_called_once()

def test_health_check_unhealthy(mock_dependencies):
    mocks = mock_dependencies
    mocks["print_health"].return_value = False
    
    result = runner.invoke(app, ["health"])
    
    assert result.exit_code == 1

def test_version_command(mock_dependencies):
    mocks = mock_dependencies
    mocks["version"].return_value = "1.2.3"
    
    result = runner.invoke(app, ["version"])
    
    assert result.exit_code == 0
    assert "Boring v1.2.3" in result.stdout

def test_version_command_fallback(mock_dependencies):
    mocks = mock_dependencies
    mocks["version"].side_effect = Exception("Not found")
    
    result = runner.invoke(app, ["version"])
    
    assert result.exit_code == 0
    assert "Boring v7.0.0" in result.stdout

# --- Workflow Commands ---

def test_workflow_list(mock_dependencies):
    mocks = mock_dependencies
    mocks["workflow_mgr"].return_value.list_local_workflows.return_value = ["flow1.md"]
    
    result = runner.invoke(app, ["workflow", "list"])
    
    assert result.exit_code == 0
    assert "flow1.md" in result.stdout

def test_workflow_list_empty(mock_dependencies):
    mocks = mock_dependencies
    mocks["workflow_mgr"].return_value.list_local_workflows.return_value = []
    
    result = runner.invoke(app, ["workflow", "list"])
    
    assert result.exit_code == 0
    assert "No workflows found" in result.stdout

def test_workflow_export_success(mock_dependencies):
    mocks = mock_dependencies
    mocks["workflow_mgr"].return_value.export_workflow.return_value = ("path/to.bwf.json", "Success")
    
    result = runner.invoke(app, ["workflow", "export", "my-flow"])
    
    assert result.exit_code == 0
    assert "Exported to" in result.stdout

def test_workflow_export_failure(mock_dependencies):
    mocks = mock_dependencies
    mocks["workflow_mgr"].return_value.export_workflow.return_value = (None, "Failed export")
    
    result = runner.invoke(app, ["workflow", "export", "my-flow"])
    
    assert result.exit_code == 1
    assert "Error: Failed export" in result.stdout

def test_workflow_publish_no_token(mock_dependencies, mocker):
    mocker.patch.dict("os.environ", {}, clear=True)
    result = runner.invoke(app, ["workflow", "publish", "my-flow"])
    assert result.exit_code == 1
    assert "GitHub Token required" in result.stdout

def test_workflow_publish_success(mock_dependencies, mocker):
    mocks = mock_dependencies
    mocks["workflow_mgr"].return_value.publish_workflow.return_value = (True, "Gist URL")
    
    mocker.patch.dict("os.environ", {"GITHUB_TOKEN": "fake-token"})
    result = runner.invoke(app, ["workflow", "publish", "my-flow"])
    assert result.exit_code == 0
    assert "Published Successfully" in result.stdout

def test_workflow_publish_failure(mock_dependencies, mocker):
    mocks = mock_dependencies
    mocks["workflow_mgr"].return_value.publish_workflow.return_value = (False, "API Error")
    
    mocker.patch.dict("os.environ", {"GITHUB_TOKEN": "fake-token"})
    result = runner.invoke(app, ["workflow", "publish", "my-flow"])
    assert result.exit_code == 1
    assert "Publish Failed" in result.stdout

def test_workflow_install_success(mock_dependencies):
    mocks = mock_dependencies
    mocks["workflow_mgr"].return_value.install_workflow.return_value = (True, "Installed!")
    
    result = runner.invoke(app, ["workflow", "install", "source.json"])
    
    assert result.exit_code == 0
    assert "Installed!" in result.stdout

def test_workflow_install_failure(mock_dependencies):
    mocks = mock_dependencies
    mocks["workflow_mgr"].return_value.install_workflow.return_value = (False, "Corrupt file")
    
    result = runner.invoke(app, ["workflow", "install", "source.json"])
    
    assert result.exit_code == 1
    assert "Error: Corrupt file" in result.stdout

# --- Evaluate Command ---

def test_evaluate_file_not_found(mock_dependencies):
    result = runner.invoke(app, ["evaluate", "nonexistent.py"])
    assert result.exit_code == 1
    assert "not found" in result.stdout

def test_evaluate_success_cli(mock_dependencies, tmp_path):
    mocks = mock_dependencies
    target = tmp_path / "test.py"
    target.touch()
    
    mocks["judge"].return_value.grade_code.return_value = {
        "score": 4.5,
        "summary": "Good code",
        "suggestions": ["Add comments"]
    }
    
    result = runner.invoke(app, ["evaluate", str(target), "--backend", "cli"])
    
    assert result.exit_code == 0
    assert "Score: 4.5/5.0" in result.stdout
    assert "Good code" in result.stdout
    assert "Add comments" in result.stdout
    mocks["gemini_cli"].assert_called_once()

def test_evaluate_api_missing_key(mock_dependencies, tmp_path):
    mocks = mock_dependencies
    target = tmp_path / "test.py"
    target.write_text("print('hello')")
    
    mocks["gemini_client"].return_value.is_available = False
    
    result = runner.invoke(app, ["evaluate", str(target), "--backend", "api"])
    
    assert result.exit_code == 1
    assert "API Key not found" in result.stdout

def test_evaluate_exception(mock_dependencies, tmp_path):
    mocks = mock_dependencies
    target = tmp_path / "test.py"
    target.touch()
    
    mocks["judge"].return_value.grade_code.side_effect = Exception("Judge Error")
    
    result = runner.invoke(app, ["evaluate", str(target)])
    
    assert result.exit_code == 1
    assert "Evaluation failed: Judge Error" in result.stdout

# --- Dashboard Command ---
def test_dashboard_success(mock_dependencies, mocker):
    mocks = mock_dependencies
    # Enable streamlit in sys.modules
    mocker.patch.dict("sys.modules", {"streamlit": mocker.MagicMock()})
    
    result = runner.invoke(app, ["dashboard"])
    assert result.exit_code == 0
    mocks["subprocess"].assert_called_once()

def test_dashboard_subprocess_error(mock_dependencies, mocker):
    mocks = mock_dependencies
    mocks["subprocess"].side_effect = Exception("Subprocess failure")
    
    mocker.patch.dict("sys.modules", {"streamlit": mocker.MagicMock()})
    
    result = runner.invoke(app, ["dashboard"])
    assert result.exit_code == 1
    assert "Failed to launch dashboard" in result.stdout

# --- Auto Fix Command ---

def test_auto_fix_success(mock_dependencies, tmp_path):
    mocks = mock_dependencies
    target = tmp_path / "broken.py"
    target.touch()
    
    mocks["autofix"].return_value.run.return_value = {
        "status": "SUCCESS",
        "iterations": 2,
        "message": "Fixed"
    }
    
    result = runner.invoke(app, ["auto-fix", str(target)])
    
    assert result.exit_code == 0
    assert "Optimized successfully" in result.stdout

def test_auto_fix_failure(mock_dependencies, tmp_path):
    mocks = mock_dependencies
    target = tmp_path / "broken.py"
    target.touch()
    
    mocks["autofix"].return_value.run.return_value = {
        "status": "FAILED",
        "message": "Could not fix"
    }
    
    result = runner.invoke(app, ["auto-fix", str(target)])
    
    assert result.exit_code == 0 
    assert "Could not fix" in result.stdout

def test_auto_fix_wrappers_logic(mock_dependencies, tmp_path):
    mocks = mock_dependencies
    target = tmp_path / "test_wrap.py"
    target.touch()
    (tmp_path / ".git").mkdir() 
    
    captured_funcs = {}
    def capture_run(run_func, verify_func):
        captured_funcs["run"] = run_func
        captured_funcs["verify"] = verify_func
        return {"status": "SUCCESS", "iterations": 1}
    
    mocks["autofix"].return_value.run.side_effect = capture_run
    
    runner.invoke(app, ["auto-fix", str(target)])
    
    v_func = captured_funcs["verify"]
    mocks["verifier"].return_value.verify_project.return_value = (False, "Lint error")
    res = v_func("STANDARD", str(tmp_path))
    assert res["passed"] is False
    assert res["issues"] == ["Lint error"]
    
    r_func = captured_funcs["run"]
    mocks["memory"].return_value.get_loop_history.return_value = [{"status": "SUCCESS"}]
    
    res_run = r_func("Fix it", "STANDARD", 2, str(tmp_path))
    assert res_run["status"] == "SUCCESS"

# --- Hooks Commands ---
def test_hooks_install_success(mock_dependencies):
    mocks = mock_dependencies
    mocks["hooks_mgr"].return_value.install_all.return_value = (True, "OK")
    
    result = runner.invoke(app, ["hooks", "install"])
    assert result.exit_code == 0
    assert "Hooks installed" in result.stdout

def test_hooks_install_fail(mock_dependencies):
    mocks = mock_dependencies
    mocks["hooks_mgr"].return_value.install_all.return_value = (False, "Fail")
    
    result = runner.invoke(app, ["hooks", "install"])
    assert result.exit_code == 1

def test_hooks_uninstall_success(mock_dependencies):
    mocks = mock_dependencies
    mocks["hooks_mgr"].return_value.uninstall_all.return_value = (True, "Removed")
    
    result = runner.invoke(app, ["hooks", "uninstall"])
    assert result.exit_code == 0
    assert "Hooks removed" in result.stdout

def test_hooks_status_not_repo(mock_dependencies):
    mocks = mock_dependencies
    mocks["hooks_mgr"].return_value.status.return_value = {"is_git_repo": False}
    
    result = runner.invoke(app, ["hooks", "status"])
    assert result.exit_code == 0
    assert "Not a Git repository" in result.stdout

def test_hooks_status_repo(mock_dependencies):
    mocks = mock_dependencies
    mocks["hooks_mgr"].return_value.status.return_value = {
        "is_git_repo": True,
        "hooks": {
            "pre-commit": {"installed": True, "is_boring_hook": True},
            "pre-push": {"installed": True, "is_boring_hook": False},
            "post-merge": {"installed": False}
        }
    }
    
    result = runner.invoke(app, ["hooks", "status"])
    assert result.exit_code == 0
    assert "Boring hook active" in result.stdout
