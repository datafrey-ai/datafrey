"""Keyring CRUD for access/refresh tokens + backend validation."""

from __future__ import annotations

SERVICE_NAME = "datafrey"
ACCESS_TOKEN_KEY = "datafrey:access_token"
REFRESH_TOKEN_KEY = "datafrey:refresh_token"

INSECURE_BACKEND_PATTERNS = ["Plaintext", "Null"]


def _check_keyring_backend() -> str:
    """Validate keyring backend is secure. Returns backend name."""
    import keyring

    from datafrey.exceptions import InsecureKeyringError

    backend = keyring.get_keyring()
    backend_name = type(backend).__name__
    if any(p in backend_name for p in INSECURE_BACKEND_PATTERNS):
        raise InsecureKeyringError(backend_name)
    return backend_name


def get_access_token() -> str | None:
    """Retrieve access token from keyring, or None if absent."""
    import keyring

    _check_keyring_backend()
    return keyring.get_password(SERVICE_NAME, ACCESS_TOKEN_KEY)


def get_refresh_token() -> str | None:
    """Retrieve refresh token from keyring, or None if absent."""
    import keyring

    _check_keyring_backend()
    return keyring.get_password(SERVICE_NAME, REFRESH_TOKEN_KEY)


def store_tokens(access_token: str, refresh_token: str) -> str:
    """Store both tokens in keyring. Returns backend name for trust signal."""
    import keyring

    backend_name = _check_keyring_backend()
    keyring.set_password(SERVICE_NAME, ACCESS_TOKEN_KEY, access_token)
    keyring.set_password(SERVICE_NAME, REFRESH_TOKEN_KEY, refresh_token)
    return backend_name


def clear_tokens() -> None:
    """Remove both tokens from keyring. Ignores missing entries."""
    import keyring

    for key in (ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY):
        try:
            keyring.delete_password(SERVICE_NAME, key)
        except keyring.errors.PasswordDeleteError:
            pass


def get_keyring_backend_name() -> str:
    """Return the active keyring backend display name."""
    import keyring

    backend = keyring.get_keyring()
    name = type(backend).__name__
    # Friendlier names
    if "Keychain" in name:
        return "macOS Keychain"
    if "SecretService" in name:
        return "GNOME Keyring"
    if "Windows" in name:
        return "Windows Credential Locker"
    return name
