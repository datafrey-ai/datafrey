"""Configuration: API URL validation, WorkOS client ID, local config file."""

from __future__ import annotations

import json
import os
import re
import stat
import tempfile
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


def _ensure_config_dir() -> None:
    """Create (or tighten permissions on) ~/.datafrey."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        CONFIG_DIR.chmod(0o700)
    except OSError:
        pass  # read-only FS, best-effort


def load_config() -> dict:
    """Load ~/.datafrey/config.json, returning {} if missing.

    Refuses to follow symlinks or read files owned by another user so a
    malicious local process cannot substitute a config under our nose.
    """
    _ensure_config_dir()
    try:
        fd = os.open(str(CONFIG_FILE), os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return {}
    except OSError as e:
        # ELOOP means the path is a symlink; refuse.
        raise RuntimeError(f"Refusing to read config: {e}") from None
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise RuntimeError(f"Refusing to read config: {CONFIG_FILE} is not a regular file")
        if st.st_uid != os.getuid():
            raise RuntimeError(
                f"Refusing to read config: {CONFIG_FILE} is owned by uid {st.st_uid}, not {os.getuid()}"
            )
        # Tighten mode if it has been loosened out-of-band.
        if stat.S_IMODE(st.st_mode) != 0o600:
            try:
                os.fchmod(fd, 0o600)
            except OSError:
                pass
        with os.fdopen(fd, "r") as f:
            return json.loads(f.read() or "{}")
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        raise


def save_config(data: dict) -> None:
    """Write ~/.datafrey/config.json atomically with restrictive permissions."""
    _ensure_config_dir()
    payload = json.dumps(data, indent=2) + "\n"

    # Write to a temp file in the same directory, then atomic-rename over
    # the target. Readers never observe a partial file or a wider-than-0o600
    # mode window.
    fd, tmp_path = tempfile.mkstemp(
        prefix=".config.", suffix=".tmp", dir=str(CONFIG_DIR)
    )
    try:
        try:
            os.fchmod(fd, 0o600)
        except OSError:
            pass
        with os.fdopen(fd, "w") as f:
            f.write(payload)
        os.replace(tmp_path, str(CONFIG_FILE))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
