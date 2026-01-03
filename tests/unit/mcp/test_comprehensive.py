"""
Comprehensive MCP Tools Test Suite
Achieves 80%+ code coverage for boring.mcp package
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path


# =============================================================================
# SPECKIT TOOLS TESTS
# =============================================================================

class TestSpeckitTools:
    """Comprehensive tests for speckit module."""

    @patch("boring.mcp.tools.speckit.get_project_root_or_error")
    def test_execute_workflow_no_project(self, mock_get_root):
        """Test workflow execution when no project found."""
        from boring.mcp.tools.speckit import _execute_workflow
        mock_get_root.return_value = (None, {"status": "ERROR", "message": "No project"})
        
        result = _execute_workflow("speckit-plan")
        assert result["status"] == "ERROR"
    
    @patch("boring.mcp.tools.speckit.get_project_root_or_error")
    @patch("boring.mcp.tools.speckit.configure_runtime_for_project")
    @patch("boring.mcp.tools.speckit._read_workflow")
    @patch("shutil.which")
    @patch("boring.cli_client.GeminiCLIAdapter")
    def test_execute_workflow_cli_mode(self, mock_cli, mock_which, mock_read, mock_configure, mock_get_root):
        """Test workflow execution using CLI."""
        mock_get_root.return_value = (MagicMock(), None)
        mock_read.return_value = "# Test workflow content"
        mock_which.return_value = "/usr/bin/gemini"
        
        mock_client = MagicMock()
        mock_client.generate_with_retry.return_value = "Result from CLI"
        mock_cli.return_value = mock_client
        
        from boring.mcp.tools.speckit import _execute_workflow
        result = _execute_workflow("speckit-plan", context="Extra context")
        
        assert result["status"] == "SUCCESS"
        assert result["mode"] == "CLI"

    @patch("boring.mcp.tools.speckit.get_project_root_or_error")
    @patch("boring.mcp.tools.speckit.configure_runtime_for_project")
    @patch("boring.mcp.tools.speckit._read_workflow")
    @patch("shutil.which")
    @patch("boring.gemini_client.GeminiClient")
    def test_execute_workflow_sdk_mode(self, mock_sdk, mock_which, mock_read, mock_configure, mock_get_root):
        """Test workflow execution using SDK (no CLI)."""
        mock_get_root.return_value = (MagicMock(), None)
        mock_read.return_value = "# Test workflow"
        mock_which.return_value = None  # No CLI available
        
        mock_client = MagicMock()
        mock_client.generate.return_value = "SDK result"
        mock_sdk.return_value = mock_client
        
        from boring.mcp.tools.speckit import _execute_workflow
        result = _execute_workflow("speckit-tasks")
        
        assert result["status"] == "SUCCESS"
        assert result["mode"] == "SDK"

    @patch("boring.mcp.tools.speckit.get_project_root_or_error")
    @patch("boring.mcp.tools.speckit.configure_runtime_for_project")
    @patch("boring.mcp.tools.speckit._read_workflow")
    @patch("shutil.which")
    def test_execute_workflow_exception(self, mock_which, mock_read, mock_configure, mock_get_root):
        """Test workflow execution handles exceptions."""
        mock_get_root.return_value = (MagicMock(), None)
        mock_read.return_value = "# Workflow"
        mock_which.side_effect = Exception("CLI error")
        
        from boring.mcp.tools.speckit import _execute_workflow
        result = _execute_workflow("speckit-analyze")
        
        assert result["status"] == "ERROR"
        assert "CLI error" in result["error"]

    def test_read_workflow_exists(self, tmp_path):
        """Test reading existing workflow file."""
        from boring.mcp.tools.speckit import _read_workflow
        
        workflow_dir = tmp_path / ".agent" / "workflows"
        workflow_dir.mkdir(parents=True)
        (workflow_dir / "test-workflow.md").write_text("# Test content", encoding="utf-8")
        
        result = _read_workflow("test-workflow", tmp_path)
        assert "Test content" in result

    def test_read_workflow_not_exists(self, tmp_path):
        """Test reading non-existent workflow file."""
        from boring.mcp.tools.speckit import _read_workflow
        
        result = _read_workflow("missing-workflow", tmp_path)
        assert "not found" in result

    @patch("boring.mcp.tools.speckit._execute_workflow")
    def test_speckit_plan(self, mock_execute):
        """Test speckit_plan delegates to _execute_workflow."""
        from boring.mcp.tools.speckit import speckit_plan
        mock_execute.return_value = {"status": "SUCCESS"}
        
        result = speckit_plan(context="test")
        mock_execute.assert_called_with("speckit-plan", "test", None)

    @patch("boring.mcp.tools.speckit._execute_workflow")
    def test_speckit_tasks(self, mock_execute):
        """Test speckit_tasks delegates correctly."""
        from boring.mcp.tools.speckit import speckit_tasks
        mock_execute.return_value = {"status": "SUCCESS"}
        
        speckit_tasks()
        mock_execute.assert_called_with("speckit-tasks", None, None)

    @patch("boring.mcp.tools.speckit._execute_workflow")
    def test_speckit_analyze(self, mock_execute):
        """Test speckit_analyze delegates correctly."""
        from boring.mcp.tools.speckit import speckit_analyze
        mock_execute.return_value = {"status": "SUCCESS"}
        
        speckit_analyze("context", "/path")
        mock_execute.assert_called_with("speckit-analyze", "context", "/path")

    @patch("boring.mcp.tools.speckit._execute_workflow")
    def test_speckit_clarify(self, mock_execute):
        """Test speckit_clarify delegates correctly."""
        from boring.mcp.tools.speckit import speckit_clarify
        mock_execute.return_value = {"status": "SUCCESS"}
        
        speckit_clarify()
        mock_execute.assert_called_with("speckit-clarify", None, None)

    @patch("boring.mcp.tools.speckit._execute_workflow")
    def test_speckit_constitution(self, mock_execute):
        """Test speckit_constitution delegates correctly."""
        from boring.mcp.tools.speckit import speckit_constitution
        mock_execute.return_value = {"status": "SUCCESS"}
        
        speckit_constitution()
        mock_execute.assert_called_with("speckit-constitution", None, None)

    @patch("boring.mcp.tools.speckit._execute_workflow")
    def test_speckit_checklist(self, mock_execute):
        """Test speckit_checklist delegates correctly."""
        from boring.mcp.tools.speckit import speckit_checklist
        mock_execute.return_value = {"status": "SUCCESS"}
        
        speckit_checklist()
        mock_execute.assert_called_with("speckit-checklist", None, None)


# =============================================================================
# KNOWLEDGE TOOLS TESTS
# =============================================================================

class TestKnowledgeTools:
    """Comprehensive tests for knowledge module."""

    @patch("boring.mcp.tools.knowledge.get_project_root_or_error")
    def test_boring_learn_no_project(self, mock_get_root):
        """Test boring_learn when no project found."""
        from boring.mcp.tools.knowledge import boring_learn
        mock_get_root.return_value = (None, {"status": "ERROR"})
        
        result = boring_learn()
        assert result["status"] == "ERROR"

    @patch("boring.mcp.tools.knowledge.get_project_root_or_error")
    @patch("boring.mcp.tools.knowledge.configure_runtime_for_project")
    @patch("boring.brain_manager.BrainManager")
    @patch("boring.storage.SQLiteStorage")
    def test_boring_learn_success(self, mock_storage, mock_brain_cls, mock_configure, mock_get_root):
        """Test successful learning."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_brain = MagicMock()
        mock_brain.learn_from_memory.return_value = {"patterns_learned": 5}
        mock_brain_cls.return_value = mock_brain
        
        from boring.mcp.tools.knowledge import boring_learn
        result = boring_learn()
        
        assert result["patterns_learned"] == 5

    @patch("boring.mcp.tools.knowledge.get_project_root_or_error")
    @patch("boring.mcp.tools.knowledge.configure_runtime_for_project")
    def test_boring_learn_exception(self, mock_configure, mock_get_root):
        """Test boring_learn handles exceptions."""
        mock_get_root.return_value = (MagicMock(), None)
        mock_configure.side_effect = Exception("Config error")
        
        from boring.mcp.tools.knowledge import boring_learn
        result = boring_learn()
        
        assert result["status"] == "ERROR"
        assert "Config error" in result["error"]

    @patch("boring.mcp.tools.knowledge.get_project_root_or_error")
    @patch("boring.mcp.tools.knowledge.configure_runtime_for_project")
    @patch("boring.brain_manager.BrainManager")
    def test_boring_create_rubrics_success(self, mock_brain_cls, mock_configure, mock_get_root):
        """Test successful rubric creation."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_brain = MagicMock()
        mock_brain.create_default_rubrics.return_value = {"rubrics_created": ["code_quality"]}
        mock_brain_cls.return_value = mock_brain
        
        from boring.mcp.tools.knowledge import boring_create_rubrics
        result = boring_create_rubrics()
        
        assert "rubrics_created" in result

    @patch("boring.mcp.tools.knowledge.get_project_root_or_error")
    def test_boring_create_rubrics_no_project(self, mock_get_root):
        """Test rubric creation when no project."""
        from boring.mcp.tools.knowledge import boring_create_rubrics
        mock_get_root.return_value = (None, {"status": "ERROR"})
        
        result = boring_create_rubrics()
        assert result["status"] == "ERROR"

    @patch("boring.mcp.tools.knowledge.get_project_root_or_error")
    @patch("boring.mcp.tools.knowledge.configure_runtime_for_project")
    @patch("boring.brain_manager.BrainManager")
    def test_boring_brain_summary_success(self, mock_brain_cls, mock_configure, mock_get_root):
        """Test brain summary retrieval."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_brain = MagicMock()
        mock_brain.get_brain_summary.return_value = {"patterns": 10, "rubrics": 3}
        mock_brain_cls.return_value = mock_brain
        
        from boring.mcp.tools.knowledge import boring_brain_summary
        result = boring_brain_summary()
        
        assert result["patterns"] == 10

    @patch("boring.mcp.tools.knowledge.get_project_root_or_error")
    @patch("boring.mcp.tools.knowledge.configure_runtime_for_project")
    def test_boring_brain_summary_exception(self, mock_configure, mock_get_root):
        """Test brain summary handles exceptions."""
        mock_get_root.return_value = (MagicMock(), None)
        mock_configure.side_effect = Exception("Summary error")
        
        from boring.mcp.tools.knowledge import boring_brain_summary
        result = boring_brain_summary()
        
        assert result["status"] == "ERROR"


# =============================================================================
# INTEGRATION TOOLS TESTS 
# =============================================================================

class TestIntegrationTools:
    """Comprehensive tests for integration module."""

    @patch("boring.mcp.tools.integration.get_project_root_or_error")
    def test_setup_extensions_no_project(self, mock_get_root):
        """Test setup_extensions when no project."""
        from boring.mcp.tools.integration import boring_setup_extensions
        mock_get_root.return_value = (None, {"status": "ERROR"})
        
        result = boring_setup_extensions()
        assert result["status"] == "ERROR"

    @patch("boring.mcp.tools.integration.get_project_root_or_error")
    @patch("boring.extensions.ExtensionsManager")
    def test_setup_extensions_no_gemini(self, mock_ext_cls, mock_get_root):
        """Test setup_extensions when no Gemini CLI."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_manager = MagicMock()
        mock_manager.is_gemini_available.return_value = False
        mock_ext_cls.return_value = mock_manager
        
        from boring.mcp.tools.integration import boring_setup_extensions
        result = boring_setup_extensions()
        
        assert result["status"] == "SKIPPED"
        assert "not found" in result["message"]

    @patch("boring.mcp.tools.integration.get_project_root_or_error")
    @patch("boring.extensions.ExtensionsManager")
    def test_setup_extensions_success(self, mock_ext_cls, mock_get_root):
        """Test successful extension setup."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_manager = MagicMock()
        mock_manager.is_gemini_available.return_value = True
        mock_manager.install_recommended_extensions.return_value = {
            "context7": (True, "Installed"),
            "criticalthink": (False, "Already exists")
        }
        mock_ext_cls.return_value = mock_manager
        
        from boring.mcp.tools.integration import boring_setup_extensions
        result = boring_setup_extensions()
        
        assert result["status"] == "SUCCESS"
        assert "context7" in result["installed"]
        assert "criticalthink" in result["failed"]

    @patch("boring.mcp.tools.integration.get_project_root_or_error")
    def test_setup_extensions_exception(self, mock_get_root):
        """Test setup_extensions handles exceptions."""
        mock_get_root.side_effect = Exception("Setup error")
        
        from boring.mcp.tools.integration import boring_setup_extensions
        result = boring_setup_extensions()
        
        assert result["status"] == "ERROR"
        assert "Setup error" in result["error"]

    def test_notebooklm_guide(self):
        """Test NotebookLM guide returns instructions."""
        from boring.mcp.tools.integration import boring_notebooklm_guide
        
        result = boring_notebooklm_guide()
        
        assert "NotebookLM" in result
        assert "setup_auth" in result
        assert "npx" in result


# =============================================================================
# VERIFICATION TOOLS TESTS
# =============================================================================

class TestVerificationTools:
    """Comprehensive tests for verification module."""

    @patch("boring.mcp.tools.verification.get_project_root_or_error")
    def test_boring_verify_no_project(self, mock_get_root):
        """Test verify when no project."""
        from boring.mcp.tools.verification import boring_verify
        mock_get_root.return_value = (None, {"status": "ERROR"})
        
        result = boring_verify()
        assert result["status"] == "ERROR"

    @patch("boring.mcp.tools.verification.get_project_root_or_error")
    @patch("boring.mcp.tools.verification.configure_runtime_for_project")
    @patch("boring.verification.CodeVerifier")
    def test_boring_verify_success(self, mock_verifier_cls, mock_configure, mock_get_root):
        """Test successful verification."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_verifier = MagicMock()
        mock_verifier.verify.return_value = MagicMock(
            passed=True,
            errors=[],
            warnings=["Minor warning"]
        )
        mock_verifier_cls.return_value = mock_verifier
        
        from boring.mcp.tools.verification import boring_verify
        result = boring_verify(level="STANDARD")
        
        assert result["status"] == "SUCCESS"

    @patch("boring.mcp.tools.verification.get_project_root_or_error")
    @patch("boring.mcp.tools.verification.configure_runtime_for_project")
    @patch("boring.verification.CodeVerifier")
    def test_boring_verify_failure(self, mock_verifier_cls, mock_configure, mock_get_root):
        """Test verification with failures."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_verifier = MagicMock()
        mock_verifier.verify.return_value = MagicMock(
            passed=False,
            errors=[{"file": "test.py", "message": "Syntax error"}],
            warnings=[]
        )
        mock_verifier_cls.return_value = mock_verifier
        
        from boring.mcp.tools.verification import boring_verify
        result = boring_verify()
        
        assert result["status"] == "FAILURE"

    @patch("boring.mcp.tools.verification.get_project_root_or_error")
    @patch("boring.mcp.tools.verification.configure_runtime_for_project")
    def test_boring_verify_exception(self, mock_configure, mock_get_root):
        """Test verify handles exceptions."""
        mock_get_root.return_value = (MagicMock(), None)
        mock_configure.side_effect = Exception("Verify error")
        
        from boring.mcp.tools.verification import boring_verify
        result = boring_verify()
        
        assert result["status"] == "ERROR"

    @patch("boring.mcp.tools.verification.get_project_root_or_error")
    @patch("boring.mcp.tools.verification.configure_runtime_for_project")
    @patch("boring.verification.CodeVerifier")
    def test_boring_verify_file_success(self, mock_verifier_cls, mock_configure, mock_get_root):
        """Test single file verification."""
        mock_root = MagicMock()
        mock_get_root.return_value = (mock_root, None)
        
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_root.__truediv__.return_value = mock_file
        
        mock_verifier = MagicMock()
        mock_verifier.verify_file.return_value = {"passed": True}
        mock_verifier_cls.return_value = mock_verifier
        
        from boring.mcp.tools.verification import boring_verify_file
        result = boring_verify_file("test.py")
        
        assert result["passed"] == True

    @patch("boring.mcp.tools.verification.get_project_root_or_error")
    @patch("boring.mcp.tools.verification.configure_runtime_for_project")
    def test_boring_verify_file_not_found(self, mock_configure, mock_get_root):
        """Test file verification when file not found."""
        mock_root = MagicMock()
        mock_get_root.return_value = (mock_root, None)
        
        mock_file = MagicMock()
        mock_file.exists.return_value = False
        mock_root.__truediv__.return_value = mock_file
        
        from boring.mcp.tools.verification import boring_verify_file
        result = boring_verify_file("missing.py")
        
        assert result["status"] == "ERROR"
        assert "not found" in result["error"]


# =============================================================================
# WORKFLOW TOOLS TESTS
# =============================================================================

class TestWorkflowTools:
    """Comprehensive tests for workflow module."""

    @patch("boring.mcp.tools.workflow.get_project_root_or_error")
    def test_evolve_workflow_no_project(self, mock_get_root):
        """Test evolve workflow when no project."""
        from boring.mcp.tools.workflow import speckit_evolve_workflow
        mock_get_root.return_value = (None, {"status": "ERROR"})
        
        result = speckit_evolve_workflow("test", "content", "reason")
        assert result["status"] == "ERROR"

    @patch("boring.mcp.tools.workflow.get_project_root_or_error")
    @patch("boring.mcp.tools.workflow.configure_runtime_for_project")
    @patch("boring.workflow_evolver.WorkflowEvolver")
    def test_evolve_workflow_success(self, mock_evolver_cls, mock_configure, mock_get_root):
        """Test successful workflow evolution."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_evolver = MagicMock()
        mock_evolver.evolve.return_value = {"status": "SUCCESS", "old_hash": "abc", "new_hash": "def"}
        mock_evolver_cls.return_value = mock_evolver
        
        from boring.mcp.tools.workflow import speckit_evolve_workflow
        result = speckit_evolve_workflow("speckit-plan", "new content", "improve quality")
        
        assert result["status"] == "SUCCESS"

    @patch("boring.mcp.tools.workflow.get_project_root_or_error")
    @patch("boring.mcp.tools.workflow.configure_runtime_for_project")
    @patch("boring.workflow_evolver.WorkflowEvolver")
    def test_reset_workflow_success(self, mock_evolver_cls, mock_configure, mock_get_root):
        """Test workflow reset."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_evolver = MagicMock()
        mock_evolver.reset.return_value = {"status": "SUCCESS"}
        mock_evolver_cls.return_value = mock_evolver
        
        from boring.mcp.tools.workflow import speckit_reset_workflow
        result = speckit_reset_workflow("speckit-plan")
        
        assert result["status"] == "SUCCESS"

    @patch("boring.mcp.tools.workflow.get_project_root_or_error")
    @patch("boring.mcp.tools.workflow.configure_runtime_for_project")
    @patch("boring.workflow_evolver.WorkflowEvolver")
    def test_workflow_status(self, mock_evolver_cls, mock_configure, mock_get_root):
        """Test workflow status check."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_evolver = MagicMock()
        mock_evolver.get_status.return_value = {"evolved": True, "current_hash": "xyz"}
        mock_evolver_cls.return_value = mock_evolver
        
        from boring.mcp.tools.workflow import speckit_workflow_status
        result = speckit_workflow_status("speckit-plan")
        
        assert result["evolved"] == True

    @patch("boring.mcp.tools.workflow.get_project_root_or_error")
    @patch("boring.mcp.tools.workflow.configure_runtime_for_project")
    @patch("boring.workflow_evolver.WorkflowEvolver")
    def test_backup_workflows(self, mock_evolver_cls, mock_configure, mock_get_root):
        """Test workflow backup."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_evolver = MagicMock()
        mock_evolver.backup_all.return_value = {"backed_up": 6}
        mock_evolver_cls.return_value = mock_evolver
        
        from boring.mcp.tools.workflow import speckit_backup_workflows
        result = speckit_backup_workflows()
        
        assert result["backed_up"] == 6

    @patch("boring.mcp.tools.workflow.get_project_root_or_error")
    @patch("boring.workflow_manager.WorkflowManager")
    def test_list_workflows(self, mock_wf_cls, mock_get_root):
        """Test listing workflows."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_manager = MagicMock()
        mock_manager.list_workflows.return_value = [
            {"name": "speckit-plan", "description": "Planning workflow"}
        ]
        mock_wf_cls.return_value = mock_manager
        
        from boring.mcp.tools.workflow import boring_list_workflows
        result = boring_list_workflows()
        
        assert len(result["workflows"]) == 1

    @patch("boring.mcp.tools.workflow.get_project_root_or_error")
    @patch("boring.workflow_manager.WorkflowManager")
    def test_install_workflow(self, mock_wf_cls, mock_get_root):
        """Test installing workflow from URL."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_manager = MagicMock()
        mock_manager.install_from_url.return_value = {"status": "INSTALLED", "name": "custom-workflow"}
        mock_wf_cls.return_value = mock_manager
        
        from boring.mcp.tools.workflow import boring_install_workflow
        result = boring_install_workflow("https://example.com/workflow.bwf.json")
        
        assert result["status"] == "INSTALLED"


# =============================================================================
# EVALUATION TOOLS TESTS
# =============================================================================

class TestEvaluationTools:
    """Tests for evaluation module."""

    @patch("boring.mcp.tools.evaluation.check_rate_limit")
    def test_boring_evaluate_rate_limited(self, mock_rate_limit):
        """Test evaluation when rate limited."""
        from boring.mcp.tools.evaluation import boring_evaluate
        mock_rate_limit.return_value = (False, "Rate limit exceeded")
        
        result = boring_evaluate("test.py")
        assert result["status"] == "RATE_LIMITED"

    @patch("boring.mcp.tools.evaluation.check_rate_limit")
    @patch("boring.mcp.tools.evaluation.get_project_root_or_error")
    @patch("boring.mcp.tools.evaluation.configure_runtime_for_project")
    @patch("boring.llm_judge.LLMJudge")
    def test_boring_evaluate_success(self, mock_judge_cls, mock_configure, mock_get_root, mock_rate_limit):
        """Test successful evaluation."""
        mock_rate_limit.return_value = (True, "")
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_judge = MagicMock()
        mock_judge.evaluate.return_value = {"score": 8, "reasoning": "Good code"}
        mock_judge_cls.return_value = mock_judge
        
        from boring.mcp.tools.evaluation import boring_evaluate
        result = boring_evaluate("test.py")
        
        assert result["score"] == 8

    @patch("boring.mcp.tools.evaluation.check_rate_limit")
    @patch("boring.mcp.tools.evaluation.get_project_root_or_error")
    def test_boring_evaluate_no_project(self, mock_get_root, mock_rate_limit):
        """Test evaluation when no project."""
        mock_rate_limit.return_value = (True, "")
        mock_get_root.return_value = (None, {"status": "ERROR"})
        
        from boring.mcp.tools.evaluation import boring_evaluate
        result = boring_evaluate("test.py")
        
        assert result["status"] == "ERROR"


# =============================================================================
# PATCHING TOOLS TESTS
# =============================================================================

class TestPatchingToolsComprehensive:
    """Additional comprehensive tests for patching module."""

    @patch("boring.mcp.tools.patching.get_project_root_or_error")
    @patch("boring.mcp.tools.patching.configure_runtime_for_project")
    def test_apply_patch_search_not_found(self, mock_configure, mock_get_root):
        """Test patch when search text not found."""
        mock_root = MagicMock()
        mock_get_root.return_value = (mock_root, None)
        
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = "def foo(): pass"
        mock_root.__truediv__.return_value = mock_file
        
        from boring.mcp.tools.patching import boring_apply_patch
        result = boring_apply_patch("test.py", "def bar():", "def baz():")
        
        assert result["status"] == "ERROR"
        assert "not found" in result["error"]

    @patch("boring.mcp.tools.patching.get_project_root_or_error")
    @patch("boring.mcp.tools.patching.configure_runtime_for_project")
    def test_apply_patch_ambiguous_match(self, mock_configure, mock_get_root):
        """Test patch when search text appears multiple times."""
        mock_root = MagicMock()
        mock_get_root.return_value = (mock_root, None)
        
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = "pass\npass\npass"
        mock_root.__truediv__.return_value = mock_file
        
        from boring.mcp.tools.patching import boring_apply_patch
        result = boring_apply_patch("test.py", "pass", "done")
        
        assert result["status"] == "ERROR"
        assert "Ambiguous" in result["error"]

    @patch("boring.mcp.tools.patching.get_project_root_or_error")
    def test_apply_patch_no_project(self, mock_get_root):
        """Test patch when no project."""
        from boring.mcp.tools.patching import boring_apply_patch
        mock_get_root.return_value = (None, {"status": "ERROR"})
        
        result = boring_apply_patch("test.py", "old", "new")
        assert result["status"] == "ERROR"

    @patch("boring.mcp.tools.patching.get_project_root_or_error")
    @patch("boring.mcp.tools.patching.configure_runtime_for_project")
    @patch("boring.diff_patcher.extract_search_replace_blocks")
    def test_extract_patches_no_patches(self, mock_extract, mock_configure, mock_get_root):
        """Test extract patches when no patches found."""
        mock_get_root.return_value = (MagicMock(), None)
        mock_extract.return_value = []
        
        from boring.mcp.tools.patching import boring_extract_patches
        result = boring_extract_patches("AI output without patches")
        
        assert result["status"] == "NO_PATCHES_FOUND"


# =============================================================================
# GIT TOOLS TESTS
# =============================================================================

class TestGitToolsComprehensive:
    """Additional tests for git module."""

    @patch("boring.mcp.tools.git.get_project_root_or_error")
    def test_hooks_install_no_project(self, mock_get_root):
        """Test hooks install when no project."""
        from boring.mcp.tools.git import boring_hooks_install
        mock_get_root.return_value = (None, {"status": "ERROR"})
        
        result = boring_hooks_install()
        assert result["status"] == "ERROR"

    @patch("boring.mcp.tools.git.get_project_root_or_error")
    @patch("boring.mcp.tools.git.configure_runtime_for_project")
    @patch("boring.hooks.HooksManager")
    def test_hooks_install_failure(self, mock_hooks_cls, mock_configure, mock_get_root):
        """Test hooks install failure."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_manager = MagicMock()
        mock_manager.status.return_value = {"is_git_repo": True, "hooks": {}}
        mock_manager.install_all.return_value = (False, "Git not initialized")
        mock_hooks_cls.return_value = mock_manager
        
        from boring.mcp.tools.git import boring_hooks_install
        result = boring_hooks_install()
        
        assert result["status"] == "ERROR"

    @patch("boring.mcp.tools.git.get_project_root_or_error")
    @patch("boring.mcp.tools.git.configure_runtime_for_project")
    def test_hooks_install_exception(self, mock_configure, mock_get_root):
        """Test hooks install handles exceptions."""
        mock_get_root.return_value = (MagicMock(), None)
        mock_configure.side_effect = Exception("Hook error")
        
        from boring.mcp.tools.git import boring_hooks_install
        result = boring_hooks_install()
        
        assert result["status"] == "ERROR"
        assert "Hook error" in result["error"]

    @patch("boring.mcp.tools.git.get_project_root_or_error")
    @patch("boring.mcp.tools.git.configure_runtime_for_project")
    @patch("boring.hooks.HooksManager")
    def test_hooks_uninstall_failure(self, mock_hooks_cls, mock_configure, mock_get_root):
        """Test hooks uninstall failure."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_manager = MagicMock()
        mock_manager.uninstall_all.return_value = (False, "No hooks to remove")
        mock_hooks_cls.return_value = mock_manager
        
        from boring.mcp.tools.git import boring_hooks_uninstall
        result = boring_hooks_uninstall()
        
        assert result["status"] == "ERROR"

    @patch("boring.mcp.tools.git.get_project_root_or_error")
    @patch("boring.mcp.tools.git.configure_runtime_for_project")
    def test_hooks_status_exception(self, mock_configure, mock_get_root):
        """Test hooks status handles exceptions."""
        mock_get_root.return_value = (MagicMock(), None)
        mock_configure.side_effect = Exception("Status error")
        
        from boring.mcp.tools.git import boring_hooks_status
        result = boring_hooks_status()
        
        assert result["status"] == "ERROR"


# =============================================================================
# UTILS TESTS
# =============================================================================

class TestUtils:
    """Tests for MCP utils module."""

    @patch("boring.mcp.utils.detect_project_root")
    def test_get_project_root_or_error_with_path(self, mock_detect):
        """Test get_project_root with explicit path."""
        from boring.mcp.utils import get_project_root_or_error
        
        result, error = get_project_root_or_error("/explicit/path")
        
        assert result == Path("/explicit/path")
        assert error is None
        mock_detect.assert_not_called()

    @patch("boring.mcp.utils.detect_project_root")
    def test_get_project_root_or_error_auto_detect(self, mock_detect):
        """Test get_project_root with auto-detection."""
        from boring.mcp.utils import get_project_root_or_error
        
        mock_detect.return_value = Path("/detected/path")
        
        result, error = get_project_root_or_error(None)
        
        assert result == Path("/detected/path")
        mock_detect.assert_called_once()

    @patch("boring.mcp.utils.detect_project_root")
    def test_get_project_root_or_error_not_found(self, mock_detect):
        """Test get_project_root when not found."""
        from boring.mcp.utils import get_project_root_or_error
        
        mock_detect.return_value = None
        
        result, error = get_project_root_or_error(None)
        
        assert result is None
        assert error["status"] == "ERROR"

    def test_check_rate_limit_allowed(self):
        """Test rate limit when allowed."""
        from boring.mcp.utils import check_rate_limit
        
        # Should always allow by default
        allowed, msg = check_rate_limit("test_operation")
        assert allowed == True

    def test_configure_runtime_for_project(self):
        """Test runtime configuration."""
        from boring.mcp.utils import configure_runtime_for_project
        
        # Should not raise
        configure_runtime_for_project(Path("/test/path"))
