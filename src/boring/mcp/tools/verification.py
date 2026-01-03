from typing import Optional
from ..instance import mcp, MCP_AVAILABLE
from ..utils import check_rate_limit, get_project_root_or_error, configure_runtime_for_project
from ...audit import audited

# ==============================================================================
# VERIFICATION TOOLS
# ==============================================================================

@audited
def boring_verify(level: str = "STANDARD", project_path: Optional[str] = None) -> dict:
    """
    Run code verification on the project.
    
    Args:
        level: Verification level (BASIC, STANDARD, FULL)
        project_path: Optional explicit path to project root
        
    Returns:
        Verification results including pass/fail and any errors
    """
    try:
        # --- Input Validation ---
        valid_levels = ("BASIC", "STANDARD", "FULL", "SEMANTIC")
        if level.upper() not in valid_levels:
            return {
                "status": "ERROR",
                "passed": False,
                "message": f"Invalid level: '{level}'.",
                "suggestion": f"Use one of: {', '.join(valid_levels)}"
            }
        # --- End Validation ---
        
        # Rate limit check
        allowed, msg = check_rate_limit("boring_verify")
        if not allowed:
            return {"status": "RATE_LIMITED", "passed": False, "message": msg}

        from ...verification import CodeVerifier
        from ...config import settings
        from ...cli_client import GeminiCLIAdapter
        from ...judge import LLMJudge
        
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
        passed, message = verifier.verify_project(level.upper())
        
        return {
            "passed": passed,
            "level": level.upper(),
            "message": message
        }
        
    except Exception as e:
        return {
            "passed": False,
            "error": str(e)
        }

@audited
def boring_verify_file(
    file_path: str,
    level: str = "STANDARD",
    project_path: Optional[str] = None
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
        from ...verification import CodeVerifier
        from ...config import settings
        
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
                "resolved_path": str(full_path)
            }
        
        # Only support Python files for now
        if full_path.suffix != ".py":
            return {
                "status": "SKIPPED",
                "passed": True,
                "message": f"Verification skipped for non-Python file: {full_path.suffix}",
                "file": str(full_path.relative_to(project_root))
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
                issues.append({
                    "check": r.check_type,
                    "message": r.message,
                    "details": r.details[:5] if r.details else []  # Limit details
                })
            if r.suggestions:
                suggestions.extend(r.suggestions[:3])  # Limit suggestions
        
        return {
            "status": "SUCCESS" if all_passed else "ISSUES_FOUND",
            "passed": all_passed,
            "file": str(full_path.relative_to(project_root)),
            "level": level.upper(),
            "checks_run": len(results),
            "issues": issues if issues else None,
            "suggestions": suggestions[:5] if suggestions else None
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "passed": False,
            "error": str(e)
        }

# ==============================================================================
# TOOL REGISTRATION
# ==============================================================================

if MCP_AVAILABLE and mcp is not None:
    mcp.tool()(boring_verify)
    mcp.tool()(boring_verify_file)
