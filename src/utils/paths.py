"""Cross-platform path handling utilities.

Handles Windows MAX_PATH (260 char) limitations and ensures
directories exist before use.
"""

import platform
import sys
from pathlib import Path


def ensure_dir(path: Path) -> Path:
    """Create directory and parents if they don't exist.

    Args:
        path: Directory path to ensure exists.

    Returns:
        The same path, for chaining.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_path(path: Path) -> Path:
    """Return a path safe for the current platform.

    On Windows, prefixes long paths with \\\\?\\ to bypass the
    260-character MAX_PATH limitation.

    Args:
        path: The path to make safe.

    Returns:
        Platform-safe version of the path.
    """
    if platform.system() != "Windows":
        return path

    resolved = path.resolve()
    str_path = str(resolved)

    if len(str_path) > 240 and not str_path.startswith("\\\\?\\"):
        return Path(f"\\\\?\\{str_path}")

    return resolved


def is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform == "win32"
