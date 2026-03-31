"""Configuration: API URL validation, WorkOS client ID, local config file."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

DEFAULT_API_URL = "https://api.datafrey.ai/manage/v1"
WORKOS_CLIENT_ID = (
    "client_01KM2ZAT5192KV11CXKJXBDCZD"  # Public client ID — safe to hardcode
)

ALLOWED_URL_PATTERNS = [
    re.compile(r"^https://[a-zA-Z0-9.-]+\.datafrey\.ai(/.*)?$"),
    re.compile(r"^http://localhost(:\d+)?(/.*)?$"),
    re.compile(r"^http://127\.0\.0\.1(:\d+)?(/.*)?$"),
]

CONFIG_DIR = Path.home() / ".datafrey"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_api_url() -> str:
    """Return validated API base URL from env or default."""
    url = os.environ.get("DATAFREY_API_URL", DEFAULT_API_URL)
    validate_api_url(url)
    return url


def validate_api_url(url: str) -> None:
    """Raise if URL doesn't match the allowlist."""
    from datafrey.exceptions import UntrustedURLError

    for pattern in ALLOWED_URL_PATTERNS:
        if pattern.match(url):
            return
    raise UntrustedURLError(url)


def is_mock_server(url: str) -> bool:
    """True if the URL points to localhost (mock server)."""
    return url.startswith("http://localhost") or url.startswith("http://127.0.0.1")


def load_config() -> dict:
    """Load ~/.datafrey/config.json, returning {} if missing."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(data: dict) -> None:
    """Write ~/.datafrey/config.json with restrictive permissions."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.chmod(0o700)
    CONFIG_FILE.write_text(json.dumps(data, indent=2) + "\n")
    CONFIG_FILE.chmod(0o600)
