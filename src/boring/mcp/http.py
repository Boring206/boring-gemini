#!/usr/bin/env python3
"""
HTTP entry point for Smithery deployment.

This module provides an HTTP/SSE server for the Boring MCP server,
required for Smithery remote hosting which only supports HTTP transport.

Includes .well-known endpoints for Smithery server discovery:
- /.well-known/mcp.json - MCP Server Card (metadata and capabilities)
- /.well-known/mcp-config - Configuration schema
"""

import logging
import os
import sys

# Configure logging to stderr
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# MCP Server Card - metadata for Smithery discovery
MCP_SERVER_CARD = {
    "name": "boring-gemini",
    "version": "11.2.2",
    "description": "Boring Vibecoder Assistant: An AI-powered development support tool with NotebookLM optimizations.",
    "vendor": {"name": "Boring for Gemini"},
    "capabilities": {"tools": True, "resources": True, "prompts": True},
    "authentication": {"type": "none"},
    "documentation": "https://github.com/Boring206/boring-gemini#readme",
}

# Configuration schema (matches smithery.yaml)
MCP_CONFIG_SCHEMA = {
    "title": "MCP Session Configuration",
    "description": "Schema for the /mcp endpoint configuration",
    "x-query-style": "dot+bracket",
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}


def _get_tools_robust(mcp):
    """Robustly extract the tools dictionary from various FastMCP/MCP server versions."""
    for attr in ["_tools", "tools"]:
        val = getattr(mcp, attr, None)
        if isinstance(val, dict):
            return val
    if hasattr(mcp, "_tool_manager"):
        tm = mcp._tool_manager
        for attr in ["_tools", "tools"]:
            val = getattr(tm, attr, None)
            if isinstance(val, dict):
                return val
    return {}


def create_app():
    """Create Starlette app with .well-known endpoints and MCP HTTP routes."""
    try:
        from starlette.applications import Starlette
        from starlette.responses import JSONResponse
        from starlette.routing import Mount, Route
    except ImportError:
        logger.error("Starlette not found. Install with: pip install starlette")
        return None

    # Import MCP server
    from boring.mcp.server import get_server_instance

    mcp = get_server_instance()

    # Safe tool count (FastMCP 2.x uses various internal structures)
    tools_dict = _get_tools_robust(mcp)
    tool_count = len(tools_dict)
    logger.info(f"Registered tools: {tool_count}")

    # .well-known endpoints
    async def mcp_server_card(request):
        """Return MCP Server Card for Smithery discovery."""
        return JSONResponse(MCP_SERVER_CARD)

    async def mcp_config(request):
        """Return MCP configuration schema."""
        return JSONResponse(MCP_CONFIG_SCHEMA)

    async def health(request):
        """Health check endpoint."""
        return JSONResponse({"status": "ok", "tools": tool_count})

    # Get HTTP app from FastMCP (correct method is http_app, not sse_app)
    try:
        # FastMCP 2.0+ uses http_app() for Streamable HTTP transport
        mcp_http = mcp.http_app(path="/mcp")
        logger.info("Using FastMCP http_app() for HTTP transport")
    except AttributeError:
        # Fallback for older FastMCP versions - try sse_app
        try:
            mcp_http = mcp.sse_app()
            logger.info("Using FastMCP sse_app() for SSE transport (legacy)")
        except AttributeError:
            logger.warning("FastMCP http_app() and sse_app() not available")
            return None

    routes = [
        Route("/.well-known/mcp.json", mcp_server_card),
        Route("/.well-known/mcp-config", mcp_config),
        Route("/health", health),
        Mount("/", app=mcp_http),  # Mount MCP HTTP at root
    ]

    # Use mcp_http's lifespan if available
    lifespan = getattr(mcp_http, "lifespan", None)

    return Starlette(routes=routes, lifespan=lifespan)


def main():
    """Run the MCP server with HTTP/SSE transport for Smithery."""
    # Set environment
    os.environ["BORING_MCP_MODE"] = "1"

    # Get port from environment (Smithery sets this)
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")  # nosec B104: Intended for container binding

    logger.info(f"Starting Boring MCP HTTP server on {host}:{port}")

    try:
        app = create_app()

        if app is not None:
            # Run with Uvicorn
            import uvicorn

            # Ensure host is string and port is int to avoid getaddrinfo TypeErrors
            host_str = str(host)
            port_int = int(port)
            uvicorn.run(app, host=host_str, port=port_int, log_level="info")
        else:
            # Fallback: Use FastMCP's built-in HTTP run
            from boring.mcp.server import get_server_instance

            mcp = get_server_instance()
            tool_count = len(getattr(mcp, "_tools", getattr(mcp, "tools", {})))
            logger.info(f"Registered tools: {tool_count}")
            mcp.run(transport="http", host=str(host), port=int(port))

    except Exception as e:
        logger.error(f"Failed to start HTTP server: {e}")
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
