"""Non-blocking background re-indexing.

Runs freshness checks and ``build_index`` off the main event loop
so the MCP server stays responsive during updates.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from src.config import FRESHNESS_CHECK_INTERVAL_SECONDS, METADATA_FILE
from src.engine import build_index
from src.engine.embedder import Embedder
from src.engine.freshness import check_freshness
from src.engine.vector_store import VectorStore
from src.telemetry import report_exception


logger = logging.getLogger(__name__)

# Module-level flag for observability
_update_in_progress: bool = False


def is_update_in_progress() -> bool:
    """Return whether a background re-index is currently running."""
    return _update_in_progress


async def background_update(
    embedder: Embedder,
    store: VectorStore,
    metadata_path: Path = METADATA_FILE,
    interval_seconds: int = FRESHNESS_CHECK_INTERVAL_SECONDS,
    force: bool = False,
) -> int:
    """Check freshness and re-index if stale.

    Runs blocking operations via :func:`asyncio.to_thread` so the MCP
    event loop is never blocked.

    Args:
        embedder: Shared embedder instance.
        store: Shared vector store instance.
        metadata_path: Path to metadata file.
        interval_seconds: Minimum seconds between freshness checks.
        force: Skip freshness check and always re-index.

    Returns:
        Number of chunks indexed (0 if skipped or on error).
    """
    global _update_in_progress

    try:
        if not force:
            result = await asyncio.to_thread(
                check_freshness,
                metadata_path=metadata_path,
                interval_seconds=interval_seconds,
            )
            if not result.is_stale:
                logger.debug("Background update skipped (fresh or rate-limited)")
                return 0

        _update_in_progress = True
        logger.info("Background re-index started")

        count = await asyncio.to_thread(
            build_index,
            embedder=embedder,
            store=store,
            metadata_path=metadata_path,
            force=True,
        )

        logger.info("Background re-index finished: %d chunks", count)
        return count

    except Exception:
        logger.exception("Background update failed")
        report_exception()
        return 0
    finally:
        _update_in_progress = False


def schedule_background_update(
    embedder: Embedder,
    store: VectorStore,
    metadata_path: Path = METADATA_FILE,
    interval_seconds: int = FRESHNESS_CHECK_INTERVAL_SECONDS,
    force: bool = False,
) -> asyncio.Task[int]:
    """Schedule :func:`background_update` as an ``asyncio.Task``."""
    return asyncio.create_task(
        background_update(
            embedder=embedder,
            store=store,
            metadata_path=metadata_path,
            interval_seconds=interval_seconds,
            force=force,
        )
    )
