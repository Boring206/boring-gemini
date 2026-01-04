#!/usr/bin/env python3
"""
HTTP entry point for Smithery deployment.

This module provides an HTTP/SSE server for the Boring MCP server,
required for Smithery remote hosting which only supports HTTP transport.

Includes .well-known endpoints for Smithery server discovery:
- /.well-known/mcp.json - MCP Server Card (metadata and capabilities)
- /.well-known/mcp-config - Configuration schema
"""

import os
import sys
import json
import logging

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# MCP Server Card - metadata for Smithery discovery
MCP_SERVER_CARD = {
    "name": "boring-gemini",
    "version": "5.2.0",
    "description": "Boring MCP Server - Autonomous AI development loop with SpecKit workflows",
    "vendor": {
        "name": "Boring for Gemini"
    },
    "capabilities": {
        "tools": True,
        "resources": True,
        "prompts": False
    },
    "authentication": {
        "type": "none"
    },
    "documentation": "https://github.com/user/boring-gemini#readme"
}

# Configuration schema (matches smithery.yaml)
MCP_CONFIG_SCHEMA = {
    "title": "MCP Session Configuration",
    "description": "Schema for the /mcp endpoint configuration",
    "x-query-style": "dot+bracket",
    "type": "object",
    "properties": {},
    "additionalProperties": False
}


def create_app():
    """Create Starlette app with .well-known endpoints and MCP SSE routes."""
    try:
        from starlette.applications import Starlette
        from starlette.responses import JSONResponse
        from starlette.routing import Route, Mount
    except ImportError:
        logger.error("Starlette not found. Install with: pip install starlette")
        return None
    
    # Import MCP server
    from boring.mcp.server import get_server_instance
    mcp = get_server_instance()
    
    # Safe tool count
    tool_count = len(getattr(mcp, '_tools', getattr(mcp, 'tools', {})))
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
    
    # Get SSE app from FastMCP
    try:
        sse_app = mcp.sse_app()
    except AttributeError:
        # Fallback for older FastMCP versions
        logger.warning("FastMCP.sse_app() not available, using direct run")
        return None
    
    routes = [
        Route("/.well-known/mcp.json", mcp_server_card),
        Route("/.well-known/mcp-config", mcp_config),
        Route("/health", health),
        Mount("/", app=sse_app),  # Mount MCP SSE at root
    ]
    
    return Starlette(routes=routes)


def main():
    """Run the MCP server with HTTP/SSE transport for Smithery."""
    # Set environment
    os.environ["BORING_MCP_MODE"] = "1"
    
    # Get port from environment (Smithery sets this)
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting Boring MCP HTTP server on {host}:{port}")
    
    try:
        app = create_app()
        
        if app is not None:
            # Run with Uvicorn
            import uvicorn
            uvicorn.run(app, host=host, port=port, log_level="info")
        else:
            # Fallback: Use FastMCP's built-in SSE run
            from boring.mcp.server import get_server_instance
            mcp = get_server_instance()
            tool_count = len(getattr(mcp, '_tools', getattr(mcp, 'tools', {})))
            logger.info(f"Registered tools: {tool_count}")
            mcp.run(transport="sse", host=host, port=port)
        
    except Exception as e:
        logger.error(f"Failed to start HTTP server: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
