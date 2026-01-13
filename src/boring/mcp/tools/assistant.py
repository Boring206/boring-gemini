# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
AI Assistant Tools - AI 助手工具。

包含:
- boring_prompt_fix: 自動修復程式碼問題
- boring_suggest_next: 建議下一步操作
- boring_get_progress: 查看任務進度

移植自 v9_tools.py (V10.26.0)

Performance optimizations:
- Concurrent execution for independent I/O operations
- ThreadPoolExecutor for parallel checks
"""

import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Annotated, Any, Optional

from pydantic import Field

from ...intelligence.pattern_mining import get_pattern_miner
from ...streaming import get_streaming_manager
from ...verification import CodeVerifier


# =============================================================================
# Performance: Parallel helper functions for boring_suggest_next
# =============================================================================
def _check_git_changes(project_root: Path) -> list[dict[str, Any]]:
    """Check for uncommitted git changes (runs in thread)."""
    enhancements = []
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=3,
            stdin=subprocess.DEVNULL,
        )
        changed_files = result.stdout.strip().split("\n") if result.stdout.strip() else []
        if changed_files:
            enhancements.append(
                {
                    "type": "git_changes",
                    "action": "Consider running `boring_commit` or `boring_verify`",
                    "priority": "high",
                    "details": f"{len(changed_files)} uncommitted files",
                }
            )
            enhancements.append(
                {
                    "type": "prompt_recommendation",
                    "action": "Run `/smart_commit` to auto-generate message and save",
                    "priority": "high",
                    "details": "High-level prompt available",
                }
            )
    except Exception:
        pass
    return enhancements


def _check_learned_patterns(args: tuple[Path, Optional[str]]) -> list[dict[str, Any]]:
    """Check learned patterns from brain (runs in thread)."""
    project_root, error_message = args
    enhancements = []
    try:
        from ...intelligence.brain_manager import BrainManager

        brain = BrainManager(project_root)

        # V10.32: Reflexive Retrieval
        # If error_message is provided, search for THAT specific error.
        # Otherwise, search for generic next steps.
        query = error_message if error_message else "next steps recommendations"
        limit = 5 if error_message else 3

        patterns = brain.get_relevant_patterns(query, limit=limit)

        for p in patterns:
            # Calculate relevance label
            if error_message:
                label = "💡 Proven Fix"
                priority = "critical"
            else:
                label = "🧠 Learned Pattern"
                priority = "medium"

            enhancements.append(
                {
                    "type": "learned_pattern",
                    "action": p.get("solution", "")[:100],
                    "priority": priority,
                    "details": f"{label}: {p.get('description', 'Unknown')}",
                    "confidence": p.get("success_count", 0),
                }
            )
    except Exception:
        pass
    return enhancements


def _check_rag_index(project_root: Path) -> list[dict[str, Any]]:
    """Check RAG index freshness (runs in thread)."""
    enhancements = []
    try:
        rag_dir = project_root / ".boring_memory" / "rag_db"
        if not rag_dir.exists():
            enhancements.append(
                {
                    "type": "rag_not_indexed",
                    "action": "Run `boring_rag_index` to enable semantic code search",
                    "priority": "medium",
                    "details": "RAG index not found",
                }
            )
    except Exception:
        pass
    return enhancements


def _check_task_progress(project_root: Path) -> list[dict[str, Any]]:
    """Check task.md for incomplete items (runs in thread)."""
    enhancements = []
    try:
        task_file = project_root / ".agent" / "workflows" / "task.md"
        if not task_file.exists():
            task_file = project_root / "task.md"
        if task_file.exists():
            content = task_file.read_text(encoding="utf-8")
            incomplete = content.count("[ ]")
            in_progress = content.count("[/]")
            if incomplete > 0 or in_progress > 0:
                enhancements.append(
                    {
                        "type": "task_progress",
                        "action": f"Continue working on task.md ({in_progress} in progress, {incomplete} remaining)",
                        "priority": "high",
                        "details": "Found incomplete tasks",
                    }
                )
    except Exception:
        pass
    return enhancements


def _check_project_context(project_root: Path) -> list[dict[str, Any]]:
    """Check project context for missing setup steps (Action 1: Smart Suggestions)."""
    enhancements = []
    try:
        from ..utils import detect_context_capabilities

        context = detect_context_capabilities(project_root)

        # 1. Missing Git
        if not context["has_git"]:
            enhancements.append(
                {
                    "type": "context_missing_setup",
                    "action": "Initialize Git Repository (`git init`)",
                    "priority": "critical",
                    "details": "No version control detected",
                }
            )

        # 2. Missing Node Dependencies
        if context["has_node"] and not context["has_node_modules"]:
            enhancements.append(
                {
                    "type": "context_missing_setup",
                    "action": "Install Dependencies (`npm install` or `pnpm install`)",
                    "priority": "high",
                    "details": "package.json exists but node_modules is missing",
                }
            )

        # 3. Missing Python Environment
        if context["has_python"] and not context["has_venv"]:
            enhancements.append(
                {
                    "type": "context_missing_setup",
                    "action": "Setup Virtual Environment (`python -m venv venv`)",
                    "priority": "medium",
                    "details": "Python project detected but no venv found",
                }
            )

    except Exception:
        pass
    return enhancements


def _check_project_empty(project_root: Path) -> list[dict[str, Any]]:
    """Check if project appears empty (runs in thread)."""
    enhancements = []
    try:
        src_dir = project_root / "src"
        if not src_dir.exists() or not any(src_dir.iterdir()):
            enhancements.append(
                {
                    "type": "prompt_recommendation",
                    "action": "Run `/vibe_start` to kickstart development",
                    "priority": "critical",
                    "details": "Project appears empty",
                }
            )
    except Exception:
        pass
    return enhancements


def register_assistant_tools(mcp, audited, helpers: dict[str, Any]) -> int:
    """
    Register AI assistant tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        audited: Audit decorator
        helpers: Dict of helper functions

    Returns:
        Number of tools registered
    """
    _get_project_root_or_error = helpers["get_project_root_or_error"]

    @mcp.tool(
        description="幫我修問題、自動修復 (Auto fix issues). 適合: 'Fix errors', '幫我修', '處理問題', 'Auto correct'.",
        annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True},
    )
    @audited
    def boring_prompt_fix(
        max_iterations: Annotated[
            int,
            Field(description="Maximum number of fix attempts. Range: 1-10. Default: 3."),
        ] = 3,
        verification_level: Annotated[
            str,
            Field(description="Verification strictness: 'BASIC', 'STANDARD', or 'FULL'."),
        ] = "STANDARD",
        project_path: Annotated[
            Optional[str],
            Field(description="Optional explicit path to project root."),
        ] = None,
    ) -> dict:
        """
        Generate a prompt to fix verification issues.

        This tool:
        1. Runs actual code verification to detect issues
        2. Returns CLI commands to fix the detected issues

        The IDE or Gemini CLI should execute the fix commands.
        This is NOT a fully automated loop - human review is required.
        """
        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        try:
            verifier = CodeVerifier(project_root)
            passed, message = verifier.verify_project(verification_level.upper())
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Verification failed: {e}",
                "suggestion": "Check if the project has valid Python files and ruff is installed.",
            }

        if passed:
            return {
                "status": "SUCCESS",
                "message": "All verification checks passed. No fixes needed.",
                "verification_level": verification_level,
                "project_root": str(project_root),
            }

        fix_prompt = f"""Fix the following code verification issues:

{message}

Requirements:
1. Fix each issue without breaking existing functionality
2. Maintain code style consistency
3. Add comments explaining non-obvious fixes
"""

        return {
            "status": "WORKFLOW_TEMPLATE",
            "workflow": "auto-fix",
            "project_root": str(project_root),
            "verification_passed": False,
            "verification_level": verification_level,
            "issues_detected": message,
            "suggested_prompt": fix_prompt,
            "cli_command": f'gemini --prompt "Fix these issues: {message[:100]}..."',
            "max_iterations": max_iterations,
            "message": (
                "Verification detected issues. Use the suggested prompt with your IDE AI or Gemini CLI to fix them.\n"
                "After fixing, run 'boring verify' (CLI) or 'boring_verify' (MCP) to check results.\n"
                "Repeat until all issues are fixed."
            ),
            "manual_steps": [
                "1. Review the detected issues above",
                "2. Run the suggested fix command in your IDE or Gemini CLI",
                "3. Run boring_verify to check results",
                "4. Repeat if needed",
            ],
        }

    @mcp.tool(
        description="告訴我下一步該做什麼 (Suggest next steps). 適合: 'What should I do next?', '下一步呢', '給我建議', 'What now?'.",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    @audited
    def boring_suggest_next(
        limit: Annotated[int, Field(description="Maximum suggestions to return")] = 3,
        error_message: Annotated[
            Optional[str],
            Field(
                description="The specific error message or context to find a solution for. Pass this to trigger Active Recall."
            ),
        ] = None,
        project_path: Annotated[
            Optional[str], Field(description="Optional project root path")
        ] = None,
    ) -> dict:
        """
        Suggest next actions based on project state and learned patterns.

        Enhanced with:
        - 🧠 **Reflexive Brain**: If `error_message` is passed, actively searches for known solutions.
        - Git change analysis (uncommitted files)
        - Learned patterns (generic or specific)
        - RAG index freshness check
        - Task.md progress detection

        Performance: Uses ThreadPoolExecutor for parallel I/O operations.
        """
        project_root, error = _get_project_root_or_error(project_path)
        if error:
            return error

        # V10.30: Profile-Aware Suggestions
        from ..tool_profiles import get_profile, should_register_prompt, should_register_tool

        profile = get_profile()

        miner = get_pattern_miner(project_root)
        base_suggestions = miner.suggest_next(project_root, limit)
        project_state = miner.analyze_project_state(project_root)

        enhancements = []

        check_functions = [
            (_check_git_changes, project_root),
            (_check_learned_patterns, (project_root, error_message)),
            (_check_rag_index, project_root),
            (_check_task_progress, project_root),
            (_check_project_empty, project_root),
            (_check_project_context, project_root),
        ]

        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="suggest-") as executor:
            futures = {executor.submit(func, arg): func.__name__ for func, arg in check_functions}

            for future in as_completed(futures, timeout=5):
                try:
                    results = future.result(timeout=2)
                    if results:
                        # V10.30: Filter enhancements based on Profile Capabilities
                        filtered_results = []
                        for item in results:
                            # 1. Check if recommended action involves a tool we don't have
                            action_text = item.get("action", "").lower()

                            if item.get("type") == "rag_not_indexed":
                                if not should_register_tool("boring_rag_index", profile):
                                    # Suggest switching profile instead of running missing tool
                                    item["action"] = (
                                        "Switch to STANDARD profile to enable RAG Code Search"
                                    )
                                    item["priority"] = "low"

                            if item.get("type") == "prompt_recommendation":
                                # Check if prompt is available (e.g. /vibe_start, /smart_commit)
                                import re

                                match = re.search(r"/(\w+)", action_text)
                                if match:
                                    prompt_name = match.group(1)
                                    if not should_register_prompt(prompt_name, profile):
                                        continue  # Skip this recommendation

                            filtered_results.append(item)

                        enhancements.extend(filtered_results)
                except Exception:
                    pass

        return {
            "status": "SUCCESS",
            "suggestions": base_suggestions,
            "context_enhancements": enhancements,
            "project_state": project_state,
        }

    @mcp.tool(
        description="查看任務進度 (Check task progress). 適合: '任務做到哪了', 'Check progress', '進度如何', 'Is it done yet?'.",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    @audited
    def boring_get_progress(
        task_id: Annotated[str, Field(description="ID of the task to check")],
    ) -> dict:
        """
        Get progress of a running task.
        """
        manager = get_streaming_manager()
        reporter = manager.get_reporter(task_id)

        if not reporter:
            return {"status": "NOT_FOUND", "message": f"Task '{task_id}' not found"}

        latest = reporter.get_latest()
        return {
            "status": "SUCCESS",
            "task_id": task_id,
            "progress": {
                "stage": latest.stage.value if latest else "unknown",
                "message": latest.message if latest else "",
                "percentage": latest.percentage if latest else 0,
            },
            "duration_seconds": reporter.get_duration(),
            "events": reporter.get_all_events(),
        }

    return 3  # Number of tools registered
