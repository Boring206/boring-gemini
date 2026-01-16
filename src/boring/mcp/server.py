"""
Boring MCP Server - Optimized for Fast Startup (V14.0)

Target: < 300ms startup time

Optimization Strategies:
1. Lazy imports for heavy modules (chromadb, torch, etc.)
2. Deferred tool registration until first use
3. Profile-based tool filtering to reduce initial load
4. Background pre-warming for optional dependencies
"""

import logging
import os
import sys
import warnings
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Suppress warnings immediately to prevent stderr pollution
warnings.simplefilter("ignore")

# Install interceptors first - this is lightweight
from . import instance, interceptors

interceptors.install_interceptors()

# Core imports - these are essential and lightweight
from boring.services.audit import audited  # V14: Enterprise Audit Service
from boring.utils.i18n import T

# V10.24: Tool Profiles and Router - lightweight
from .tool_profiles import ToolRegistrationFilter, get_profile
from .tool_router import get_tool_router

# Utils - lightweight
from .utils import configure_runtime_for_project, detect_project_root, get_project_root_or_error

# Deferred imports for tool registration functions
# These are imported lazily to speed up startup
_TOOL_REGISTRARS_LOADED = False
_tool_registrars = {}


def _load_tool_registrars():
    """Lazy load tool registration functions."""
    global _TOOL_REGISTRARS_LOADED, _tool_registrars

    if _TOOL_REGISTRARS_LOADED:
        return _tool_registrars

    from .intelligence_tools import register_intelligence_tools
    from .prompts import register_prompts
    from .tools.advanced import register_advanced_tools
    from .tools.assistant import register_assistant_tools
    from .tools.discovery import register_discovery_resources
    from .tools.plugins import register_plugin_tools
    from .tools.vibe import register_vibe_tools
    from .tools.workspace import register_workspace_tools
    from .v10_tools import register_v10_tools

    _tool_registrars = {
        "intelligence": register_intelligence_tools,
        "prompts": register_prompts,
        "advanced": register_advanced_tools,
        "assistant": register_assistant_tools,
        "discovery": register_discovery_resources,
        "plugins": register_plugin_tools,
        "vibe": register_vibe_tools,
        "workspace": register_workspace_tools,
        "v10": register_v10_tools,
    }

    _TOOL_REGISTRARS_LOADED = True
    return _tool_registrars


def _import_tool_modules():
    """Import tool modules that use decorators."""
    # These imports trigger @mcp.tool decorators
    from .tools import (
        batch,  # noqa: F401 - V13.0: Batch Execution
        compare,  # noqa: F401 - V13.0: File Comparison
        git,  # noqa: F401
        session,  # noqa: F401 - V10.25: Vibe Session
    )


# Try to import Smithery decorator for HTTP deployment
try:
    from smithery.decorators import smithery

    SMITHERY_AVAILABLE = True
except ImportError:
    SMITHERY_AVAILABLE = False
    smithery = None


def _get_tool_filter() -> ToolRegistrationFilter:
    """Get tool filter based on current profile configuration."""
    profile_name = get_profile().name
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


def _register_all_tools(mcp_instance, audited, helpers):
    """Register all MCP tools in a unified manner.

    Optimized for startup time by using lazy-loaded registrars.
    """
    # Load registrars lazily
    registrars = _load_tool_registrars()

    # Import tool modules with decorators
    _import_tool_modules()

    # --- Renaissance V2: Core Tools Registration ---
    import boring.mcp.tools.core  # noqa: F401
    import boring.mcp.tools.evaluation  # noqa: F401
    import boring.mcp.tools.verification  # noqa: F401

    # Register Modular Tools (formerly V9)
    registrars["workspace"](mcp_instance, audited, helpers)
    registrars["plugins"](mcp_instance, audited, helpers)
    registrars["assistant"](mcp_instance, audited, helpers)

    # Knowledge Tools (Unified Registration)
    from .tools.knowledge import register_knowledge_tools

    register_knowledge_tools(mcp_instance, audited, helpers)

    # Register V10 Tools (RAG, Multi-Agent, Shadow Mode)
    registrars["v10"](mcp_instance, audited, helpers)

    # 3.5 [ONE DRAGON] Register Flow Tool
    import boring.mcp.tools.flow_tool  # noqa: F401

    # Register Advanced Tools (Security, Transactions, Background, Context)
    registrars["advanced"](mcp_instance)

    # Register Discovery Resources
    registrars["discovery"](mcp_instance)

    # Register Prompts
    registrars["prompts"](mcp_instance, helpers)

    # Register Vibe Coder Pro Tools
    registrars["vibe"](mcp_instance, audited, helpers)

    # Register Intelligence Tools (V10.23: PredictiveAnalyzer, AdaptiveCache, Session Context)
    registrars["intelligence"](mcp_instance, audited, helpers)

    # Register Auto-Fix tool (depends on run_boring and boring_verify)
    from boring.auto_fix import create_auto_fix_tool
    from boring.mcp.tools.core import run_boring
    from boring.mcp.tools.git import boring_hooks_install, boring_visualize
    from boring.mcp.tools.verification import boring_verify

    create_auto_fix_tool(
        mcp_instance,
        audited,
        run_boring,
        boring_verify,
        helpers.get("get_project_root_or_error"),
    )

    # Ensure legacy Git tools are exposed in full profile
    mcp_instance.tool(
        description="Install Git hooks", annotations={"readOnlyHint": False, "idempotentHint": True}
    )(boring_hooks_install)
    mcp_instance.tool(
        description="Generate architecture diagram from codebase",
        annotations={"readOnlyHint": True},
    )(boring_visualize)

    # Register SpecKit Tools (Spec-Driven Development Workflows)
    from .speckit_tools import register_speckit_tools

    register_speckit_tools(mcp_instance, audited, helpers)

    # Register Brain Tools (V10.23 Enhanced: boring_brain_health, boring_global_*)
    from .brain_tools import register_brain_tools

    register_brain_tools(mcp_instance, audited, helpers)

    # Register Skills Tools
    import boring.mcp.tools.metrics  # noqa: F401
    import boring.mcp.tools.skills  # noqa: F401

    # Register Tool Router
    from .tools.router_tools import register_router_tools

    register_router_tools(mcp_instance)


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

    # V14.0 Fix: Support FastMCP get_tools() method or iterators
    if hasattr(mcp, "get_tools") and callable(mcp.get_tools):
        try:
            tools = mcp.get_tools()
            return {t.name: t for t in tools}
        except Exception as e:
            logger.debug("Failed to get tools via get_tools(): %s", e)

    return {}


def _log_stderr(message_key: str, **kwargs):
    sys.stderr.write(T(message_key, **kwargs))


def get_server_instance():
    """
    Get the configured FastMCP server instance (raw).
    Use this for direct access without Smithery decorators (e.g. for http.py).
    """
    # <!-- CACHEABLE_CONTENT_START -->
    os.environ["BORING_MCP_MODE"] = "1"

    if not instance.MCP_AVAILABLE:
        raise RuntimeError("'fastmcp' not found. Install with: pip install boring-aicoding[mcp]")

    # Register Resources
    @instance.mcp.resource("boring://logs")
    def get_logs() -> str:
        """Get recent server logs."""
        return "Log access not implemented in stdio mode"

    # Common Helpers
    helpers = {
        "get_project_root_or_error": get_project_root_or_error,
        "detect_project_root": detect_project_root,
        "configure_runtime": configure_runtime_for_project,
    }

    # Unified Tool Registration
    _register_all_tools(instance.mcp, audited, helpers)

    # <!-- CACHEABLE_CONTENT_END -->
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
        _log_stderr("mcp_server_creating")
        try:
            tool_count = len(_get_tools_robust(mcp_instance))
            _log_stderr("mcp_server_registered_tools", count=tool_count)
        except Exception as e:
            logger.debug("Failed to count tools in create_server: %s", e)

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
        _log_stderr("mcp_fastmcp_missing")
        sys.exit(1)

    # 1. Install stdout interceptor immediately
    interceptors.install_interceptors()

    # Helpers
    helpers = {
        "get_project_root_or_error": get_project_root_or_error,
        "detect_project_root": detect_project_root,
        "configure_runtime": configure_runtime_for_project,
    }

    # 2. Unified Tool Registration
    _register_all_tools(instance.mcp, audited, helpers)

    # 3. Profile & Router Setup
    profile = get_profile()
    get_tool_router()

    # V14.0: Hot Reload (Dev Mode)
    if os.environ.get("BORING_MCP_DEV") == "1":
        try:
            from .reloader import start_reloader

            start_reloader(instance.mcp)
        except Exception as e:
            _log_stderr("mcp_hot_reload_warning", error=str(e))

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
            _log_stderr(
                "mcp_prompt_filter",
                original=original_prompt_count,
                filtered=filtered_prompt_count,
            )
        else:
            _log_stderr("mcp_prompt_filter_failed")

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
        _log_stderr(
            "mcp_profile_filter",
            original=original_count,
            filtered=filtered_count,
            saved_tokens=(original_count - filtered_count) * 50,
        )

    # Vibe Coder Tutorial Hook - Show MCP intro on first launch
    try:
        from ..tutorial import TutorialManager

        TutorialManager().show_tutorial("mcp_intro")
    except Exception as e:
        logger.debug("MCP tutorial hint unavailable: %s", e)

    # 4. Configured logging
    with _configure_logging():
        # Always check for optional RAG dependencies at startup
        import importlib.util

        rag_ok = importlib.util.find_spec("chromadb") and importlib.util.find_spec(
            "sentence_transformers"
        )
        if not rag_ok:
            _log_stderr(
                "mcp_rag_missing",
                python=sys.executable,
            )

        # V10.24: Show profile info
        tool_count = len(profile.tools) if profile.tools else "all"
        _log_stderr("mcp_tool_profile", profile=profile.name, tool_count=tool_count)

        if os.environ.get("BORING_MCP_DEBUG") == "1":
            _log_stderr("mcp_server_starting")
            _log_stderr("mcp_server_python", python=sys.executable)
            try:
                _log_stderr(
                    "mcp_server_registered_tools",
                    count=len(_get_tools_robust(instance.mcp)),
                )
            except Exception as e:
                logger.debug("Failed to count tools in run_server: %s", e)
            if rag_ok:
                _log_stderr("mcp_rag_found")

        # 3. Mark MCP as started (allows JSON-RPC traffic)
        if hasattr(sys.stdout, "mark_mcp_started"):
            sys.stdout.mark_mcp_started()

        # 4. Run the server
        # Explicitly use stdio transport
        try:
            instance.mcp.run(transport="stdio")
        except Exception as e:
            _log_stderr("mcp_critical_error", error=str(e))
            sys.exit(1)


if __name__ == "__main__":
    run_server()
