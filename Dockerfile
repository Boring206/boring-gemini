# Use a lightweight Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install git (required for boring-gemini functionality)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy project configuration files first for caching
COPY pyproject.toml README.md ./

# Copy source code
COPY src src

# Install the project with MCP dependencies
RUN pip install --no-cache-dir ".[mcp]"

# Environment variables
# Ensure unbuffered output for logging
ENV PYTHONUNBUFFERED=1
# Set BORING_MCP_MODE to suppress Rich output and force JSON-RPC
ENV BORING_MCP_MODE=1
# Set the port for Smithery HTTP transport
ENV PORT=8000

# Expose the HTTP port
EXPOSE 8000

# Run the MCP server with HTTP transport for Smithery
# Smithery expects HTTP transport on the specified PORT
CMD ["python", "-c", "from boring.mcp.server import create_server; server = create_server(); server.run(transport='sse', port=8000)"]
