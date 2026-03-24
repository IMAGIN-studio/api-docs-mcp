"""Local RAG engine: embed and index document chunks.

Orchestrates the embedding and indexing of chunks produced
by the document pipeline into the vector store.
"""

import logging
from datetime import UTC, datetime
from pathlib import Path

from src.config import DOCS_DIR, DOCS_REPO_BRANCH, DOCS_REPO_URL, METADATA_FILE
from src.engine.embedder import Embedder
from src.engine.vector_store import SearchResult, VectorStore
from src.pipeline import run_pipeline
from src.pipeline.git_sync import load_metadata, save_metadata


logger = logging.getLogger(__name__)


def build_index(
    embedder: Embedder | None = None,
    store: VectorStore | None = None,
    repo_url: str = DOCS_REPO_URL,
    docs_dir: Path = DOCS_DIR,
    branch: str = DOCS_REPO_BRANCH,
    metadata_path: Path = METADATA_FILE,
    force: bool = False,
) -> int:
    """Run the full pipeline and index chunks into the vector store.

    Skips re-indexing if the commit hash hasn't changed (unless force=True).

    Args:
        embedder: Embedder instance (created if None).
        store: VectorStore instance (created if None).
        repo_url: Git repository URL.
        docs_dir: Local directory for the clone.
        branch: Branch to track.
        metadata_path: Path to metadata file.
        force: Force re-indexing even if commit unchanged.

    Returns:
        Number of chunks indexed.
    """
    if embedder is None:
        embedder = Embedder()
    if store is None:
        store = VectorStore()

    # Run document pipeline (git sync + parse + chunk)
    chunks = run_pipeline(repo_url, docs_dir, branch)

    if not chunks:
        logger.warning("Pipeline produced no chunks")
        return 0

    # Check if re-indexing is needed
    metadata = load_metadata(metadata_path)
    if not force and metadata.last_indexed_at is not None and store.has_table():
        logger.info("Index is up to date (commit %s), skipping", metadata.commit_hash)
        return metadata.chunk_count

    # Embed all chunks
    logger.info("Embedding %d chunks...", len(chunks))
    texts = [c.content for c in chunks]
    vectors = embedder.embed_texts(texts)

    # Index into vector store
    count = store.upsert_chunks(
        chunk_ids=[c.chunk_id for c in chunks],
        document_paths=[c.document_path for c in chunks],
        heading_hierarchies=[" > ".join(c.heading_hierarchy) for c in chunks],
        contents=[c.content for c in chunks],
        urls=[c.url for c in chunks],
        vectors=vectors,
    )

    # Update metadata
    metadata.last_indexed_at = datetime.now(tz=UTC)
    metadata.chunk_count = count
    save_metadata(metadata, metadata_path)

    logger.info("Indexed %d chunks", count)
    return count


__all__ = ["Embedder", "SearchResult", "VectorStore", "build_index"]
