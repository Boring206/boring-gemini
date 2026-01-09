# Use a lightweight Python base image
FROM python:3.14-slim

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

# Install the project with lightweight MCP dependencies (without heavy torch/chromadb)
# For full RAG support, use ".[mcp]" instead (requires ~4GB more disk space)
RUN pip install --no-cache-dir ".[mcp-lite]"

# Note: HEALTHCHECK removed to prevent build-time failures on Smithery
# Smithery handles container health separately

# Document the port
EXPOSE 8000

# Run the HTTP server module
CMD ["python", "-m", "boring.mcp.http"]
