"""Configuration via environment variables."""

from __future__ import annotations

import os

AGENT_API_URL: str = os.environ.get(
    "DATAFREY_AGENT_API_URL", "https://api.datafrey.ai/agent/v1"
)

MCP_HOST: str = os.environ.get("DATAFREY_MCP_HOST", "0.0.0.0")
MCP_PORT: int = int(os.environ.get("DATAFREY_MCP_PORT", "8080"))

WORKOS_AUTHKIT_DOMAIN: str = os.environ.get(
    "WORKOS_AUTHKIT_DOMAIN", "valiant-glow-53.authkit.app"
)
WORKOS_CLIENT_ID: str = os.environ.get(
    "WORKOS_CLIENT_ID", "client_01KM2ZAT5192KV11CXKJXBDCZD"
)
MCP_BASE_URL: str = os.environ.get("DATAFREY_MCP_BASE_URL", "")
