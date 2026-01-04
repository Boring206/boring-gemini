"""
V10 Tools Registration

Registers all V10 tools (RAG, Multi-Agent, Shadow Mode) with FastMCP.
"""

from typing import Dict, Any, Callable


def register_v10_tools(mcp, audited: Callable, helpers: Dict[str, Any]) -> int:
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
        from .tools.rag import register_rag_tools
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
        from .tools.agents import register_agent_tools
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
        from .tools.shadow import register_shadow_tools
        register_shadow_tools(mcp, helpers)
        tool_count += 5  # status, approve, reject, mode, clear
    except ImportError as e:
        import sys
        sys.stderr.write(f"[boring-mcp] Warning: Shadow tools not available: {e}\n")
    except Exception as e:
        import sys
        sys.stderr.write(f"[boring-mcp] Warning: Failed to register Shadow tools: {e}\n")
    
    return tool_count
