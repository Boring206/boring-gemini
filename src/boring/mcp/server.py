import sys
import logging
import os
from contextlib import contextmanager

from . import interceptors
# Install interceptors immediately BEFORE any other imports to catch early stdout pollution
interceptors.install_interceptors()

# Import all modules to register tools with FastMCP
from . import instance
from . import resources
# Import tools packages to trigger decorators
from .tools import (
    core,
    verification,
    speckit,
    workflow,
    knowledge,
    patching,
    git,
    integration,
    evaluation
)

@contextmanager
def _configure_logging():
    """Configure logging to avoid polluting stdout."""
    # Force generic logs to stderr
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format='[%(levelname)s] %(message)s'
    )
    # Silence specific noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    yield

def run_server():
    """
    Main entry point for the Boring MCP server.
    """
    if not instance.MCP_AVAILABLE:
        sys.stderr.write("Error: 'fastmcp' not found. Install with: pip install fastmcp\n")
        sys.exit(1)

    # 1. Configured logging
    with _configure_logging():
        if os.environ.get("BORING_MCP_DEBUG") == "1":
            sys.stderr.write("[boring-mcp] Server starting...\n")
            sys.stderr.write(f"[boring-mcp] Python: {sys.executable}\n")
            sys.stderr.write(f"[boring-mcp] Registered tools: {len(instance.mcp._tools)}\n")
            
        # 3. Mark MCP as started (allows JSON-RPC traffic)
        if hasattr(sys.stdout, 'mark_mcp_started'):
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
