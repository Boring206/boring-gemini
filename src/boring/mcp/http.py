#!/usr/bin/env python3
"""
HTTP entry point for Smithery deployment.

This module provides an HTTP/SSE server for the Boring MCP server,
required for Smithery remote hosting which only supports HTTP transport.
"""

import os
import sys
import logging

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the MCP server with HTTP/SSE transport for Smithery."""
    # Set environment
    os.environ["BORING_MCP_MODE"] = "1"
    
    # Get port from environment (Smithery sets this)
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting Boring MCP HTTP server on {host}:{port}")
    
    try:
        # Import and setup server
        from boring.mcp.server import create_server
        
        mcp = create_server()
        
        logger.info(f"Registered tools: {len(mcp._tools)}")
        
        # Run with SSE transport (Streamable HTTP for MCP)
        # FastMCP supports 'sse' transport for HTTP/SSE
        mcp.run(transport="sse", host=host, port=port)
        
    except Exception as e:
        logger.error(f"Failed to start HTTP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
