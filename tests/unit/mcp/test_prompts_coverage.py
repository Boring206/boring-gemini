
from unittest.mock import MagicMock

from boring.mcp.prompts import register_prompts


def test_prompts_coverage():
    mock_mcp = MagicMock()
    captured_prompts = {}

    def prompt_decorator(name, description):
        def wrapper(func):
            captured_prompts[name] = func
            return func
        return wrapper

    mock_mcp.prompt = MagicMock(side_effect=prompt_decorator)

    # Exectute registration
    register_prompts(mock_mcp)

    # --- verify registrations ---
    assert len(captured_prompts) > 10
    assert "plan_feature" in captured_prompts
    assert "review_code" in captured_prompts
    assert "setup_project" in captured_prompts
    assert "vibe_start" in captured_prompts

    # --- verify prompt contents ---

    # 1. plan_feature
    res = captured_prompts["plan_feature"](feature="Dark Mode")
    assert "Dark Mode" in res
    assert "Files to create/modify" in res

    # 2. review_code
    res = captured_prompts["review_code"](file_path="src/main.py")
    assert "src/main.py" in res
    assert "Chief Architect" in res

    # 3. debug_error
    res = captured_prompts["debug_error"](error_message="segfault")
    assert "segfault" in res
    assert "Root Cause" in res

    # 4. refactor_code
    res = captured_prompts["refactor_code"](target="users.py")
    assert "users.py" in res
    assert "Testability" in res

    # 5. explain_code
    res = captured_prompts["explain_code"](code_path="logic.ts")
    assert "logic.ts" in res
    assert "Purpose and responsibility" in res

    # 6. setup_project
    res = captured_prompts["setup_project"]()
    assert "boring_quickstart" in res

    # 7. verify_work
    res = captured_prompts["verify_work"](level="FULL")
    assert "boring_verify(level='FULL')" in res

    # 8. manage_memory
    res = captured_prompts["manage_memory"]()
    assert "boring_learn" in res

    # 9. evaluate_architecture
    res = captured_prompts["evaluate_architecture"](target="core/")
    assert "core/" in res
    assert "Architecture Smells" in res or "Scalability" in res

    # 10. run_agent
    res = captured_prompts["run_agent"](task="build API")
    assert "build API" in res
    assert "boring_multi_agent" in res

    # 11. vibe_start
    res = captured_prompts["vibe_start"](idea="CRM")
    assert "CRM" in res
    assert "Phase 1" in res or "Phase 1" in res.replace("**", "")

    # 12. quick_fix
    res = captured_prompts["quick_fix"](target="tests/")
    assert "tests/" in res
    assert "boring_prompt_fix" in res

    # 13. full_stack_dev
    res = captured_prompts["full_stack_dev"](app_name="Shop", stack="LAMP")
    assert "Shop" in res
    assert "LAMP" in res
    assert "Phase 3" in res or "Phase 3" in res.replace("**", "")

    # 14. security_scan
    res = captured_prompts["security_scan"](target="secrets.env")
    assert "secrets.env" in res
    assert "scan_type='secrets'" in res

    # 15. shadow_review
    res = captured_prompts["shadow_review"]()
    assert "boring_shadow_approve" in res

    # 16. semantic_search
    res = captured_prompts["semantic_search"](query="login")
    assert "query='login'" in res

    # 17. save_session / load_session
    assert "my_session" in captured_prompts["save_session"](name="my_session")
    assert "my_session" in captured_prompts["load_session"](name="my_session")

    # 18. safe_refactor / rollback
    res = captured_prompts["safe_refactor"](target="utils.py", description="cleanup")
    assert "utils.py" in res
    assert "cleanup" in res
    assert "boring_transaction_start" in res

    assert "boring_rollback" in captured_prompts["rollback"]()

    # 19. background tasks
    assert "FULL" in captured_prompts["background_verify"](level="FULL")
    assert "boring_background_task" in captured_prompts["background_test"]()

    # 20. smart_commit
    res = captured_prompts["smart_commit"](message="feat: new", push=True)
    assert "feat: new" in res
    assert "push=True" in res or "True" in res # Depending on exact formatting

    # 21. project/plugin/eval prompts
    assert "boring_workspace_switch" in captured_prompts["switch_project"]()
    assert "boring_workspace_add" in captured_prompts["add_project"]()
    assert "boring_run_plugin" in captured_prompts["run_plugin"]()
    assert ".boring_plugins/" in captured_prompts["create_plugin"](name="foo")

    # 22. analyze_error_context
    res = captured_prompts["analyze_error_context"](
        error_type="ValError",
        error_line=99,
        code_context="def foo():\n  pass",
        stack_trace="Traceback..."
    )
    assert "`ValError`" in res
    assert "Line**: 99" in res
    assert "def foo():" in res
    assert "Traceback..." in res
