try:
    from fastmcp import FastMCP

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    FastMCP = None

# Create MCP server instance
if MCP_AVAILABLE:
    mcp = FastMCP(name="Boring AI Development Agent")
else:
    mcp = None
