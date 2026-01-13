import logging
import os
import sys
import warnings

# Suppress warnings to prevent stderr pollution/noise in MCP connection
warnings.simplefilter("ignore")

from contextlib import contextmanager

from . import interceptors

# Install interceptors immediately BEFORE any other imports to catch early stdout pollution
interceptors.install_interceptors()

# Import all modules to register tools with FastMCP
from ..audit import audited  # Moved to top-level to avoid import issues in tests
from . import instance
from .intelligence_tools import register_intelligence_tools  # V10.23
from .prompts import register_prompts

# V10.24: Tool Profiles and Router
from .tool_profiles import ToolRegistrationFilter, get_profile
from .tool_router import get_tool_router

# Import git tools to trigger @mcp.tool registration (boring_commit, boring_visualize)
# Import session tools to trigger @mcp.tool registration (boring_session_*)
from .tools import (
    git,  # noqa: F401
    session,  # noqa: F401 - V10.25: Vibe Session
)

# Import legacy tools to trigger @mcp.tool registration
from .tools.advanced import register_advanced_tools
from .tools.assistant import register_assistant_tools

# V10.26: Import refactored tools from tools/ directory
from .tools.discovery import register_discovery_resources
from .tools.plugins import register_plugin_tools

# from .vibe_tools import register_vibe_tools  # Deprecated and Removed in Phase 10
from .tools.vibe import register_vibe_tools  # Phase 10: Modernized Vibe Module
from .tools.workspace import register_workspace_tools

# Import tools packages to trigger decorators
from .utils import configure_runtime_for_project, detect_project_root, get_project_root_or_error
from .v10_tools import register_v10_tools

# Try to import Smithery decorator for HTTP deployment
try:
    from smithery.decorators import smithery

    SMITHERY_AVAILABLE = True
except ImportError:
    SMITHERY_AVAILABLE = False
    smithery = None


def _get_tool_filter() -> ToolRegistrationFilter:
    """Get tool filter based on current profile configuration."""
    profile_name = os.environ.get("BORING_MCP_PROFILE", "lite")
    return ToolRegistrationFilter(profile_name)


@contextmanager
def _configure_logging():
    """Configure logging to avoid polluting stdout."""
    # Force generic logs to stderr
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="[%(levelname)s] %(message)s")
    # Silence specific noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    yield


def _get_tools_robust(mcp):
    """Robustly extract the tools dictionary from various FastMCP/MCP server versions."""
    # FastMCP 2.x often uses _tools or tools directly on the instance
    for attr in ["_tools", "tools"]:
        val = getattr(mcp, attr, None)
        if isinstance(val, dict):
            return val
    # Newer FastMCP hides it in _tool_manager
    if hasattr(mcp, "_tool_manager"):
        tm = mcp._tool_manager
        for attr in ["_tools", "tools"]:
            val = getattr(tm, attr, None)
            if isinstance(val, dict):
                return val
    return {}


def get_server_instance():
    """
    Get the configured FastMCP server instance (raw).
    Use this for direct access without Smithery decorators (e.g. for http.py).
    """
    os.environ["BORING_MCP_MODE"] = "1"

    if not instance.MCP_AVAILABLE:
        raise RuntimeError("'fastmcp' not found. Install with: pip install boring-aicoding[mcp]")

    # Register Resources
    @instance.mcp.resource("boring://logs")
    def get_logs() -> str:
        """Get recent server logs."""
        return "Log access not implemented in stdio mode"

    # Register Modular Tools (formerly V9)
    helpers = {
        "get_project_root_or_error": get_project_root_or_error,
        "detect_project_root": detect_project_root,
        "configure_runtime": configure_runtime_for_project,
    }
    # register_v9_tools(instance.mcp, audited, helpers)
    register_workspace_tools(instance.mcp, audited, helpers)
    register_plugin_tools(instance.mcp, audited, helpers)
    register_assistant_tools(instance.mcp, audited, helpers)
    # register_knowledge_tools(instance.mcp, audited, helpers)

    # Register V10 Tools (RAG, Multi-Agent, Shadow Mode)
    register_v10_tools(instance.mcp, audited, helpers)

    # Register Advanced Tools (Security, Transactions, Background, Context)
    register_advanced_tools(instance.mcp)

    # Register Discovery Resources
    register_discovery_resources(instance.mcp)

    # Register Prompts
    register_prompts(instance.mcp, helpers)

    # Register Vibe Coder Pro Tools
    register_vibe_tools(instance.mcp, audited, helpers)

    # Register Intelligence Tools (V10.23: PredictiveAnalyzer, AdaptiveCache, Session Context)
    register_intelligence_tools(instance.mcp, audited, helpers)

    return instance.mcp


def create_server():
    """
    Create and return a FastMCP server instance for Smithery deployment.

    This function is called by Smithery to get the server instance.
    It must be decorated with @smithery.server() and return a FastMCP instance.

    Note: Smithery uses HTTP transport, not stdio.
    """
    mcp_instance = get_server_instance()

    if os.environ.get("BORING_MCP_DEBUG") == "1":
        sys.stderr.write("[boring-mcp] Creating server for Smithery...\n")
        sys.stderr.write(f"[boring-mcp] Registered tools: {len(mcp_instance._tools)}\n")

    return mcp_instance


# Apply Smithery decorator if available
if SMITHERY_AVAILABLE and smithery is not None:
    create_server = smithery.server()(create_server)


def run_server():
    """
    Main entry point for the Boring MCP server (stdio transport).
    Used for local CLI execution: boring-mcp
    """
    # 0. Set MCP Mode flag to silence tool outputs (e.g. health check)
    os.environ["BORING_MCP_MODE"] = "1"

    if not instance.MCP_AVAILABLE:
        sys.stderr.write(
            "Error: 'fastmcp' not found. Install with: pip install boring-aicoding[mcp]\n"
        )
        sys.exit(1)

    # 1. Install stdout interceptor immediately
    interceptors.install_interceptors()

    # --- Renaissance V2: Core Tools Registration ---
    # register_core_tools registers tools that must ALWAYS be exposed
    import boring.mcp.tools.core  # noqa: F401
    # --- End Renaissance ---

    # 2. Register Modular Tools (formerly V9)
    helpers = {
        "get_project_root_or_error": get_project_root_or_error,
        "detect_project_root": detect_project_root,
        "configure_runtime": configure_runtime_for_project,
    }
    # register_v9_tools(instance.mcp, audited, helpers)
    register_workspace_tools(instance.mcp, audited, helpers)
    register_plugin_tools(instance.mcp, audited, helpers)
    register_assistant_tools(instance.mcp, audited, helpers)
    # knowledge tools registered via import side-effect (top-level)
    from .tools import knowledge  # noqa: F401 - V10: Knowledge System (boring_learn)

    register_v10_tools(instance.mcp, audited, helpers)

    # 3.5 [ONE DRAGON] Register Flow Tool
    import boring.mcp.tools.flow_tool  # noqa: F401

    # 4. Register Advanced Tools (Security, Transactions, Background, Context)
    register_advanced_tools(instance.mcp)

    # 5. Register Discovery Resources (Capabilities)
    register_discovery_resources(instance.mcp)

    # Register Prompts
    register_prompts(instance.mcp, helpers)

    # Register Vibe Coder Pro Tools
    register_vibe_tools(instance.mcp, audited, helpers)

    # Register Intelligence Tools (V10.23: PredictiveAnalyzer, AdaptiveCache, Session Context)
    register_intelligence_tools(instance.mcp, audited, helpers)

    # Register SpecKit Tools (Spec-Driven Development Workflows)
    from .speckit_tools import register_speckit_tools

    register_speckit_tools(instance.mcp, audited, helpers)

    # Register Brain Tools (V10.23 Enhanced: boring_brain_health, boring_global_*)
    from .brain_tools import register_brain_tools

    register_brain_tools(instance.mcp, audited, helpers)

    # Register Skills Tools
    # V11.4: Register Metrics & Guidance Tools (Project Jarvis)
    import boring.mcp.tools.metrics  # noqa: F401
    import boring.mcp.tools.skills  # noqa: F401

    # V10.24: Register Tool Router (Universal Natural Language Gateway)
    # Refactored in V11.4 (Renaissance) to dedicated module
    from .tools.router_tools import register_router_tools
    register_router_tools(instance.mcp)

    profile = get_profile()
    get_tool_router()

    # V10.29: Post-registration PROMPT filtering based on profile
    # FastMCP stores prompts in _prompts dict. We filter it directly.
    # This prevents context window bloat (52 prompts -> ~5 in LITE)
    from .tool_profiles import should_register_prompt

    if profile.prompts is not None:  # None means FULL profile (all prompts)
        # Access internal prompts storage
        # FastMCP 2.x usually has _prompts on the instance
        prompts_dict = getattr(instance.mcp, "_prompts", None)

        if prompts_dict and isinstance(prompts_dict, dict):
            original_prompt_count = len(prompts_dict)
            prompts_to_remove = [
                name for name in prompts_dict.keys() if not should_register_prompt(name, profile)
            ]

            for name in prompts_to_remove:
                del prompts_dict[name]

            filtered_prompt_count = len(prompts_dict)
            sys.stderr.write(
                f"[boring-mcp] 📝 Prompt Filter: {original_prompt_count} → {filtered_prompt_count} prompts "
                f"(saved context for Vibe Coding)\n"
            )
        else:
            sys.stderr.write(
                "[boring-mcp] ⚠️ Could not filter prompts: internal structure changed\n"
            )

    # V10.26: Cache all tools BEFORE filtering for boring_discover
    # FastMCP 2.x uses various internal structures; use robust accessor
    tools_dict = _get_tools_robust(instance.mcp)
    instance._all_tools_cache = dict(tools_dict)

    # V10.26: Post-registration tool filtering based on profile
    # This removes tools not in the profile to reduce context window usage
    if profile.tools:  # Non-empty means we should filter (empty = FULL profile)
        # Always keep these essential tools regardless of profile
        essential_tools = {"boring", "boring_help"}
        allowed_tools = set(profile.tools) | essential_tools

        # Get current tools and filter
        original_count = len(tools_dict)
        tools_to_remove = [name for name in tools_dict.keys() if name not in allowed_tools]
        for tool_name in tools_to_remove:
            if tool_name in tools_dict:
                del tools_dict[tool_name]

        filtered_count = len(_get_tools_robust(instance.mcp))
        sys.stderr.write(
            f"[boring-mcp] 🎛️ Profile Filter: {original_count} → {filtered_count} tools "
            f"(saved ~{(original_count - filtered_count) * 50} tokens)\n"
        )

    # Vibe Coder Tutorial Hook - Show MCP intro on first launch
    try:
        from ..tutorial import TutorialManager

        TutorialManager().show_tutorial("mcp_intro")
    except Exception:
        pass  # Fail silently if tutorial not available

    # 4. Configured logging
    with _configure_logging():
        # Always check for optional RAG dependencies at startup
        import importlib.util

        rag_ok = importlib.util.find_spec("chromadb") and importlib.util.find_spec(
            "sentence_transformers"
        )
        if not rag_ok:
            sys.stderr.write(
                f"[boring-mcp] ⚠️ RAG features unavailable: Missing dependencies.\n"
                f"[boring-mcp] To enable RAG, run:\n"
                f"    {sys.executable} -m pip install boring-aicoding[vector]\n"
            )

        # V10.24: Show profile info
        sys.stderr.write(
            f"[boring-mcp] 🎛️ Tool Profile: {profile.name} ({len(profile.tools) or 'all'} tools)\n"
        )

        if os.environ.get("BORING_MCP_DEBUG") == "1":
            sys.stderr.write("[boring-mcp] Server starting...\n")
            sys.stderr.write(f"[boring-mcp] Python: {sys.executable}\n")
            sys.stderr.write(f"[boring-mcp] Registered tools: {len(instance.mcp._tools)}\n")
            if rag_ok:
                sys.stderr.write(
                    "[boring-mcp] ✅ RAG dependencies found (chromadb, sentence_transformers)\n"
                )

        # 3. Mark MCP as started (allows JSON-RPC traffic)
        if hasattr(sys.stdout, "mark_mcp_started"):
            sys.stdout.mark_mcp_started()

        # 4. Run the server
        # Explicitly use stdio transport
        try:
            instance.mcp.run(transport="stdio")
        except Exception as e:
            sys.stderr.write(f"[boring-mcp] Critical Error: {e}\n")
            sys.exit(1)


if __name__ == "__main__":
    run_server()
