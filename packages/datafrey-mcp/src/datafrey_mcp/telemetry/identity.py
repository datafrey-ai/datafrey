"""Distinct ID extraction from the authenticated access token."""

from __future__ import annotations

from typing import Any


def extract_workos_sub(claims: dict[str, Any] | None) -> str | None:
    """Return the `sub` claim from a JWT claims dict, if it's a string."""
    if not claims:
        return None
    sub = claims.get("sub")
    return sub if isinstance(sub, str) else None


def get_distinct_id() -> str | None:
    """Return the WorkOS sub from the current request's access token, or None.

    The MCP server is authenticated for tool calls, so this returns the user's
    WorkOS `sub` for tool/session events. Returns None pre-auth or on failure.
    """
    try:
        from fastmcp.server.dependencies import get_access_token

        token = get_access_token()
        if token is None:
            return None
        return extract_workos_sub(getattr(token, "claims", None))
    except Exception:
        return None
