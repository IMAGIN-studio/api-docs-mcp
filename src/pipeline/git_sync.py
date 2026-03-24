"""Git synchronization for the documentation repository.

Clones or updates the docs repo using git reset --hard to ensure
local state always mirrors the remote source of truth.
"""

import json
import logging
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from src.config import DOCS_DIR, DOCS_REPO_BRANCH, DOCS_REPO_URL, METADATA_FILE
from src.pipeline.exceptions import GitSyncError
from src.pipeline.models import IndexMetadata
from src.utils.paths import ensure_dir


logger = logging.getLogger(__name__)


def clone_or_update_repo(
    repo_url: str = DOCS_REPO_URL,
    target_dir: Path = DOCS_DIR,
    branch: str = DOCS_REPO_BRANCH,
) -> str:
    """Clone the docs repo or update it via fetch + reset --hard.

    Args:
        repo_url: Git repository URL to clone.
        target_dir: Local directory for the clone.
        branch: Branch to track.

    Returns:
        The current HEAD commit hash after sync.

    Raises:
        GitSyncError: If any git operation fails.
    """
    try:
        if (target_dir / ".git").is_dir():
            return _update_repo(target_dir, branch)
        return _clone_repo(repo_url, target_dir, branch)
    except subprocess.CalledProcessError as exc:
        raise GitSyncError(f"Git operation failed: {exc.stderr}") from exc


def _clone_repo(repo_url: str, target_dir: Path, branch: str) -> str:
    """Clone a fresh copy of the repository."""
    logger.info("Cloning %s into %s", repo_url, target_dir)
    ensure_dir(target_dir.parent)
    subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", branch, repo_url, str(target_dir)],
        capture_output=True,
        text=True,
        check=True,
    )
    return _get_head_hash(target_dir)


def _update_repo(target_dir: Path, branch: str) -> str:
    """Fetch and reset --hard to match remote."""
    logger.info("Updating repo in %s", target_dir)
    subprocess.run(
        ["git", "fetch", "origin", branch],
        cwd=str(target_dir),
        capture_output=True,
        text=True,
        check=True,
    )
    subprocess.run(
        ["git", "reset", "--hard", f"origin/{branch}"],
        cwd=str(target_dir),
        capture_output=True,
        text=True,
        check=True,
    )
    return _get_head_hash(target_dir)


def _get_head_hash(target_dir: Path) -> str:
    """Get the current HEAD commit hash."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(target_dir),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def load_metadata(path: Path = METADATA_FILE) -> IndexMetadata:
    """Load index metadata from disk.

    Args:
        path: Path to metadata JSON file.

    Returns:
        Loaded metadata, or fresh defaults if file doesn't exist.
    """
    if not path.exists():
        return IndexMetadata()
    data = json.loads(path.read_text(encoding="utf-8"))
    return IndexMetadata.model_validate(data)


def save_metadata(metadata: IndexMetadata, path: Path = METADATA_FILE) -> None:
    """Persist index metadata to disk.

    Args:
        metadata: The metadata to save.
        path: Path to write the JSON file.
    """
    ensure_dir(path.parent)
    metadata.last_checked_at = datetime.now(tz=UTC)
    path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")
