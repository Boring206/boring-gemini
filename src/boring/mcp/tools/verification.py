from typing import Annotated

from pydantic import Field

from ...audit import audited
from ..instance import MCP_AVAILABLE, mcp
from ..utils import check_rate_limit, configure_runtime_for_project, get_project_root_or_error

# ==============================================================================
# VERIFICATION TOOLS
# ==============================================================================


@audited
def boring_verify(
    level: Annotated[
        str,
        Field(
            description="Verification level: BASIC (syntax), STANDARD (lint), FULL (tests), SEMANTIC (judge)"
        ),
    ] = "STANDARD",
    auto_fix: Annotated[
        bool, Field(description="If True, auto-fix lint issues with ruff --fix before checking")
    ] = False,
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Run code verification on the project.

    Args:
        level: Verification level (BASIC, STANDARD, FULL, SEMANTIC)
        auto_fix: If True, auto-fix lint issues with ruff --fix before checking
        project_path: Optional explicit path to project root

    Returns:
        Verification results including pass/fail and any errors
    """
    try:
        # --- Input Validation ---
        valid_levels = ("BASIC", "STANDARD", "FULL", "SEMANTIC", "DOCS")
        if level.upper() not in valid_levels:
            return {
                "status": "ERROR",
                "passed": False,
                "message": f"Invalid level: '{level}'.",
                "suggestion": f"Use one of: {', '.join(valid_levels)}",
            }

        # --- Special Handling for DOCS level (Pure CLI Mode) ---
        if level.upper() == "DOCS":
            # DOCS verification requires LLM analysis, which is best done via CLI directly
            # to avoid timeout/context issues in MCP.
            return {
                "status": "WORKFLOW_TEMPLATE",
                "workflow": "verify_docs",
                "project_root": str(get_project_root_or_error(project_path)[0]),
                "level": "DOCS",
                "message": (
                    "📄 **Documentation Verification Template**\n\n"
                    "Verifying code vs documentation consistency (DOCS level) requires LLM analysis.\n"
                    "Please execute the following command in your terminal:\n\n"
                    "```bash\n"
                    "boring evaluate --level DOCS\n"
                    "```\n"
                    "**What it checks:**\n"
                    "- Function signatures vs Docstrings\n"
                    "- Parameter descriptions vs Actual usage\n"
                    "- Return type annotations vs Docstring returns"
                ),
                "cli_command": "boring evaluate --level DOCS",
                "suggestion": "Run `boring evaluate --level DOCS` in your terminal.",
            }
        # --- End Validation ---

        # Rate limit check
        allowed, msg = check_rate_limit("boring_verify")
        if not allowed:
            return {"status": "RATE_LIMITED", "passed": False, "message": msg}

        from ...cli_client import GeminiCLIAdapter
        from ...config import settings
        from ...judge import LLMJudge
        from ...verification import CodeVerifier

        # Resolve project root
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error

        # CRITICAL: Update global settings for dependencies
        configure_runtime_for_project(project_root)

        # Initialize Judge if Semantic Level
        judge = None
        if level.upper() == "SEMANTIC":
            # Create Adapter (uses project root for CWD)
            adapter = GeminiCLIAdapter(cwd=project_root)
            judge = LLMJudge(adapter)

        # Pass judge to verifier
        verifier = CodeVerifier(project_root, settings.LOG_DIR, judge=judge)
        passed, message = verifier.verify_project(level.upper(), auto_fix=auto_fix)

        result = {"passed": passed, "level": level.upper(), "message": message}

        if auto_fix:
            result["auto_fix"] = True
            result["note"] = "Lint issues were auto-fixed with ruff --fix"

        return result

    except Exception as e:
        return {"passed": False, "error": str(e)}


@audited
def boring_verify_file(
    file_path: Annotated[
        str, Field(description="Relative path to the file to verify (from project root)")
    ],
    level: Annotated[
        str, Field(description="Verification level: BASIC, STANDARD, FULL")
    ] = "STANDARD",
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> dict:
    """
    Verify a single file for syntax errors, linting issues, and import problems.

    This exposes the CodeVerifier functionality for single-file verification.
    Unlike boring_verify (project-wide), this focuses on one specific file.

    Args:
        file_path: Relative path to the file to verify (from project root)
        level: Verification level (BASIC, STANDARD, FULL)
               - BASIC: Syntax check only
               - STANDARD: Syntax + Linting (ruff)
               - FULL: Syntax + Linting + Import validation
        project_path: Optional explicit path to project root

    Returns:
        Verification results for the file
    """
    try:
        from ...config import settings
        from ...verification import CodeVerifier

        # Resolve project root
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error

        # CRITICAL: Configure runtime
        configure_runtime_for_project(project_root)

        # Build full path
        full_path = project_root / file_path.strip().strip('"').strip("'")

        if not full_path.exists():
            return {
                "status": "ERROR",
                "passed": False,
                "error": f"File not found: {file_path}",
                "resolved_path": str(full_path),
            }

        # Only support Python files for now
        if full_path.suffix != ".py":
            return {
                "status": "SKIPPED",
                "passed": True,
                "message": f"Verification skipped for non-Python file: {full_path.suffix}",
                "file": str(full_path.relative_to(project_root)),
            }

        # Run verification
        verifier = CodeVerifier(project_root, settings.LOG_DIR)
        results = verifier.verify_file(full_path, level=level.upper())

        # Process results
        all_passed = all(r.passed for r in results)
        issues = []
        suggestions = []

        for r in results:
            if not r.passed:
                issues.append(
                    {
                        "check": r.check_type,
                        "message": r.message,
                        "details": r.details[:5] if r.details else [],  # Limit details
                    }
                )
            if r.suggestions:
                suggestions.extend(r.suggestions[:3])  # Limit suggestions

        return {
            "status": "SUCCESS" if all_passed else "ISSUES_FOUND",
            "passed": all_passed,
            "file": str(full_path.relative_to(project_root)),
            "level": level.upper(),
            "checks_run": len(results),
            "issues": issues if issues else None,
            "suggestions": suggestions[:5] if suggestions else None,
        }

    except Exception as e:
        return {"status": "ERROR", "passed": False, "error": str(e)}


# ==============================================================================
# TOOL REGISTRATION
# ==============================================================================

if MCP_AVAILABLE and mcp is not None:
    mcp.tool(description="Verify project code", annotations={"readOnlyHint": True})(boring_verify)
    mcp.tool(description="Verify single file", annotations={"readOnlyHint": True})(
        boring_verify_file
    )
