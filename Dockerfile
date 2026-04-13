# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

# System deps for fastembed / lancedb (onnxruntime needs libgomp)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install the package from PyPI
RUN pip install --no-cache-dir imagin-studio-api-docs-mcp

ENTRYPOINT ["imagin-studio-api-docs-mcp"]
