"""Configuration via environment variables."""

from __future__ import annotations

import os
import re

_ALLOWED_AGENT_URL_PATTERNS = (
    re.compile(r"^https://[a-zA-Z0-9.-]+\.datafrey\.ai(/.*)?$"),
    re.compile(r"^http://localhost(:\d+)?(/.*)?$"),
    re.compile(r"^http://127\.0\.0\.1(:\d+)?(/.*)?$"),
)


def _validate_agent_api_url(url: str) -> str:
    for pattern in _ALLOWED_AGENT_URL_PATTERNS:
        if pattern.match(url):
            return url
    raise RuntimeError(
        f"DATAFREY_AGENT_API_URL rejected: {url!r}. "
        "Allowed: https://*.datafrey.ai, http://localhost, http://127.0.0.1."
    )


AGENT_API_URL: str = _validate_agent_api_url(
    os.environ.get("DATAFREY_AGENT_API_URL", "https://api.datafrey.ai/agent/v1")
)

# MCP_HOST binds to 0.0.0.0 by default so the server is reachable when run
# in a container / behind an ingress. Auth is enforced upstream by AuthKit /
# WorkOS — the server rejects unauthenticated traffic. If you run the server
# only on a trusted host, override with DATAFREY_MCP_HOST=127.0.0.1.
MCP_HOST: str = os.environ.get("DATAFREY_MCP_HOST", "0.0.0.0")
MCP_PORT: int = int(os.environ.get("DATAFREY_MCP_PORT", "8080"))

WORKOS_AUTHKIT_DOMAIN: str = os.environ.get(
    "WORKOS_AUTHKIT_DOMAIN", "valiant-glow-53.authkit.app"
)
WORKOS_CLIENT_ID: str = os.environ.get(
    "WORKOS_CLIENT_ID", "client_01KM2ZAT5192KV11CXKJXBDCZD"
)
MCP_BASE_URL: str = os.environ.get("DATAFREY_MCP_BASE_URL", "")
