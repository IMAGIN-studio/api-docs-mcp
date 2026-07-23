"""Document pipeline: git sync, parse, chunk.

Orchestrates the full pipeline from git clone through to producing chunks ready
for embedding. Markdown docs and the committed OpenAPI spec are both turned into
chunks in the *same* run, because the vector store rebuilds its single table from
one combined list — indexing a source separately would wipe the other.
"""

import logging
from pathlib import Path

from src.config import DOCS_DIR, DOCS_REPO_BRANCH, DOCS_REPO_URL, OPENAPI_ENABLED
from src.pipeline.chunker import chunk_document
from src.pipeline.git_sync import clone_or_update_repo, load_metadata, save_metadata
from src.pipeline.markdown_parser import parse_all_documents
from src.pipeline.models import Chunk
from src.pipeline.openapi_parser import find_spec_file, load_openapi_spec, parse_openapi_spec
from src.telemetry import report_exception


logger = logging.getLogger(__name__)


def run_pipeline(
    repo_url: str = DOCS_REPO_URL,
    docs_dir: Path = DOCS_DIR,
    branch: str = DOCS_REPO_BRANCH,
    openapi_enabled: bool = OPENAPI_ENABLED,
) -> list[Chunk]:
    """Run the full document pipeline.

    1. Clone or update the docs repository.
    2. Parse all markdown files and chunk them into semantic sections.
    3. Parse the committed OpenAPI spec into one chunk per endpoint (additive,
       non-fatal).
    4. Update metadata.

    Args:
        repo_url: Git repository URL.
        docs_dir: Local directory for the clone.
        branch: Branch to track.
        openapi_enabled: Whether to also index the committed OpenAPI spec.

    Returns:
        List of all chunks produced from the documentation and API spec.
    """
    # Step 1: Git sync
    commit_hash = clone_or_update_repo(repo_url, docs_dir, branch)
    logger.info("Synced to commit %s", commit_hash)

    # Step 2: Parse + chunk markdown
    documents = parse_all_documents(docs_dir)
    logger.info("Parsed %d documents", len(documents))

    all_chunks: list[Chunk] = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc))
    logger.info("Produced %d markdown chunks", len(all_chunks))

    # Step 3: Add OpenAPI endpoint chunks into the SAME list
    if openapi_enabled:
        _append_openapi_chunks(all_chunks, docs_dir)

    # Step 4: Persist metadata
    metadata = load_metadata()
    metadata.commit_hash = commit_hash
    metadata.doc_count = len(documents)
    metadata.chunk_count = len(all_chunks)
    save_metadata(metadata)

    return all_chunks


def _append_openapi_chunks(all_chunks: list[Chunk], docs_dir: Path) -> None:
    """Parse the committed OpenAPI spec and append its endpoint chunks.

    Additive and non-fatal: any failure (missing/invalid spec, parse error) leaves
    the markdown chunks intact so the docs index still builds.
    """
    try:
        spec_path = find_spec_file(docs_dir)
        if spec_path is None:
            logger.info("No OpenAPI spec found under docs repo; skipping API indexing")
            return
        spec = load_openapi_spec(spec_path)
        if spec is None:
            return
        api_chunks = parse_openapi_spec(spec)
        all_chunks.extend(api_chunks)
        logger.info("Indexed %d OpenAPI endpoint chunks from %s", len(api_chunks), spec_path.name)
    except Exception:
        logger.warning("OpenAPI indexing failed; continuing with markdown only", exc_info=True)
        report_exception()
