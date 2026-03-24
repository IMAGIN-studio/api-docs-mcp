"""Data models for the document pipeline."""

from datetime import datetime

from pydantic import BaseModel, Field


class Document(BaseModel):
    """A parsed markdown document with metadata."""

    path: str
    title: str = ""
    content: str = ""
    frontmatter: dict[str, object] = Field(default_factory=dict)
    url: str = ""


class Chunk(BaseModel):
    """A semantic chunk extracted from a document."""

    chunk_id: str
    document_path: str
    heading_hierarchy: list[str] = Field(default_factory=list)
    content: str
    url: str = ""
    char_count: int = 0

    def model_post_init(self, _context: object) -> None:
        """Set char_count from content length."""
        if not self.char_count:
            self.char_count = len(self.content)


class IndexMetadata(BaseModel):
    """Persisted metadata about the current index state."""

    commit_hash: str = ""
    last_indexed_at: datetime | None = None
    last_checked_at: datetime | None = None
    doc_count: int = 0
    chunk_count: int = 0
