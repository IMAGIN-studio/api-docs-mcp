"""Document pipeline: git sync, parse, chunk.

Orchestrates the full pipeline from git clone through to
producing chunks ready for embedding.
"""

import logging
from pathlib import Path

from src.config import DOCS_DIR, DOCS_REPO_BRANCH, DOCS_REPO_URL
from src.pipeline.chunker import chunk_document
from src.pipeline.git_sync import clone_or_update_repo, load_metadata, save_metadata
from src.pipeline.markdown_parser import parse_all_documents
from src.pipeline.models import Chunk


logger = logging.getLogger(__name__)


def run_pipeline(
    repo_url: str = DOCS_REPO_URL,
    docs_dir: Path = DOCS_DIR,
    branch: str = DOCS_REPO_BRANCH,
) -> list[Chunk]:
    """Run the full document pipeline.

    1. Clone or update the docs repository.
    2. Parse all markdown files.
    3. Chunk documents into semantic sections.
    4. Update metadata.

    Args:
        repo_url: Git repository URL.
        docs_dir: Local directory for the clone.
        branch: Branch to track.

    Returns:
        List of all chunks produced from the documentation.
    """
    # Step 1: Git sync
    commit_hash = clone_or_update_repo(repo_url, docs_dir, branch)
    logger.info("Synced to commit %s", commit_hash)

    # Step 2: Parse markdown
    documents = parse_all_documents(docs_dir)
    logger.info("Parsed %d documents", len(documents))

    # Step 3: Chunk
    all_chunks: list[Chunk] = []
    for doc in documents:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
    logger.info("Produced %d chunks", len(all_chunks))

    # Step 4: Persist metadata
    metadata = load_metadata()
    metadata.commit_hash = commit_hash
    metadata.doc_count = len(documents)
    metadata.chunk_count = len(all_chunks)
    save_metadata(metadata)

    return all_chunks
