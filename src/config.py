"""Application configuration and paths.

All persistent data stored under ~/.imagin-docs-mcp/:
    docs/           - Cloned GitHub repo
    lancedb/        - Vector store
    models/         - Cached embedding model
    metadata.json   - Index state (commit hash, timestamps)
"""

import os
from pathlib import Path
from urllib.parse import urlparse


# GitHub documentation repository
DOCS_REPO_URL = "https://github.com/IMAGIN-studio/api-docs.git"
DOCS_REPO_BRANCH = "main"

# Freshness / auto-update settings
FRESHNESS_CHECK_INTERVAL_SECONDS = 300
GITHUB_API_BASE = "https://api.github.com"

# Data directory
DATA_DIR = Path.home() / ".imagin-docs-mcp"
DOCS_DIR = DATA_DIR / "docs"
LANCEDB_DIR = DATA_DIR / "lancedb"
MODELS_DIR = DATA_DIR / "models"
METADATA_FILE = DATA_DIR / "metadata.json"

# Embedding model
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
LANCEDB_TABLE_NAME = "docs"

# Pipeline settings
SUPPORTED_EXTENSIONS = {".md", ".mdx"}
MAX_CHUNK_CHARS = 8192
MIN_CHUNK_CHARS = 200

# Search settings
SEARCH_TOP_K = 5
SEARCH_TOP_K_MAX = 20
CHARACTER_LIMIT = SEARCH_TOP_K_MAX * (MAX_CHUNK_CHARS + 200)


# --- Telemetry (opt-in) ---
# Users enable with IMAGIN_DOCS_TELEMETRY=1. Reports go to GCE Error Reporting.
TELEMETRY_ENABLED: bool = os.getenv("IMAGIN_DOCS_TELEMETRY", "").lower() in ("1", "true", "yes")
TELEMETRY_GCP_PROJECT: str = os.getenv("IMAGIN_DOCS_GCP_PROJECT", "imagin-mlops-prod")
TELEMETRY_GCP_API_KEY: str = os.getenv("IMAGIN_DOCS_GCP_API_KEY", "AIzaSyDoyJBZ3HyW6Ggoaqhl8gOkmIC_o1pHCgY")
TELEMETRY_DRY_RUN: bool = os.getenv("IMAGIN_DOCS_TELEMETRY_DRY_RUN", "").lower() in ("1", "true", "yes")


def get_github_api_commit_url(repo_url: str = DOCS_REPO_URL, branch: str = DOCS_REPO_BRANCH) -> str:
    """Build the GitHub API URL for the latest commit on a branch.

    Parses owner/repo from a GitHub clone URL and returns
    ``/repos/{owner}/{repo}/commits/{branch}``.
    """
    parsed = urlparse(repo_url)
    # Strip leading '/' and trailing '.git'
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return f"{GITHUB_API_BASE}/repos/{path}/commits/{branch}"
