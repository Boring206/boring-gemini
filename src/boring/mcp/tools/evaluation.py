import os
from pathlib import Path
from typing import Annotated

from pydantic import Field

from ...audit import audited
from ...judge import LLMJudge, create_judge_provider
from ..instance import MCP_AVAILABLE, mcp
from ..utils import check_rate_limit, detect_project_root

# ==============================================================================
# EVALUATION TOOLS
# ==============================================================================


@audited
def boring_evaluate(
    target: Annotated[str, Field(description="File path or content to evaluate")],
    context: Annotated[str, Field(description="Optional context or requirements")] = "",
    level: Annotated[
        str, Field(description="Evaluation technique: DIRECT (score 1-5), PAIRWISE (comparison)")
    ] = "DIRECT",
    interactive: Annotated[
        bool,
        Field(
            description="If True, returns the PROMPT instead of executing it. Useful for IDE AI."
        ),
    ] = None,
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
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

        # CRITICAL: Contextually update project root
        settings.PROJECT_ROOT = project_root

        # Auto-detect MCP mode: If running as MCP tool, default to interactive
        is_mcp_mode = os.environ.get("BORING_MCP_MODE", "0") == "1"

        if is_mcp_mode and interactive is None:
            interactive = True
        elif interactive is None:
            interactive = False

        # Initialize Judge with configured provider
        provider = create_judge_provider()

        # Check availability
        if not provider.is_available and not interactive:
            return f"❌ LLM Provider ({provider.provider_name}) not available. Check configuration."

        judge = LLMJudge(provider)

        # Handle Pairwise Comparison (V10.27: PREPAIR technique)
        if level.upper() == "PAIRWISE":
            targets = [t.strip() for t in target.split(",")]
            if len(targets) != 2:
                return "❌ PAIRWISE mode requires exactly two comma-separated files in 'target' (e.g., 'src/old.py,src/new.py')"

            path_a = (
                project_root / targets[0]
                if not Path(targets[0]).is_absolute()
                else Path(targets[0])
            )
            path_b = (
                project_root / targets[1]
                if not Path(targets[1]).is_absolute()
                else Path(targets[1])
            )

            if not path_a.exists() or not path_b.exists():
                return f"❌ Files not found: {path_a} or {path_b}"

            content_a = path_a.read_text(encoding="utf-8", errors="replace")
            content_b = path_b.read_text(encoding="utf-8", errors="replace")

            # V10.27: PREPAIR - Check reasoning cache for pointwise analyses
            from ...intelligence.context_optimizer import get_reasoning_cache

            cache = get_reasoning_cache()
            cached_a, cached_b = cache.compare_with_cache(content_a, content_b)

            prepair_info = ""
            if cached_a and cached_b:
                # Both cached - use existing pointwise reasoning
                prepair_info = (
                    f"\n\n### 🧠 PREPAIR Cache (Both Hit)\n"
                    f"- **{path_a.name}**: Score {cached_a.score}/5, "
                    f"{len(cached_a.strengths)} strengths, {len(cached_a.weaknesses)} weaknesses\n"
                    f"- **{path_b.name}**: Score {cached_b.score}/5, "
                    f"{len(cached_b.strengths)} strengths, {len(cached_b.weaknesses)} weaknesses\n"
                )
            elif cached_a:
                prepair_info = f"\n\n### 🧠 PREPAIR Cache (Partial: {path_a.name} hit)\n"
            elif cached_b:
                prepair_info = f"\n\n### 🧠 PREPAIR Cache (Partial: {path_b.name} hit)\n"

            result = judge.compare_code(
                name_a=path_a.name,
                code_a=content_a,
                name_b=path_b.name,
                code_b=content_b,
                context=context,
                interactive=interactive,
            )

            if interactive:
                prompts = result.get("prompts", {})
                return (
                    f"### ⚖️ Pairwise Comparison Prompts (PREPAIR Enhanced){prepair_info}\n\n"
                    f"**Pass 1 (A vs B):**\n```markdown\n{prompts.get('pass1', '')}\n```\n\n"
                    f"**Pass 2 (B vs A):**\n```markdown\n{prompts.get('pass2', '')}\n```"
                )

            winner = result.get("winner", "TIE")
            confidence = result.get("confidence", 0.0)
            reasoning = result.get("reasoning", "")

            # V10.27: Cache the pointwise analyses for future comparisons
            if "analysis_a" in result:
                cache.set(
                    content_a,
                    result.get("analysis_a", ""),
                    score=result.get("score_a", 0),
                    strengths=result.get("strengths_a", []),
                    weaknesses=result.get("weaknesses_a", []),
                )
            if "analysis_b" in result:
                cache.set(
                    content_b,
                    result.get("analysis_b", ""),
                    score=result.get("score_b", 0),
                    strengths=result.get("strengths_b", []),
                    weaknesses=result.get("weaknesses_b", []),
                )

            emoji = "🏆" if winner != "TIE" else "⚖️"
            stats = cache.get_stats()

            return (
                f"# {emoji} Pairwise Evaluation Result (PREPAIR)\n\n"
                f"**Winner**: {winner} (Confidence: {confidence})\n\n"
                f"**Reasoning**:\n{reasoning}\n"
                f"{prepair_info}"
                f"\n📊 Cache: {stats['hits']} hits, {stats['misses']} misses ({stats['hit_rate']:.0%} hit rate)"
            )

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
                prompt_content = result.get("prompt", "Error generating prompt")
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
                    error_report += (
                        f"## Raw Response (first 500 chars):\n```\n{raw_response[:500]}...\n```\n\n"
                    )

                error_report += "## 💡 Try Interactive Mode:\n"
                error_report += f'```\nboring_evaluate(target="{target}", interactive=True)\n```\n'
                error_report += "This returns the evaluation prompt for you to execute manually."

                return error_report
            suggestions = result.get("suggestions", [])
            dimensions = result.get("dimensions", {})

            # Format report with multi-dimensional scores
            emoji = "🟢" if score >= 4 else "🟡" if score >= 3 else "🔴"
            report = f"# {emoji} Evaluation: {target_path.name}\n"
            report += f"**Overall Score**: {score}/5.0\n\n"
            report += f"**Summary**: {summary}\n\n"

            # Record metrics in QualityTracker
            try:
                from ...quality_tracker import QualityTracker

                tracker = QualityTracker()
                tracker.record(
                    score=float(score), issues_count=len(suggestions), context="boring_evaluate"
                )
            except Exception as e:
                report += f"\n[Warning: Failed to record quality stats: {e}]\n"

            # Display multi-dimensional breakdown
            if dimensions:
                report += "## 📊 Dimension Scores\n\n"
                report += "| Dimension | Score | Comment |\n"
                report += "|-----------|-------|--------|\n"
                for dim_name, dim_data in dimensions.items():
                    dim_score = dim_data.get("score", 0)
                    dim_comment = dim_data.get("comment", "N/A")[:60]
                    dim_emoji = "🟢" if dim_score >= 4 else "🟡" if dim_score >= 3 else "🔴"
                    report += (
                        f"| {dim_emoji} **{dim_name.title()}** | {dim_score}/5 | {dim_comment} |\n"
                    )
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


# ==============================================================================
# V10.25: ADVANCED EVALUATION TOOLS
# ==============================================================================


@audited
def boring_evaluation_metrics(
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> str:
    """
    Get evaluation system metrics and statistics.

    Shows correlation with human judgments, position consistency, and bias indicators.

    Returns:
        Formatted metrics report
    """
    allowed, msg = check_rate_limit("boring_evaluation_metrics")
    if not allowed:
        return f"⏱️ Rate limited: {msg}"

    project_root = detect_project_root(project_path)
    if not project_root:
        return "❌ No valid Boring project found. Run in project root."

    try:
        from ...judge.metrics import (
            format_metrics_report,
            generate_metrics_report,
        )

        # Try to load historical evaluation data
        memory_dir = project_root / ".boring_memory"
        if not memory_dir.exists():
            return (
                "# 📊 Evaluation Metrics\n\n"
                "No evaluation history found. Run `boring_evaluate` on some files first.\n\n"
                "After evaluations, this tool will show:\n"
                "- Correlation metrics (Spearman's ρ, Kendall's τ)\n"
                "- Agreement metrics (Cohen's κ)\n"
                "- Position consistency for pairwise comparisons\n"
                "- Bias indicators"
            )

        # Generate sample report (in production, load real data)
        report = generate_metrics_report(
            evaluation_type="general",
        )

        return format_metrics_report(report)

    except Exception as e:
        return f"❌ Error getting metrics: {str(e)}"


@audited
def boring_bias_report(
    days: Annotated[int, Field(description="Number of days to analyze (default: 30)")] = 30,
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> str:
    """
    Get bias monitoring report for the evaluation system.

    Analyzes position bias (first-position preference) and length bias (longer = higher scores).

    Returns:
        Formatted bias report with recommendations
    """
    allowed, msg = check_rate_limit("boring_bias_report")
    if not allowed:
        return f"⏱️ Rate limited: {msg}"

    project_root = detect_project_root(project_path)
    if not project_root:
        return "❌ No valid Boring project found. Run in project root."

    try:
        from ...judge.bias_monitor import format_bias_report, get_bias_monitor

        monitor = get_bias_monitor(project_root)
        report = monitor.get_bias_report(days=days)

        return format_bias_report(report)

    except Exception as e:
        return f"❌ Error getting bias report: {str(e)}"


@audited
def boring_generate_rubric(
    name: Annotated[str, Field(description="Name for the rubric")],
    domain: Annotated[
        str,
        Field(description="Domain: code_quality, security, performance, documentation"),
    ] = "code_quality",
    strictness: Annotated[
        str, Field(description="Strictness: lenient, balanced, strict")
    ] = "balanced",
    criteria: Annotated[str, Field(description="Comma-separated criterion names")] = "",
    project_path: Annotated[
        str, Field(description="Optional explicit path to project root")
    ] = None,
) -> str:
    """
    Generate a detailed evaluation rubric with level descriptions.

    Creates rubrics with:
    - Detailed level descriptions (1-5 scale)
    - Edge case guidance
    - Scoring guidelines based on strictness

    Returns:
        Generated rubric in prompt format
    """
    allowed, msg = check_rate_limit("boring_generate_rubric")
    if not allowed:
        return f"⏱️ Rate limited: {msg}"

    try:
        from ...judge.rubric_generator import generate_rubric, rubric_to_prompt

        # Parse criteria
        if criteria:
            criteria_list = [c.strip() for c in criteria.split(",")]
        else:
            # Default criteria based on domain
            default_criteria = {
                "code_quality": ["Readability", "Documentation", "Modularity", "Error Handling"],
                "security": ["Secrets Management", "Input Validation", "Injection Prevention"],
                "performance": ["Algorithmic Efficiency", "Resource Usage", "Caching"],
                "documentation": ["Completeness", "Examples", "Accuracy"],
            }
            criteria_list = default_criteria.get(domain, ["Quality", "Correctness"])

        rubric = generate_rubric(
            name=name,
            description=f"Evaluation rubric for {name}",
            domain=domain,
            criteria_names=criteria_list,
            scale="1-5",
            strictness=strictness,
        )

        prompt_text = rubric_to_prompt(rubric)

        return (
            f"# 📏 Generated Rubric: {name}\n\n"
            f"**Domain**: {domain}\n"
            f"**Strictness**: {strictness}\n"
            f"**Criteria**: {', '.join(criteria_list)}\n\n"
            f"---\n\n"
            f"{prompt_text}"
        )

    except Exception as e:
        return f"❌ Error generating rubric: {str(e)}"


if MCP_AVAILABLE and mcp is not None:
    mcp.tool(
        description="Evaluate code quality (LLM Judge)",
        annotations={"readOnlyHint": True, "openWorldHint": True},
    )(boring_evaluate)

    mcp.tool(
        description="Get evaluation system metrics (Spearman, Kappa, etc.)",
        annotations={"readOnlyHint": True},
    )(boring_evaluation_metrics)

    mcp.tool(
        description="Get bias monitoring report (position bias, length bias)",
        annotations={"readOnlyHint": True},
    )(boring_bias_report)

    mcp.tool(
        description="Generate detailed evaluation rubric with level descriptions",
        annotations={"readOnlyHint": True},
    )(boring_generate_rubric)
