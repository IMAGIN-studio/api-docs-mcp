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
# BGE's retrieval instruction for queries (documents are embedded without it).
EMBEDDING_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "
LANCEDB_TABLE_NAME = "docs"

# Pipeline settings
SUPPORTED_EXTENSIONS = {".md", ".mdx"}
MAX_CHUNK_CHARS = 2000  # ~512 tokens: the embedding model ignores input past that
MIN_CHUNK_CHARS = 200

# OpenAPI spec source (committed inside the docs repo; indexed alongside markdown).
# The spec rides the existing git sync, so a committed change re-indexes automatically.
OPENAPI_ENABLED: bool = os.getenv("IMAGIN_DOCS_OPENAPI", "1").lower() in ("1", "true", "yes")
OPENAPI_SPEC_RELPATH = ".gitbook/assets/openapi (1).yaml"  # relative to DOCS_DIR
OPENAPI_DOCS_URL = "https://docs.imagin.studio"  # per-endpoint result URL; "" to omit

# Search settings
SEARCH_TOP_K = 5
SEARCH_TOP_K_MAX = 20
CHARACTER_LIMIT = SEARCH_TOP_K_MAX * (MAX_CHUNK_CHARS + 200)

# Hybrid search (vector + BM25, merged by weighted reciprocal rank fusion).
# Tuned with eval/run_eval.py on 62 questions: deeper candidate pools (20, 50)
# traded top-1 hits for top-5 hits and lowered MRR; a keyword weight of 0.5 or
# 2 did not beat equal weights. Re-run the sweep before changing these.
HYBRID_CANDIDATES = 5  # chunks fetched from each ranking before fusion (at least top_k)
RRF_K = 60  # RRF damping constant (60 = original RRF paper)
HYBRID_KEYWORD_WEIGHT = 1.0  # keyword ranking weight; the vector ranking has weight 1

# Markdown files left out of the index, relative to the docs root.
# The MCP manual page describes this server and lists example questions, so it
# matched many unrelated queries; leaving it out gained 1 top-1 and 1 top-5 hit.
INDEX_EXCLUDE_PATHS: frozenset[str] = frozenset(
    {"api-integration/manuals/mcp-api-documentation.md"}
)


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
