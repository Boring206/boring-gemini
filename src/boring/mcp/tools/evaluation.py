from pathlib import Path
from typing import Optional
from ..instance import mcp, MCP_AVAILABLE
from ..utils import check_rate_limit, detect_project_root, get_project_root_or_error
from ...audit import audited

# ==============================================================================
# EVALUATION TOOLS
# ==============================================================================

@audited
def boring_evaluate(target: str, context: str = "", level: str = "DIRECT", interactive: bool = False, project_path: Optional[str] = None) -> str:
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
        
        # Initialize Judge
        adapter = GeminiCLIAdapter(model_name=settings.DEFAULT_MODEL)
        
        # In interactive mode, we don't strictly need the CLI to be functional if we just want prompts
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
            summary = result.get("summary", "No summary")
            suggestions = result.get("suggestions", [])
            
            # Format report
            emoji = "🟢" if score >= 4 else "🟡" if score >= 3 else "🔴"
            report = f"# {emoji} Evaluation: {target_path.name}\n"
            report += f"**Score**: {score}/5.0\n\n"
            report += f"**Summary**: {summary}\n\n"
            
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
    mcp.tool()(boring_evaluate)
