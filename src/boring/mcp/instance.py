from boring.core.dependencies import DependencyManager

# Create MCP server instance lazily or via guard
if DependencyManager.check_mcp():
    from fastmcp import FastMCP

    mcp = FastMCP(name="Boring AI Development Agent")
    MCP_AVAILABLE = True
else:
    mcp = None
    MCP_AVAILABLE = False
