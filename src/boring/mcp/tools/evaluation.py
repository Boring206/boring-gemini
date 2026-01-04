from pathlib import Path
from typing import Optional, Annotated
from pydantic import Field
from ..instance import mcp, MCP_AVAILABLE
from ..utils import check_rate_limit, detect_project_root, get_project_root_or_error
from ...audit import audited

# ==============================================================================
# EVALUATION TOOLS
# ==============================================================================

@audited
def boring_evaluate(
    target: Annotated[str, Field(description="File path or content to evaluate")],
    context: Annotated[str, Field(description="Optional context or requirements")] = "",
    level: Annotated[str, Field(description="Evaluation technique: DIRECT (score 1-5), PAIRWISE (comparison)")] = "DIRECT",
    interactive: Annotated[bool, Field(description="If True, returns the PROMPT instead of executing it. Useful for IDE AI.")] = None,
    project_path: Annotated[str, Field(description="Optional explicit path to project root")] = None
) -> str:
    """
    Evaluate code quality using Advanced Evaluation techniques (LLM-as-a-Judge).
    
    Args:
       target: File path or content to evaluate.
       context: Optional context or requirements.
       level: Evaluation technique:
              - DIRECT: Direct Scoring (1-5 scale) against strict rubrics.
              - PAIRWISE: (Coming soon) Compare valid alternatives.
       interactive: If True, returns the PROMPT instead of executing it. Useful for IDE AI.
       project_path: Optional explicit path to project root
              
    Returns:
        Evaluation report (JSON score) or Prompt (if interactive=True).
    """
    # Rate limit check
    allowed, msg = check_rate_limit("boring_evaluate")
    if not allowed:
        return f"⏱️ Rate limited: {msg}"
        
    project_root = detect_project_root(project_path)
    if not project_root:
        return "❌ No valid Boring project found. Run in project root."
        
    try:
        from ...config import settings
        # CRITICAL: Contextually update project root
        settings.PROJECT_ROOT = project_root
        
        from ...judge import LLMJudge
        from ...cli_client import GeminiCLIAdapter
        
        # Auto-detect MCP mode: If running as MCP tool, default to interactive
        # This allows IDE AI (Cursor, Claude Desktop) to execute the evaluation
        import os
        is_mcp_mode = os.environ.get("BORING_MCP_MODE", "0") == "1"
        
        # In MCP mode, default to interactive unless explicitly set to False
        if is_mcp_mode and interactive is None:
            interactive = True
        elif interactive is None:
            interactive = False
        
        # Initialize Judge
        adapter = GeminiCLIAdapter(model_name=settings.DEFAULT_MODEL)
        
        # In interactive mode, we don't strictly need the CLI to be functional
        if not adapter.is_available and not interactive:
             return "❌ Gemini CLI not found. Install it or use interactive=True to generate prompts."

        judge = LLMJudge(adapter)
        
        # Resolve target
        target_path = Path(target)
        if not target_path.is_absolute():
            target_path = project_root / target_path
            
        if not target_path.exists():
            return f"❌ Target not found: {target}"
            
        if target_path.is_file():
            # Safe file reading with encoding fallback
            try:
                content = target_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    content = target_path.read_text(encoding="latin-1")
                except Exception as e:
                    return f"❌ Cannot read file (binary or encoding issue): {e}"
            except Exception as e:
                return f"❌ File read error: {e}"
            
            result = judge.grade_code(target_path.name, content, interactive=interactive)
            
            if interactive:
                prompt_content = result.get('prompt', 'Error generating prompt')
                return f"### 📋 Evaluation Prompt (Copy to Chat)\n\nUse this prompt to evaluate `{target_path.name}` using your current AI context:\n\n```markdown\n{prompt_content}\n```"
            
            score = result.get("score", 0)
            summary = result.get("summary", "No summary available")
            suggestions = result.get("suggestions", [])
            raw_response = result.get("raw", "")
            reasoning = result.get("reasoning", "")
            
            # Check for failed evaluation - provide diagnostic info
            if score == 0:
                error_report = f"# ⚠️ Evaluation Failed: {target_path.name}\n\n"
                error_report += "**Score**: 0/5 (Evaluation could not complete)\n\n"
                error_report += "## Possible Causes:\n"
                error_report += "1. **Gemini CLI unavailable** - Install with: `npm install -g @google/gemini-cli`\n"
                error_report += "2. **JSON parsing failed** - LLM response was not valid JSON\n"
                error_report += "3. **File too small** - Very short files may not have enough content to evaluate\n\n"
                
                if reasoning:
                    error_report += f"## Error Details:\n{reasoning}\n\n"
                
                if raw_response:
                    error_report += f"## Raw Response (first 500 chars):\n```\n{raw_response[:500]}...\n```\n\n"
                
                error_report += "## 💡 Try Interactive Mode:\n"
                error_report += f"```\nboring_evaluate(target=\"{target}\", interactive=True)\n```\n"
                error_report += "This returns the evaluation prompt for you to execute manually."
                
                return error_report
            suggestions = result.get("suggestions", [])
            dimensions = result.get("dimensions", {})
            
            # Format report with multi-dimensional scores
            emoji = "🟢" if score >= 4 else "🟡" if score >= 3 else "🔴"
            report = f"# {emoji} Evaluation: {target_path.name}\n"
            report += f"**Overall Score**: {score}/5.0\n\n"
            report += f"**Summary**: {summary}\n\n"
            
            # Display multi-dimensional breakdown
            if dimensions:
                report += "## 📊 Dimension Scores\n\n"
                report += "| Dimension | Score | Comment |\n"
                report += "|-----------|-------|--------|\n"
                for dim_name, dim_data in dimensions.items():
                    dim_score = dim_data.get("score", 0)
                    dim_comment = dim_data.get("comment", "N/A")[:60]
                    dim_emoji = "🟢" if dim_score >= 4 else "🟡" if dim_score >= 3 else "🔴"
                    report += f"| {dim_emoji} **{dim_name.title()}** | {dim_score}/5 | {dim_comment} |\n"
                report += "\n"
            
            if suggestions:
                report += "## 💡 Suggestions\n"
                for s in suggestions:
                    report += f"- {s}\n"
                    
            return report
        
        # Directory support: evaluate all Python files
        if target_path.is_dir():
            py_files = list(target_path.glob("*.py"))
            if not py_files:
                return f"❌ No Python files found in directory: {target}"
            
            reports = []
            for py_file in py_files[:5]:  # Limit to 5 files to avoid overload
                try:
                    content = py_file.read_text(encoding="utf-8")
                    result = judge.grade_code(py_file.name, content, interactive=False)
                    score = result.get("score", 0)
                    emoji = "🟢" if score >= 4 else "🟡" if score >= 3 else "🔴"
                    reports.append(f"{emoji} **{py_file.name}**: {score}/5.0")
                except Exception:
                    reports.append(f"⚠️ **{py_file.name}**: Error reading")
            
            return "# Directory Evaluation\n\n" + "\n".join(reports)
            
        return "❌ Invalid target type."
        
    except Exception as e:
        return f"❌ Error evaluating: {str(e)}"

if MCP_AVAILABLE and mcp is not None:
    mcp.tool(description="Evaluate code quality (LLM Judge)", annotations={"readOnlyHint": True, "openWorldHint": True})(boring_evaluate)

