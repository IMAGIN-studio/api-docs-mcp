"""Vector store backed by LanceDB.

Provides embedded vector storage for document chunks with
semantic search capabilities.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import lancedb
import pyarrow as pa

from src.config import LANCEDB_DIR, LANCEDB_TABLE_NAME, SEARCH_TOP_K
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
        if self._table_name in db.table_names():
            db.drop_table(self._table_name)

        db.create_table(self._table_name, data=data)
        count = len(chunk_ids)
        logger.info("Indexed %d chunks into table '%s'", count, self._table_name)
        return count

    def search(self, query_vector: list[float], top_k: int = SEARCH_TOP_K) -> list[SearchResult]:
        """Search for the most similar chunks.

        Args:
            query_vector: The query embedding vector.
            top_k: Number of results to return.

        Returns:
            List of SearchResult objects sorted by relevance.
        """
        db = self._get_db()

        if self._table_name not in db.table_names():
            logger.warning("Table '%s' does not exist yet", self._table_name)
            return []

        table = db.open_table(self._table_name)
        results = table.search(query_vector).limit(top_k).to_arrow()

        return [
            SearchResult(
                chunk_id=str(results.column("chunk_id")[i].as_py()),
                document_path=str(results.column("document_path")[i].as_py()),
                heading_hierarchy=str(results.column("heading_hierarchy")[i].as_py()),
                content=str(results.column("content")[i].as_py()),
                url=str(results.column("url")[i].as_py()),
                score=float(results.column("_distance")[i].as_py()),
            )
            for i in range(results.num_rows)
        ]

    def has_table(self) -> bool:
        """Check if the docs table exists."""
        db = self._get_db()
        return self._table_name in db.table_names()
