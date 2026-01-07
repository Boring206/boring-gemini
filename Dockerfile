# Use a lightweight Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV BORING_MCP_MODE=1

# Install system dependencies (git for boring-gemini functionality)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project configuration files first for caching
COPY pyproject.toml README.md ./

# Copy source code
COPY src src

# Install the project with MCP dependencies (Core + MCP)
RUN pip install --no-cache-dir ".[mcp]"

# Health check endpoint (use port 8000, Smithery sets PORT env at runtime)
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Document the port
EXPOSE 8000

# Run the HTTP server module
CMD ["python", "-m", "boring.mcp.http"]
