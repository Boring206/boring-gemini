"""
Response Analyzer for Boring V4.0

Analyzes Gemini output to determine loop exit conditions.
Prioritizes structured function call results over text-based heuristics.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .logger import log_status

ANALYSIS_RESULT_FILE = Path(".response_analysis")
EXIT_SIGNALS_FILE = Path(".exit_signals")


def analyze_response(
    output_file: Path, loop_number: int, function_call_results: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """
    Analyzes Gemini output and extracts signals.

    Priority order for exit detection:
    1. Function call results (report_status tool) - Most reliable
    2. Structured status block (---BORING_STATUS---) - Reliable
    3. Git diff for file changes - Objective measure of progress

    Removed: Natural language keyword guessing (unreliable)

    Args:
        output_file: Path to the Gemini output log file
        loop_number: Current loop iteration number
        function_call_results: Optional dict containing processed function call data,
            particularly 'report_status' tool results from gemini_client

    Returns:
        Analysis results dict with exit signals and confidence scores
    """
    analysis_results: dict[str, Any] = {
        "loop_number": loop_number,
        "timestamp": datetime.now().isoformat(),
        "output_file": str(output_file),
        "analysis": {
            "has_completion_signal": False,
            "is_test_only": False,
            "is_stuck": False,
            "has_progress": False,
            "files_modified": 0,
            "confidence_score": 0,
            "exit_signal": False,
            "work_summary": "",
            "output_length": 0,
            "source": "none",  # Track where signal came from
        },
    }

    # === PRIORITY 1: Function Call Results (Most Reliable) ===
    if function_call_results:
        status_report = function_call_results.get("report_status") or function_call_results.get(
            "status"
        )
        if status_report:
            analysis_results["analysis"]["source"] = "function_call"

            # Extract structured data from report_status tool
            if isinstance(status_report, dict):
                exit_signal = status_report.get("exit_signal", False)
                status = status_report.get("status", "")
                tasks = status_report.get("tasks_completed", [])
                files = status_report.get("files_modified", [])

                if exit_signal or status in ("COMPLETE", "DONE", "FINISHED"):
                    analysis_results["analysis"]["has_completion_signal"] = True
                    analysis_results["analysis"]["exit_signal"] = True
                    # Base 100 + 20 for completion task
                    analysis_results["analysis"]["confidence_score"] = 120

                if tasks:
                    analysis_results["analysis"]["has_progress"] = True
                    analysis_results["analysis"]["work_summary"] = (
                        f"Completed: {', '.join(tasks[:3])}"
                    )
                    analysis_results["analysis"]["confidence_score"] += 20

                if files:
                    analysis_results["analysis"]["files_modified"] = (
                        len(files) if isinstance(files, list) else 1
                    )
                    analysis_results["analysis"]["has_progress"] = True

            # If we got function call data, save and return early (most reliable source)
            if analysis_results["analysis"]["confidence_score"] > 0:
                ANALYSIS_RESULT_FILE.write_text(json.dumps(analysis_results, indent=4))
                return analysis_results

    # === PRIORITY 2: Structured Status Block (Reliable) ===
    if output_file.exists():
        try:
            output_content = output_file.read_text(encoding="utf-8")
            analysis_results["analysis"]["output_length"] = len(output_content)
        except Exception:
            output_content = ""
    else:
        log_status(Path("logs"), "ERROR", f"Output file not found: {output_file}")
        ANALYSIS_RESULT_FILE.write_text(json.dumps(analysis_results, indent=4))
        return analysis_results

    # Check for explicit structured output block
    if "---BORING_STATUS---" in output_content:
        status_block_match = re.search(
            r"---BORING_STATUS---\s*(.*?)\s*---END_BORING_STATUS---", output_content, re.DOTALL
        )
        if status_block_match:
            analysis_results["analysis"]["source"] = "status_block"
            status_block = status_block_match.group(1)

            if "STATUS: COMPLETE" in status_block or "EXIT_SIGNAL: true" in status_block:
                analysis_results["analysis"]["has_completion_signal"] = True
                analysis_results["analysis"]["exit_signal"] = True
                analysis_results["analysis"]["confidence_score"] = 100

    # === PRIORITY 3: Git Diff for File Changes (Objective) ===
    try:
        from git import InvalidGitRepositoryError, Repo

        try:
            repo = Repo(Path.cwd())
            changed_files = [item.a_path for item in repo.index.diff(None)]
            unstaged_new_files = repo.untracked_files

            total_modified_files = len(changed_files) + len(unstaged_new_files)
            if total_modified_files > 0:
                analysis_results["analysis"]["has_progress"] = True
                analysis_results["analysis"]["files_modified"] = total_modified_files
                analysis_results["analysis"]["confidence_score"] += 20
                if analysis_results["analysis"]["source"] == "none":
                    analysis_results["analysis"]["source"] = "git_diff"
        except InvalidGitRepositoryError:
            pass
    except ImportError:
        pass  # GitPython not installed

    # === Minimal Fallback: Only if no other signals ===
    if analysis_results["analysis"]["confidence_score"] == 0:
        # Check for completely empty or minimal output (possible stuck state)
        if len(output_content) < 50:
            analysis_results["analysis"]["work_summary"] = "Minimal output detected"
            analysis_results["analysis"]["source"] = "fallback"
        else:
            analysis_results["analysis"]["work_summary"] = (
                "Output analyzed, awaiting structured signals"
            )
            analysis_results["analysis"]["source"] = "fallback"

    # Save analysis results
    ANALYSIS_RESULT_FILE.write_text(json.dumps(analysis_results, indent=4))
    return analysis_results


def update_exit_signals(exit_signals_file: Path):
    """Updates the .exit_signals file based on the latest analysis."""
    if not ANALYSIS_RESULT_FILE.exists():
        return

    analysis_data = json.loads(ANALYSIS_RESULT_FILE.read_text())

    is_test_only = analysis_data["analysis"].get("is_test_only", False)
    has_completion_signal = analysis_data["analysis"].get("has_completion_signal", False)
    loop_number = analysis_data["loop_number"]
    has_progress = analysis_data["analysis"].get("has_progress", False)
    confidence = analysis_data["analysis"].get("confidence_score", 0)

    signals_data = {}
    if exit_signals_file.exists():
        try:
            signals_data = json.loads(exit_signals_file.read_text())
        except (json.JSONDecodeError, Exception):
            signals_data = {}

    if not signals_data:
        signals_data = {"test_only_loops": [], "done_signals": [], "completion_indicators": []}

    # Update test_only_loops
    if is_test_only:
        signals_data["test_only_loops"].append(loop_number)
    elif has_progress:
        signals_data["test_only_loops"] = []

    # Update done_signals
    if has_completion_signal:
        signals_data["done_signals"].append(loop_number)

    # Update completion_indicators (strong signals)
    if confidence >= 60:
        signals_data["completion_indicators"].append(loop_number)

    # Keep only last 5 signals (rolling window)
    signals_data["test_only_loops"] = signals_data.get("test_only_loops", [])[-5:]
    signals_data["done_signals"] = signals_data.get("done_signals", [])[-5:]
    signals_data["completion_indicators"] = signals_data.get("completion_indicators", [])[-5:]

    exit_signals_file.write_text(json.dumps(signals_data, indent=4))


def log_analysis_summary():
    """Logs the analysis summary in a human-readable format."""
    if not ANALYSIS_RESULT_FILE.exists():
        return

    analysis_data = json.loads(ANALYSIS_RESULT_FILE.read_text())
    analysis = analysis_data["analysis"]

    log_status(Path("logs"), "INFO", f"Analysis Summary (Loop #{analysis_data['loop_number']}):")
    log_status(Path("logs"), "INFO", f"  Exit Signal: {analysis['exit_signal']}")
    log_status(Path("logs"), "INFO", f"  Confidence: {analysis['confidence_score']}%")
    log_status(Path("logs"), "INFO", f"  Source: {analysis.get('source', 'unknown')}")
    log_status(Path("logs"), "INFO", f"  Files Changed: {analysis['files_modified']}")
    log_status(Path("logs"), "INFO", f"  Summary: {analysis['work_summary']}")
