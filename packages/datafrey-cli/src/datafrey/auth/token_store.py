"""Keyring CRUD for access/refresh tokens + backend validation."""

from __future__ import annotations

SERVICE_NAME = "datafrey"
ACCESS_TOKEN_KEY = "datafrey:access_token"
REFRESH_TOKEN_KEY = "datafrey:refresh_token"

# Allow-list of OS-native keyring backends keyed by module.classname. Using
# the qualified name (not just the class __name__) prevents a third-party
# `keyrings.alt.*` backend (Plaintext, Null, RegistryKeyring, EncryptedKeyring)
# from matching a bare name like "Keyring" by accident.
ALLOWED_BACKENDS: frozenset[str] = frozenset({
    "keyring.backends.macOS.Keyring",
    "keyring.backends.Windows.WinVaultKeyring",
    "keyring.backends.SecretService.Keyring",
    "keyring.backends.libsecret.Keyring",
    "keyring.backends.kwallet.DBusKeyring",
})


def _backend_qualname(backend) -> str:
    cls = type(backend)
    return f"{cls.__module__}.{cls.__name__}"


def _check_keyring_backend() -> str:
    """Validate keyring backend against allow-list. Returns class name."""
    import keyring

    from datafrey.exceptions import InsecureKeyringError

    backend = keyring.get_keyring()
    qualname = _backend_qualname(backend)
    if qualname not in ALLOWED_BACKENDS:
        raise InsecureKeyringError(qualname)
    return type(backend).__name__


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
    """Store both tokens in keyring.

    Rolls back the access-token write if the refresh-token write fails so
    the stored pair is never out of sync.

    Returns backend class name for trust signalling.
    """
    import keyring

    backend_name = _check_keyring_backend()
    keyring.set_password(SERVICE_NAME, ACCESS_TOKEN_KEY, access_token)
    try:
        keyring.set_password(SERVICE_NAME, REFRESH_TOKEN_KEY, refresh_token)
    except Exception:
        try:
            keyring.delete_password(SERVICE_NAME, ACCESS_TOKEN_KEY)
        except Exception:
            pass
        raise
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
