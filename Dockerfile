# syntax=docker/dockerfile:1
FROM python:3.12.15-slim-trixie@sha256:a0f57064cbdcd6285fa45f51237ab0b35ea8ebaed06a1f5973e89e19dfb86704

# OCI labels — link image to the GitHub repo so it appears under Packages
LABEL org.opencontainers.image.source="https://github.com/IMAGIN-studio/api-docs-mcp"
LABEL org.opencontainers.image.description="Give your AI coding assistant direct access to the IMAGIN.studio vehicle imagery API docs."
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

# Install the package from this commit (not from PyPI), so the image always
# matches its version tag even while the PyPI release is still publishing.
# PIP_CONSTRAINT pins every dependency and the build backend to
# requirements.lock (every pin is at least two weeks old; see `make lock`).
COPY pyproject.toml SETUP.md LICENSE NOTICE MANIFEST.in requirements.lock /tmp/build/
COPY src/ /tmp/build/src/
RUN PIP_CONSTRAINT=/tmp/build/requirements.lock pip install --no-cache-dir /tmp/build \
    && rm -rf /tmp/build

ENTRYPOINT ["imagin-studio-api-docs-mcp"]
