"""Pipeline-specific exceptions."""


class PipelineError(Exception):
    """Base exception for pipeline errors."""


class GitSyncError(PipelineError):
    """Raised when git clone/pull operations fail."""


class ParseError(PipelineError):
    """Raised when markdown parsing fails."""
