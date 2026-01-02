# ==============================================================================
# Boring MCP Server - Docker Configuration
# ==============================================================================
# Multi-stage build optimized for Python MCP servers
# Based on 2025 Docker best practices
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies
# ------------------------------------------------------------------------------
FROM python:3.9-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy build configuration and source
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install the package with MCP dependencies
# We install "." to ensure the "boring" package is recognized correctly
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[mcp]" && \
    pip install --no-cache-dir .

# ------------------------------------------------------------------------------
# Stage 2: Runtime - Minimal production image
# ------------------------------------------------------------------------------
FROM python:3.9-slim AS runtime

LABEL maintainer="Boring206 <C112156246@nkust.edu.tw>"
LABEL description="Boring MCP Server - Autonomous AI Development Agent"
LABEL version="5.1.0"

# Create non-root user for security
RUN groupadd --gid 1000 boring && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home boring

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy essential files
COPY --chown=boring:boring src/ ./src/
COPY --chown=boring:boring templates/ ./templates/

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    BORING_MCP_MODE=1 \
    # Ensure PYTHONPATH includes /app/src to find the module if needed
    PYTHONPATH="/app/src:${PYTHONPATH}"

# Switch to non-root user
USER boring

# Health check
# Note: Since boring.mcp_server intercepts stdout, we use a custom check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import boring.mcp_server; print('OK')" || exit 1

# Default command - run MCP server
# Using module invocation to ensure proper relative imports
CMD ["python", "-m", "boring.mcp_server"]
