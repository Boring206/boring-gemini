"""
V10 Tools Registration

Registers all V10 tools (RAG, Multi-Agent, Shadow Mode) with FastMCP.
"""

from typing import Any, Callable

from .tools.agents import register_agent_tools
from .tools.rag import register_rag_tools
from .tools.shadow import register_shadow_tools
from .utils import get_project_root_or_error  # noqa: F401


def register_v10_tools(mcp, audited: Callable, helpers: dict[str, Any]) -> int:
    """
    Register all V10 tools with the MCP server.

    V10 Features:
    - RAG (Vector Memory + Graph RAG)
    - Multi-Agent Orchestration
    - Shadow Mode (Human-in-the-Loop)

    Args:
        mcp: FastMCP instance
        audited: Audit decorator
        helpers: Dict with helper functions

    Returns:
        Number of tools registered
    """
    tool_count = 0

    # =========================================================================
    # RAG Tools
    # =========================================================================
    try:
        register_rag_tools(mcp, helpers)
        tool_count += 4  # index, search, context, expand
    except ImportError as e:
        import sys

        sys.stderr.write(f"[boring-mcp] Warning: RAG tools not available: {e}\n")
    except Exception as e:
        import sys

        sys.stderr.write(f"[boring-mcp] Warning: Failed to register RAG tools: {e}\n")

    # =========================================================================
    # Multi-Agent Tools
    # =========================================================================
    try:
        register_agent_tools(mcp, helpers)
        tool_count += 3  # multi_agent, agent_plan, agent_review
    except ImportError as e:
        import sys

        sys.stderr.write(f"[boring-mcp] Warning: Agent tools not available: {e}\n")
    except Exception as e:
        import sys

        sys.stderr.write(f"[boring-mcp] Warning: Failed to register Agent tools: {e}\n")

    # =========================================================================
    # Shadow Mode Tools
    # =========================================================================
    try:
        register_shadow_tools(mcp, helpers)
        tool_count += 8  # status, approve, reject, mode, clear, trust, trust_list, trust_remove
    except ImportError as e:
        import sys

        sys.stderr.write(f"[boring-mcp] Warning: Shadow tools not available: {e}\n")
    except Exception as e:
        import sys

        sys.stderr.write(f"[boring-mcp] Warning: Failed to register Shadow tools: {e}\n")

    return tool_count
