"""PostHog client: lazy init, async send, atexit flush, opt-out."""

from __future__ import annotations

import atexit
import os
import platform
import sys
from typing import Any

# Public write-only key — safe to hardcode (same model as Sentry DSN).
# Shared with the CLI so CLI→MCP funnel events land on the same person.
POSTHOG_PROJECT_KEY = "phc_vi6z3VS6dT4wj9DRJxHYAUhXK3o2GPHTxGa2ndJFTWv8"
POSTHOG_HOST = "https://us.i.posthog.com"

_OPT_OUT_VARS = ("DATAFREY_TELEMETRY_DISABLED", "DO_NOT_TRACK")
_TRUTHY = ("1", "true", "yes", "on")

_client_instance: Any = None


def is_disabled() -> bool:
    """True if telemetry is opt'd out or no key is configured.

    Re-read on every call so toggling DATAFREY_TELEMETRY_DISABLED or
    DO_NOT_TRACK mid-session takes effect immediately.
    """
    if not POSTHOG_PROJECT_KEY or POSTHOG_PROJECT_KEY.startswith("phc_REPLACE"):
        return True
    for var in _OPT_OUT_VARS:
        if os.environ.get(var, "").strip().lower() in _TRUTHY:
            return True
    return False


def _client_or_none() -> Any:
    """Lazily construct the PostHog client; returns None if unavailable."""
    global _client_instance
    if is_disabled():
        return None
    if _client_instance is not None:
        return _client_instance
    try:
        from posthog import Posthog

        _client_instance = Posthog(
            project_api_key=POSTHOG_PROJECT_KEY,
            host=POSTHOG_HOST,
            disable_geoip=True,
        )
        atexit.register(_shutdown)
    except Exception:
        return None
    return _client_instance


def _shutdown() -> None:
    if _client_instance is None:
        return
    try:
        _client_instance.shutdown()
    except Exception:
        pass


def _default_properties() -> dict[str, Any]:
    try:
        from datafrey_mcp import __version__ as mcp_version
    except Exception:
        mcp_version = "unknown"

    return {
        "service": "mcp_server",
        "mcp_version": mcp_version,
        "os": platform.system().lower(),
        "arch": platform.machine().lower(),
        "python_version": (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        ),
        # The server's IP is not the user's, but suppress regardless.
        "$ip": "",
    }


def track(event: str, distinct_id: str | None = None, **properties: Any) -> None:
    """Fire a PostHog event. Never raises, never blocks.

    If `distinct_id` is None, the event is dropped — we only track
    identified users on the server side (no anon ID concept on a hosted server).
    """
    if is_disabled():
        return
    if not distinct_id:
        return
    try:
        client = _client_or_none()
        if client is None:
            return
        merged = {**_default_properties(), **properties}
        client.capture(
            distinct_id=distinct_id,
            event=event,
            properties=merged,
        )
    except Exception:
        pass


def flush() -> None:
    """Flush queued events. Never raises."""
    if _client_instance is None:
        return
    try:
        _client_instance.flush()
    except Exception:
        pass
