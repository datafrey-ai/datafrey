"""Map HTTP status codes to CLI exceptions."""

from __future__ import annotations

import httpx

from datafrey.exceptions import (
    ApiRequestError,
    NotAuthenticatedError,
    SessionExpiredError,
)


def raise_for_status(response: httpx.Response) -> None:
    """Raise a DatafreyError subclass for non-2xx responses."""
    if response.is_success:
        return

    status = response.status_code
    try:
        body = response.json()
        error = body.get("error", "unknown")
        message = body.get("message", response.reason_phrase)
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
