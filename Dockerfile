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

# Install the project and dependencies
# Using -e . isn't necessary for a production image, direct install is better
RUN pip install --no-cache-dir .

# Environment variables
# Ensure unbuffered output for logging
ENV PYTHONUNBUFFERED=1
# Set BORING_MCP_MODE to suppress Rich output and force JSON-RPC
ENV BORING_MCP_MODE=1

# Run the MCP server command installed by pip
CMD ["boring-mcp"]
