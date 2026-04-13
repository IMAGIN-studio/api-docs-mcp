# syntax=docker/dockerfile:1
FROM python:3.12-slim

# OCI labels — link image to the GitHub repo so it appears under Packages
LABEL org.opencontainers.image.source="https://github.com/IMAGIN-studio/api-docs-mcp"
LABEL org.opencontainers.image.description="IMAGIN.studio API Docs MCP Server — semantic search over IMAGIN.studio documentation"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.vendor="IMAGIN.studio"
LABEL org.opencontainers.image.url="https://github.com/IMAGIN-studio/api-docs-mcp"
LABEL org.opencontainers.image.documentation="https://github.com/IMAGIN-studio/api-docs-mcp/blob/main/SETUP.md"

WORKDIR /app

# System deps for fastembed / lancedb (onnxruntime needs libgomp)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install the package from PyPI
RUN pip install --no-cache-dir imagin-studio-api-docs-mcp

ENTRYPOINT ["imagin-studio-api-docs-mcp"]
