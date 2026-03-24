"""Opt-in error telemetry via Google Cloud Error Reporting REST API.

Activation requires the user to set:
    IMAGIN_DOCS_TELEMETRY=1

The GCP project and API key are embedded in config.py (write-only key,
restricted to the Error Reporting API with a daily quota cap).

No GCP SDK is required — reports are sent via the REST API using urllib.
All errors in this module are silently swallowed so telemetry never
breaks the server.
"""

from __future__ import annotations

import json
import logging
import platform
import sys
import traceback
import urllib.error
import urllib.request
from datetime import UTC, datetime
from types import TracebackType

from src.config import (
    TELEMETRY_DRY_RUN,
    TELEMETRY_ENABLED,
    TELEMETRY_GCP_API_KEY,
    TELEMETRY_GCP_PROJECT,
)


logger = logging.getLogger(__name__)

_GCE_REPORT_URL = (
    "https://clouderrorreporting.googleapis.com/v1beta1"
    "/projects/{project_id}/events:report?key={api_key}"
)
_SERVICE_NAME = "imagin-studio-api-docs-mcp"


def _get_package_version() -> str:
    """Return the installed package version, falling back to 'unknown'."""
    try:
        from importlib.metadata import version

        return version("imagin-studio-api-docs-mcp")
    except Exception:
        return "unknown"


def _build_payload(
    exc_type: type[BaseException],
    exc_value: BaseException,
    tb: TracebackType | None,
) -> dict[str, object]:
    """Build the ReportedErrorEvent payload for the GCE REST API."""
    stack_trace = "".join(traceback.format_exception(exc_type, exc_value, tb))
    return {
        "eventTime": datetime.now(tz=UTC).isoformat(),
        "serviceContext": {
            "service": _SERVICE_NAME,
            "version": _get_package_version(),
        },
        "message": stack_trace,
        "context": {
            "httpRequest": {},
            "reportLocation": {
                "filePath": "",
                "lineNumber": 0,
                "functionName": "",
            },
            "sourceReferences": [],
        },
    }


def _send_report(
    project_id: str,
    api_key: str,
    payload: dict[str, object],
    *,
    dry_run: bool = False,
) -> None:
    """POST the error event payload to GCE Error Reporting.

    Silently swallows all exceptions — must never break the server.
    """
    if dry_run:
        logger.info(
            "Telemetry DRY RUN — payload:\n%s",
            json.dumps(payload, indent=2),
        )
        return

    url = _GCE_REPORT_URL.format(project_id=project_id, api_key=api_key)
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            logger.debug("Error reported to GCE (status %s)", resp.status)
    except urllib.error.HTTPError as exc:
        logger.debug("GCE error reporting HTTP error: %s %s", exc.code, exc.reason)
    except Exception as exc:
        logger.debug("GCE error reporting failed silently: %s", exc)


class _ErrorReporter:
    """Stateful reporter holding validated config."""

    def __init__(
        self,
        project_id: str,
        api_key: str,
        *,
        dry_run: bool = False,
    ) -> None:
        self._project_id = project_id
        self._api_key = api_key
        self._dry_run = dry_run

    def report(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        tb: TracebackType | None,
    ) -> None:
        """Build and send the report. Never raises."""
        try:
            payload = _build_payload(exc_type, exc_value, tb)
            # Enrich with runtime context
            ctx = payload.get("context")
            enriched: dict[str, object] = {**(ctx if isinstance(ctx, dict) else {}), "user": platform.platform()}
            payload["context"] = enriched
            _send_report(self._project_id, self._api_key, payload, dry_run=self._dry_run)
        except Exception:
            logger.debug("Unexpected error in telemetry reporter", exc_info=True)


# Module-level singleton, set by install_hooks()
_reporter: _ErrorReporter | None = None


def report_exception() -> None:
    """Report the current exception (must be called inside an except block).

    No-op if telemetry is disabled or no exception is active.
    """
    if _reporter is None:
        return
    exc_type, exc_value, tb = sys.exc_info()
    if exc_type is None or exc_value is None:
        return
    _reporter.report(exc_type, exc_value, tb)


def install_hooks() -> None:
    """Install sys.excepthook and asyncio exception handler if telemetry is enabled.

    Safe to call unconditionally — performs all opt-in checks internally.
    Idempotent: calling twice has no effect.
    """
    global _reporter

    if not TELEMETRY_ENABLED:
        logger.info(
            "Tip: set IMAGIN_DOCS_TELEMETRY=1 to help improve this tool "
            "by sending anonymous crash reports"
        )
        return

    if not TELEMETRY_GCP_PROJECT:
        logger.warning("Telemetry enabled but IMAGIN_DOCS_GCP_PROJECT is not set — disabling")
        return

    if not TELEMETRY_GCP_API_KEY and not TELEMETRY_DRY_RUN:
        logger.warning("Telemetry enabled but IMAGIN_DOCS_GCP_API_KEY is not set — disabling")
        return

    if _reporter is not None:
        return  # Already installed

    _reporter = _ErrorReporter(
        project_id=TELEMETRY_GCP_PROJECT,
        api_key=TELEMETRY_GCP_API_KEY,
        dry_run=TELEMETRY_DRY_RUN,
    )

    # --- sys.excepthook: catches synchronous unhandled exceptions ---
    _original_excepthook = sys.excepthook

    def _excepthook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        tb: TracebackType | None,
    ) -> None:
        _reporter.report(exc_type, exc_value, tb)
        _original_excepthook(exc_type, exc_value, tb)

    sys.excepthook = _excepthook

    logger.info(
        "Error telemetry enabled (project=%s, dry_run=%s)",
        TELEMETRY_GCP_PROJECT,
        TELEMETRY_DRY_RUN,
    )
