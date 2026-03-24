"""Header-based semantic chunking for markdown documents.

Splits documents into chunks at heading boundaries while preserving
code blocks intact and tracking the heading hierarchy for context.
"""

import hashlib
import re
from typing import TypedDict

from src.config import MAX_CHUNK_CHARS, MIN_CHUNK_CHARS
from src.pipeline.models import Chunk, Document


# Regex matching markdown headings (e.g. "## My Section")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


class _Section(TypedDict):
    level: int
    heading: str
    body: str


def chunk_document(
    document: Document,
    max_chars: int = MAX_CHUNK_CHARS,
    min_chars: int = MIN_CHUNK_CHARS,
) -> list[Chunk]:
    """Split a document into semantic chunks at heading boundaries.

    Each chunk captures the heading hierarchy (e.g. ["Guide", "Installation", "Linux"])
    so that search results can show the full section path.

    Code blocks are never split mid-block. Undersized chunks are merged in a
    post-processing step to reduce fragmentation.

    Args:
        document: The parsed document to chunk.
        max_chars: Maximum characters per chunk (hard cap).
        min_chars: Minimum characters; smaller chunks are merged with neighbours.

    Returns:
        List of Chunk objects.
    """
    if not document.content.strip():
        return []

    sections = _split_by_headings(document.content)
    chunks: list[Chunk] = []
    heading_stack: list[tuple[int, str]] = []

    for section in sections:
        heading_level = section["level"]
        heading_text = section["heading"]
        body = section["body"].strip()

        if heading_level > 0:
            # Pop headings at same or deeper level
            heading_stack = [(lv, txt) for lv, txt in heading_stack if lv < heading_level]
            heading_stack.append((heading_level, heading_text))

        if not body and not heading_text:
            continue

        hierarchy = [txt for _, txt in heading_stack]
        content = _build_chunk_content(heading_text, body)

        if not content.strip():
            continue

        # Split oversized chunks
        for part in _split_oversized(content, max_chars):
            chunk_id = _make_chunk_id(document.path, part)
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_path=document.path,
                    heading_hierarchy=hierarchy,
                    content=part,
                    url=document.url,
                )
            )

    chunks = _merge_undersized_chunks(chunks, document.path, min_chars, max_chars)
    return chunks


def _split_by_headings(content: str) -> list[_Section]:
    """Split markdown content into sections at heading boundaries.

    Returns a list of sections. Content before the first heading gets level=0.
    """
    sections: list[_Section] = []
    last_end = 0

    for match in _HEADING_RE.finditer(content):
        # Capture text before this heading
        before = content[last_end : match.start()]
        if sections:
            sections[-1]["body"] += before
        elif before.strip():
            sections.append({"level": 0, "heading": "", "body": before})

        level = len(match.group(1))
        heading = match.group(2).strip()
        sections.append({"level": level, "heading": heading, "body": ""})
        last_end = match.end()

    # Remaining text after last heading
    remaining = content[last_end:]
    if sections:
        sections[-1]["body"] += remaining
    elif remaining.strip():
        sections.append({"level": 0, "heading": "", "body": remaining})

    return sections


def _build_chunk_content(heading: str, body: str) -> str:
    """Combine heading and body into chunk text."""
    if heading:
        return f"# {heading}\n\n{body}" if body else f"# {heading}"
    return body


def _split_oversized(text: str, max_chars: int) -> list[str]:
    """Split text that exceeds max_chars, preserving code blocks.

    Tries to split at paragraph boundaries first, falling back to
    hard truncation only if a single paragraph exceeds the limit.
    """
    if len(text) <= max_chars:
        return [text]

    parts: list[str] = []
    current: list[str] = []
    current_len = 0

    # Split on double-newlines (paragraph boundaries), preserving code blocks
    paragraphs = _split_preserving_code_blocks(text)

    for para in paragraphs:
        para_len = len(para)

        if current_len + para_len + 2 > max_chars and current:
            parts.append("\n\n".join(current))
            current = []
            current_len = 0

        # Single paragraph exceeds limit - hard split
        if para_len > max_chars:
            for i in range(0, para_len, max_chars):
                parts.append(para[i : i + max_chars])
            continue

        current.append(para)
        current_len += para_len + 2

    if current:
        parts.append("\n\n".join(current))

    return parts


def _split_preserving_code_blocks(text: str) -> list[str]:
    """Split text into paragraphs without breaking code blocks.

    Code fences (```) are detected and their content is kept together
    as a single paragraph unit.
    """
    lines = text.split("\n")
    paragraphs: list[str] = []
    current: list[str] = []
    in_code_block = False

    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            current.append(line)
            if not in_code_block:
                # End of code block - emit as one paragraph
                paragraphs.append("\n".join(current))
                current = []
            continue

        if in_code_block:
            current.append(line)
            continue

        if line.strip() == "" and current:
            paragraphs.append("\n".join(current))
            current = []
        else:
            current.append(line)

    if current:
        paragraphs.append("\n".join(current))

    return paragraphs


def _make_chunk_id(doc_path: str, content: str) -> str:
    """Generate a deterministic chunk ID from path and content."""
    raw = f"{doc_path}:{content}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _merge_undersized_chunks(
    chunks: list[Chunk],
    doc_path: str,
    min_chars: int,
    max_chars: int,
) -> list[Chunk]:
    """Merge undersized chunks with their neighbours to reduce fragmentation.

    Iterates forward through *chunks*. Any chunk whose content is shorter than
    *min_chars* accumulates into a buffer. When the next chunk arrives:

    * If buffer + next fits within *max_chars* → merge (keep first chunk's
      hierarchy and metadata).
    * If the merged result is still undersized → keep accumulating.
    * If merge would exceed *max_chars* → flush the buffer as a standalone
      chunk, then handle the next chunk normally.

    At end-of-list, if a buffer remains it is merged backward into the last
    emitted chunk (if it fits); otherwise it is emitted standalone.
    """
    if len(chunks) <= 1:
        return chunks

    merged: list[Chunk] = []

    buf_content: str = ""
    buf_hierarchy: list[str] = []
    buf_url: str = ""

    for chunk in chunks:
        if not buf_content:
            # Nothing buffered yet
            if len(chunk.content) < min_chars:
                # Start accumulating
                buf_content = chunk.content
                buf_hierarchy = chunk.heading_hierarchy
                buf_url = chunk.url
            else:
                merged.append(chunk)
            continue

        # We have buffered content — try to merge with current chunk
        candidate = buf_content + "\n\n" + chunk.content
        if len(candidate) <= max_chars:
            # Merge succeeds
            buf_content = candidate
            # Keep checking if still undersized (continue accumulating)
            if len(buf_content) >= min_chars:
                # Flush the buffer
                merged.append(
                    Chunk(
                        chunk_id=_make_chunk_id(doc_path, buf_content),
                        document_path=doc_path,
                        heading_hierarchy=buf_hierarchy,
                        content=buf_content,
                        url=buf_url,
                    )
                )
                buf_content = ""
                buf_hierarchy = []
                buf_url = ""
        else:
            # Would exceed max — flush buffer standalone, handle current chunk
            merged.append(
                Chunk(
                    chunk_id=_make_chunk_id(doc_path, buf_content),
                    document_path=doc_path,
                    heading_hierarchy=buf_hierarchy,
                    content=buf_content,
                    url=buf_url,
                )
            )
            buf_content = ""
            buf_hierarchy = []
            buf_url = ""

            if len(chunk.content) < min_chars:
                buf_content = chunk.content
                buf_hierarchy = chunk.heading_hierarchy
                buf_url = chunk.url
            else:
                merged.append(chunk)

    # Handle remaining buffer
    if buf_content:
        if merged:
            # Try merging backward into the last emitted chunk
            last = merged[-1]
            candidate = last.content + "\n\n" + buf_content
            if len(candidate) <= max_chars:
                merged[-1] = Chunk(
                    chunk_id=_make_chunk_id(doc_path, candidate),
                    document_path=doc_path,
                    heading_hierarchy=last.heading_hierarchy,
                    content=candidate,
                    url=last.url,
                )
            else:
                # Emit standalone
                merged.append(
                    Chunk(
                        chunk_id=_make_chunk_id(doc_path, buf_content),
                        document_path=doc_path,
                        heading_hierarchy=buf_hierarchy,
                        content=buf_content,
                        url=buf_url,
                    )
                )
        else:
            # No preceding chunk — emit standalone
            merged.append(
                Chunk(
                    chunk_id=_make_chunk_id(doc_path, buf_content),
                    document_path=doc_path,
                    heading_hierarchy=buf_hierarchy,
                    content=buf_content,
                    url=buf_url,
                )
            )

    return merged
