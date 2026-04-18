"""Map HTTP status codes to CLI exceptions."""

from __future__ import annotations

import httpx

from datafrey.exceptions import (
    ApiRequestError,
    NotAuthenticatedError,
    SessionExpiredError,
)


_MAX_MESSAGE_LEN = 512


def _sanitize(value: object, default: str) -> str:
    """Coerce a server-provided string into a safe, bounded plain-text value.

    Rich markup and ANSI escapes from a compromised or misconfigured server
    must never influence how errors render in the user's terminal.
    """
    from rich.markup import escape

    text = value if isinstance(value, str) else default
    # Drop ANSI escapes, cap length, then escape Rich markup.
    text = text.replace("\x1b", "").replace("\r", " ").strip()
    if len(text) > _MAX_MESSAGE_LEN:
        text = text[:_MAX_MESSAGE_LEN] + "…"
    return escape(text)


def raise_for_status(response: httpx.Response) -> None:
    """Raise a DatafreyError subclass for non-2xx responses."""
    if response.is_success:
        return

    status = response.status_code
    try:
        body = response.json()
        error = _sanitize(body.get("error", "unknown"), "unknown")
        message = _sanitize(
            body.get("message", response.reason_phrase),
            response.reason_phrase or f"HTTP {status}",
        )
    except Exception:
        error = "unknown"
        message = response.reason_phrase or f"HTTP {status}"

    if status == 401:
        raise NotAuthenticatedError(message)
    if status == 403:
        raise SessionExpiredError(message)

    err = ApiRequestError(status, error, message)
    if status == 404:
        err.hint = "Run 'datafrey db list' to see available databases."
    elif status == 429:
        retry = response.headers.get("Retry-After", "a few seconds")
        err.hint = f"Rate limited. Try again in {retry}."
    raise err
