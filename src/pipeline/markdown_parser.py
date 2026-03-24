"""Markdown file discovery and parsing.

Discovers .md/.mdx files in the docs repo and extracts
frontmatter metadata and body content.
"""

import logging
from pathlib import Path

import frontmatter

from src.config import DOCS_DIR, SUPPORTED_EXTENSIONS
from src.pipeline.exceptions import ParseError
from src.pipeline.models import Document


logger = logging.getLogger(__name__)


def discover_markdown_files(docs_dir: Path = DOCS_DIR) -> list[Path]:
    """Find all markdown files in the docs directory.

    Args:
        docs_dir: Root directory to search.

    Returns:
        Sorted list of markdown file paths.
    """
    files: list[Path] = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(docs_dir.rglob(f"*{ext}"))
    return sorted(files)


def parse_markdown_file(file_path: Path, docs_dir: Path = DOCS_DIR) -> Document:
    """Parse a single markdown file, extracting frontmatter and content.

    Args:
        file_path: Path to the markdown file.
        docs_dir: Root docs directory (for computing relative paths).

    Returns:
        A Document with frontmatter and content populated.

    Raises:
        ParseError: If the file cannot be read or parsed.
    """
    try:
        text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ParseError(f"Cannot read {file_path}: {exc}") from exc

    try:
        post = frontmatter.loads(text)
    except Exception as exc:
        raise ParseError(f"Failed to parse frontmatter in {file_path}: {exc}") from exc

    relative_path = str(file_path.relative_to(docs_dir))
    meta: dict[str, object] = dict(post.metadata)
    title = str(meta.get("title", file_path.stem))

    return Document(
        path=relative_path,
        title=title,
        content=post.content,
        frontmatter=meta,
    )


def parse_all_documents(docs_dir: Path = DOCS_DIR) -> list[Document]:
    """Discover and parse all markdown files in the docs directory.

    Args:
        docs_dir: Root directory to search.

    Returns:
        List of parsed Documents.
    """
    files = discover_markdown_files(docs_dir)
    documents: list[Document] = []

    for file_path in files:
        try:
            doc = parse_markdown_file(file_path, docs_dir)
            documents.append(doc)
        except ParseError:
            logger.warning("Skipping unparseable file: %s", file_path)

    logger.info("Parsed %d documents from %s", len(documents), docs_dir)
    return documents
