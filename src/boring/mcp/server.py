import logging
import os
import sys
from contextlib import contextmanager

from . import interceptors

# Install interceptors immediately BEFORE any other imports to catch early stdout pollution
interceptors.install_interceptors()

# Import all modules to register tools with FastMCP
from ..audit import audited  # Moved to top-level to avoid import issues in tests
from . import instance
from .prompts import register_prompts

# Import legacy tools to trigger @mcp.tool registration
from .tools.advanced import register_advanced_tools
from .tools.discovery import register_discovery_resources

# Import tools packages to trigger decorators
from .utils import detect_project_root, get_project_root_or_error
from .v9_tools import register_v9_tools
from .v10_tools import register_v10_tools

# Try to import Smithery decorator for HTTP deployment
try:
    from smithery.decorators import smithery

    SMITHERY_AVAILABLE = True
except ImportError:
    SMITHERY_AVAILABLE = False
    smithery = None


@contextmanager
def _configure_logging():
    """Configure logging to avoid polluting stdout."""
    # Force generic logs to stderr
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="[%(levelname)s] %(message)s")
    # Silence specific noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    yield


def get_server_instance():
    """
    Get the configured FastMCP server instance (raw).
    Use this for direct access without Smithery decorators (e.g. for http.py).
    """
    os.environ["BORING_MCP_MODE"] = "1"

    if not instance.MCP_AVAILABLE:
        raise RuntimeError("'fastmcp' not found. Install with: pip install fastmcp")

    # Register Resources
    @instance.mcp.resource("boring://logs")
    def get_logs() -> str:
        """Get recent server logs."""
        return "Log access not implemented in stdio mode"

    # Register V9 Tools
    helpers = {
        "get_project_root_or_error": get_project_root_or_error,
        "detect_project_root": detect_project_root,
    }
    register_v9_tools(instance.mcp, audited, helpers)

    # Register V10 Tools (RAG, Multi-Agent, Shadow Mode)
    register_v10_tools(instance.mcp, audited, helpers)

    # Register Advanced Tools (Security, Transactions, Background, Context)
    register_advanced_tools(instance.mcp)

    # Register Discovery Resources
    register_discovery_resources(instance.mcp)

    # Register Prompts
    register_prompts(instance.mcp)

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
        sys.stderr.write("Error: 'fastmcp' not found. Install with: pip install fastmcp\n")
        sys.exit(1)

    # 1. Install stdout interceptor immediately
    # This prevents any print() statement from corrupting the JSON-RPC stream
    interceptors.install_interceptors()

    # 2. Register V9 Tools
    helpers = {
        "get_project_root_or_error": get_project_root_or_error,
        "detect_project_root": detect_project_root,
    }
    register_v9_tools(instance.mcp, audited, helpers)

    # 3. Register V10 Tools (RAG, Multi-Agent, Shadow Mode)
    register_v10_tools(instance.mcp, audited, helpers)

    # 4. Register Advanced Tools (Security, Transactions, Background, Context)
    register_advanced_tools(instance.mcp)

    # 5. Register Discovery Resources (Capabilities)
    register_discovery_resources(instance.mcp)

    # Register Prompts
    register_prompts(instance.mcp)

    # 4. Configured logging
    with _configure_logging():
        if os.environ.get("BORING_MCP_DEBUG") == "1":
            sys.stderr.write("[boring-mcp] Server starting...\n")
            sys.stderr.write(f"[boring-mcp] Python: {sys.executable}\n")
            sys.stderr.write(f"[boring-mcp] Registered tools: {len(instance.mcp._tools)}\n")

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
