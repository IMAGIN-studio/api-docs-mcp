"""Freshness checking via the GitHub API.

Compares the latest remote commit hash against the locally stored
``metadata.commit_hash`` to decide whether a re-index is needed.
Rate-limited to avoid unnecessary API calls.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

from src.config import (
    FRESHNESS_CHECK_INTERVAL_SECONDS,
    METADATA_FILE,
    get_github_api_commit_url,
)
from src.pipeline.git_sync import load_metadata, save_metadata


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FreshnessResult:
    """Outcome of a freshness check."""

    is_stale: bool
    remote_hash: str
    local_hash: str
    skipped: bool


def _fetch_remote_commit_hash(api_url: str, timeout: int = 10) -> str:
    """GET the latest commit SHA from the GitHub API.

    Uses the ``Accept: application/vnd.github.sha`` header so the
    response body is a plain-text SHA (no JSON parsing needed).
    """
    request = Request(api_url, headers={"Accept": "application/vnd.github.sha"})
    with urlopen(request, timeout=timeout) as resp:
        body: bytes = resp.read()
        return body.decode("utf-8").strip()


def check_freshness(
    metadata_path: Path = METADATA_FILE,
    interval_seconds: int = FRESHNESS_CHECK_INTERVAL_SECONDS,
    api_url: str | None = None,
) -> FreshnessResult:
    """Check whether the local index is stale compared to the remote repo.

    Skips the network call when ``last_checked_at`` is less than
    *interval_seconds* ago (rate limiting).

    Returns a :class:`FreshnessResult` describing the outcome.
    """
    if api_url is None:
        api_url = get_github_api_commit_url()

    metadata = load_metadata(metadata_path)

    # Rate-limit: skip if we checked recently
    if metadata.last_checked_at is not None:
        elapsed = (datetime.now(tz=UTC) - metadata.last_checked_at).total_seconds()
        if elapsed < interval_seconds:
            logger.debug("Freshness check skipped (%.0fs since last check)", elapsed)
            return FreshnessResult(
                is_stale=False,
                remote_hash=metadata.commit_hash,
                local_hash=metadata.commit_hash,
                skipped=True,
            )

    remote_hash = _fetch_remote_commit_hash(api_url)
    local_hash = metadata.commit_hash

    is_stale = remote_hash != local_hash
    if is_stale:
        logger.info("Index is stale: local=%s remote=%s", local_hash, remote_hash)
    else:
        logger.debug("Index is fresh (commit %s)", local_hash)

    # Persist updated check timestamp
    metadata.last_checked_at = datetime.now(tz=UTC)
    save_metadata(metadata, metadata_path)

    return FreshnessResult(
        is_stale=is_stale,
        remote_hash=remote_hash,
        local_hash=local_hash,
        skipped=False,
    )
