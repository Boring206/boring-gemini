"""
Quality Trend MCP Tool
"""

from typing import Annotated

from pydantic import Field

from ...audit import audited
from ...quality_tracker import QualityTracker
from ...types import BoringResult, create_error_result, create_success_result
from ..instance import MCP_AVAILABLE, mcp


@audited
def boring_quality_trend(
    days: Annotated[int, Field(description="Number of days/entries context to show")] = 30,
) -> BoringResult:
    """
    Show the code quality trend chart and stats.
    Useful for checking if the project health is improving or degrading.
    """
    tracker = QualityTracker()
    chart = tracker.render_ascii_chart(width=50, height=10)

    # Get last entry stats
    history = tracker.get_trend(1)
    if not history:
        return create_error_result("No quality history available yet. Run an evaluation first.")

    last = history[0]

    report = "# 📈 Quality Trend Report\n\n"
    report += f"**Current Score**: {last['score']}/5.0\n"
    report += f"**Open Issues**: {last['issues_count']}\n"
    report += f"**Last Check**: {last['date']}\n\n"
    report += "```\n" + chart + "\n```"

    return create_success_result(
        message=report, data={"history": history, "current_score": last["score"]}
    )


if MCP_AVAILABLE and mcp is not None:
    mcp.tool(description="Show code quality trends")(boring_quality_trend)
