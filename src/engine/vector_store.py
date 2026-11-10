"""Vector store backed by LanceDB.

Stores document chunks with their embeddings plus a full-text (BM25) index
on the chunk text, and searches them in hybrid mode: the vector ranking finds
chunks by meaning, the keyword ranking finds exact terms such as parameter
names, and the two rankings are merged with reciprocal rank fusion (RRF).
"""

import logging
from dataclasses import dataclass, replace
from pathlib import Path

import lancedb
import pyarrow as pa
from lancedb.index import FTS

from src.config import (
    HYBRID_CANDIDATES,
    HYBRID_KEYWORD_WEIGHT,
    LANCEDB_DIR,
    LANCEDB_TABLE_NAME,
    RRF_K,
    SEARCH_TOP_K,
)
from src.utils.paths import ensure_dir


logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result from the vector store."""

    chunk_id: str
    document_path: str
    heading_hierarchy: str
    content: str
    url: str
    score: float


def fuse_rankings(
    rankings: list[tuple[list[SearchResult], float]], rrf_k: int = RRF_K
) -> list[SearchResult]:
    """Merge ranked result lists by weighted reciprocal rank fusion (RRF).

    Each chunk scores ``sum(weight / (rrf_k + rank))`` over the lists it
    appears in (rank starts at 1). Only ranks are used, so the vector
    distances and BM25 scores, which are on different scales, never need to
    be compared. A chunk found by both rankings usually beats one found by
    only one of them; a higher weight lets a strong keyword hit compete.

    Args:
        rankings: (results, weight) pairs, each list ordered best first.
        rrf_k: Damping constant; 60 is the value from the original RRF paper.

    Returns:
        The union of all results, ordered by fused score, best first, with
        ``score`` set to the fused score.
    """
    scores: dict[str, float] = {}
    first_seen: dict[str, SearchResult] = {}
    for results, weight in rankings:
        for rank, result in enumerate(results, 1):
            scores[result.chunk_id] = scores.get(result.chunk_id, 0.0) + weight / (rrf_k + rank)
            first_seen.setdefault(result.chunk_id, result)
    ordered = sorted(scores, key=lambda cid: scores[cid], reverse=True)
    return [replace(first_seen[cid], score=scores[cid]) for cid in ordered]


class VectorStore:
    """LanceDB-backed vector store for document chunks."""

    def __init__(
        self,
        db_path: Path = LANCEDB_DIR,
        table_name: str = LANCEDB_TABLE_NAME,
    ) -> None:
        self._db_path = db_path
        self._table_name = table_name
        self._db: lancedb.DBConnection | None = None

    def _get_db(self) -> lancedb.DBConnection:
        """Lazily connect to the LanceDB database."""
        if self._db is None:
            ensure_dir(self._db_path)
            self._db = lancedb.connect(str(self._db_path))
        return self._db

    def _table_exists(self, db: lancedb.DBConnection) -> bool:
        """Whether this store's table exists (``list_tables`` is paginated)."""
        page_token: str | None = None
        while True:
            response = db.list_tables(page_token=page_token)
            if self._table_name in response.tables:
                return True
            page_token = response.page_token
            if not page_token:
                return False

    def upsert_chunks(
        self,
        chunk_ids: list[str],
        document_paths: list[str],
        heading_hierarchies: list[str],
        contents: list[str],
        urls: list[str],
        vectors: list[list[float]],
    ) -> int:
        """Insert or replace chunks in the vector store.

        Drops and recreates the table to ensure a clean index
        that exactly mirrors the current documentation state.

        Args:
            chunk_ids: Unique IDs for each chunk.
            document_paths: Source document path for each chunk.
            heading_hierarchies: Serialized heading hierarchy for each chunk.
            contents: Text content for each chunk.
            urls: Source URL for each chunk.
            vectors: Embedding vectors for each chunk.

        Returns:
            Number of chunks indexed.
        """
        db = self._get_db()

        data = pa.table(
            {
                "chunk_id": chunk_ids,
                "document_path": document_paths,
                "heading_hierarchy": heading_hierarchies,
                "content": contents,
                "url": urls,
                "vector": vectors,
            }
        )

        # Drop existing table and create fresh
        if self._table_exists(db):
            db.drop_table(self._table_name)

        table = db.create_table(self._table_name, data=data)
        self._create_fts_index(table)
        count = len(chunk_ids)
        logger.info("Indexed %d chunks into table '%s'", count, self._table_name)
        return count

    @staticmethod
    def _create_fts_index(table: lancedb.table.Table) -> None:
        """Build the BM25 full-text index on chunk content.

        Uses LanceDB's native index (no tantivy dependency). The tokenizer
        lower-cases and splits on non-alphanumerics, so a query for
        ``safeMode`` matches ``safemode``. Settings, chosen with
        eval/run_eval.py on lancedb 0.40:

        - stop words removed: filler words in sentence-style questions
          ("is there a way for them to...") otherwise outrank the words that
          matter; +3 top-1 and +2 top-5 hits, identifier questions unchanged.
        - no stemming: it rewrites identifiers and lost identifier hits.
        - no ASCII folding: the docs are English, nothing to fold.

        A failure is logged, not raised: search then falls back to vectors only.
        """
        fts = FTS(stem=False, remove_stop_words=True, ascii_folding=False)
        try:
            table.create_index("content", config=fts, replace=True)
        except Exception:
            logger.exception("Failed to build full-text index; search will be vector-only")

    def search(
        self,
        query_vector: list[float],
        top_k: int = SEARCH_TOP_K,
        query_text: str | None = None,
        *,
        candidates: int = HYBRID_CANDIDATES,
        rrf_k: int = RRF_K,
        keyword_weight: float = HYBRID_KEYWORD_WEIGHT,
    ) -> list[SearchResult]:
        """Search for the most relevant chunks.

        With *query_text*, runs a hybrid search: the vector ranking and the
        full-text (BM25) ranking each fetch *candidates* chunks, and the two
        rankings are merged by weighted reciprocal rank fusion (see
        :func:`fuse_rankings`). Without *query_text*, or if the full-text query
        fails (for example an index built by an older version without the
        full-text index), runs a vector-only search.

        Args:
            query_vector: The query embedding vector.
            top_k: Number of results to return.
            query_text: The raw query text for the keyword half of the search.
            candidates: Chunks fetched from each ranking before fusion.
            rrf_k: RRF damping constant; lower values favour top ranks more.
            keyword_weight: Weight of the keyword ranking (the vector ranking
                has weight 1).

        Returns:
            List of SearchResult objects, most relevant first. ``score`` is the
            fused RRF score (higher is better) for hybrid results and the vector
            distance (lower is better) for vector-only results.
        """
        db = self._get_db()

        if not self._table_exists(db):
            logger.warning("Table '%s' does not exist yet", self._table_name)
            return []

        table = db.open_table(self._table_name)
        depth = max(top_k, candidates)

        vector_hits = self._to_results(
            table.search(query_vector).limit(depth).to_arrow(), "_distance"
        )
        if not (query_text and query_text.strip()):
            return vector_hits[:top_k]

        try:
            keyword_hits = self._to_results(
                table.search(query_text, query_type="fts").limit(depth).to_arrow(), "_score"
            )
        except Exception:
            logger.warning("Full-text search failed; falling back to vector-only", exc_info=True)
            return vector_hits[:top_k]

        return fuse_rankings(
            [(vector_hits, 1.0), (keyword_hits, keyword_weight)], rrf_k=rrf_k
        )[:top_k]

    @staticmethod
    def _to_results(results: pa.Table, score_column: str) -> list[SearchResult]:
        """Convert a LanceDB result table into SearchResult objects."""
        return [
            SearchResult(
                chunk_id=str(results.column("chunk_id")[i].as_py()),
                document_path=str(results.column("document_path")[i].as_py()),
                heading_hierarchy=str(results.column("heading_hierarchy")[i].as_py()),
                content=str(results.column("content")[i].as_py()),
                url=str(results.column("url")[i].as_py()),
                score=float(results.column(score_column)[i].as_py()),
            )
            for i in range(results.num_rows)
        ]

    def has_table(self) -> bool:
        """Check if the docs table exists."""
        db = self._get_db()
        return self._table_exists(db)
