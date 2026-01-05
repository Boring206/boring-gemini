"""
Quality Trend MCP Tool
"""

from typing import Annotated

from pydantic import Field

from ...audit import audited
from ...quality_tracker import QualityTracker
from ..instance import MCP_AVAILABLE, mcp


@audited
def boring_quality_trend(
    days: Annotated[int, Field(description="Number of days/entries context to show")] = 30,
) -> str:
    """
    Show the code quality trend chart and stats.
    Useful for checking if the project health is improving or degrading.
    """
    tracker = QualityTracker()
    chart = tracker.render_ascii_chart(width=50, height=10)

    # Get last entry stats
    history = tracker.get_trend(1)
    if not history:
        return "No quality history available yet. Run an evaluation first."

    last = history[0]

    report = "# 📈 Quality Trend Report\n\n"
    report += f"**Current Score**: {last['score']}/5.0\n"
    report += f"**Open Issues**: {last['issues_count']}\n"
    report += f"**Last Check**: {last['date']}\n\n"
    report += "```\n" + chart + "\n```"

    return report


if MCP_AVAILABLE and mcp is not None:
    mcp.tool(description="Show code quality trends")(boring_quality_trend)
