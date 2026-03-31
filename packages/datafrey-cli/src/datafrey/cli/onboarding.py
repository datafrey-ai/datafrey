"""Database connection onboarding workflow helpers."""

from __future__ import annotations

import gc
import os

from datafrey.ui.console import err_console
from datafrey.ui.display import (
    print_docs_link,
    print_success,
    show_onboarding_panel,
)
from datafrey.ui.terminal import onboarding_prompt


def ensure_recent_auth() -> str:
    """Return a recently-issued access token, re-authenticating if needed."""
    from datafrey.auth import token_store
    from datafrey.auth.device_flow import check_recent_auth, start_device_flow

    env_token = os.environ.get("DATAFREY_TOKEN")
    if env_token:
        return env_token

    access_token = token_store.get_access_token()
    if not access_token:
        from datafrey.exceptions import NotAuthenticatedError

        raise NotAuthenticatedError("Not authenticated.")

    if not check_recent_auth(access_token):
        err_console.print(
            "Database connections require recent authentication (within 5 min). "
            "Please re-authenticate to continue."
        )
        result = start_device_flow()
        token_store.store_tokens(result["access_token"], result["refresh_token"])
        access_token = result["access_token"]
        print_success(
            f"Re-authenticated. Token stored in {token_store.get_keyring_backend_name()}"
        )

    return access_token


def run_onboarding(provider, choices: dict) -> None:
    """Walk user through SQL onboarding panels (forward-only)."""
    steps = provider.get_onboarding_steps(choices)
    for title, sql in steps:
        show_onboarding_panel(title, sql)
        onboarding_prompt(sql)


def encrypt_and_submit(
    client, provider_name: str, credentials: dict, review_fields: dict
):
    """Encrypt credentials, verify server key, and submit the database connection."""
    import os

    import jwt as pyjwt

    from datafrey.auth import token_store
    from datafrey.auth.encryption import encrypt_credentials
    from datafrey.config import get_api_url, is_mock_server
    from datafrey_api import DatabaseCreate, EncryptedCredentials

    # Fetch and verify public key
    pubkey_resp = client.get_public_key()

    api_url = get_api_url()
    if not is_mock_server(api_url):
        _verify_fingerprint(pubkey_resp.fingerprint)

    print_success(f"Server key verified  {pubkey_resp.fingerprint}")

    # Validate credentials against provider schema before encrypting
    from datafrey_api import Provider, validate_credentials

    sensitive = {k: v for k, v in credentials.items() if k not in ("name",)}
    validate_credentials(Provider(provider_name), sensitive)

    # Derive AAD from authenticated user's sub claim.
    # The server must pass the same sub as AAD during decryption,
    # preventing replay of encrypted credentials under a different account.
    access_token = os.environ.get("DATAFREY_TOKEN") or token_store.get_access_token()
    try:
        payload = pyjwt.decode(access_token, options={"verify_signature": False})
        user_sub = payload.get("sub", "")
    except Exception:
        user_sub = ""
    aad = user_sub.encode("utf-8") if user_sub else None

    encrypted = encrypt_credentials(sensitive, pubkey_resp.public_key, aad=aad)

    print_success("Credentials encrypted (AES-256-GCM + RSA-OAEP) before transmission")
    print_docs_link("encryption")

    # Clear sensitive data
    del sensitive
    del credentials
    gc.collect()

    # Submit
    create_data = DatabaseCreate(
        provider=provider_name,
        name=review_fields["Name"],
        encrypted_credentials=EncryptedCredentials(**encrypted),
    )

    client._show_spinner = False
    with err_console.status("Creating connection..."):
        result = client.create_database(create_data)
    client._show_spinner = True

    from datafrey.ui.console import console

    console.print()
    print_success(f"Database saved: {result.name}")
    console.print(f"  ID:       {result.id}")
    console.print(f"  Provider: {result.provider.value}")
    console.print(f"  Host:     {result.host}")

    return result


def wait_for_connection(
    client, db_id: str, *, poll_interval: float = 3.0, max_wait: float = 120.0
) -> tuple:
    """Poll until database status leaves 'loading'.

    Returns ``(status, was_skipped)`` where *status* is a
    :class:`DatabaseStatus` or ``None`` on timeout/skip.
    """
    import sys
    import time

    from datafrey_api import DatabaseStatus

    client._show_spinner = False

    def _poll_once():
        databases = client.list_databases()
        db = next((d for d in databases if d.id == db_id), None)
        if db and db.status != DatabaseStatus.loading:
            return db.status
        return None

    # Non-interactive: poll without skip option
    if not sys.stdin.isatty():
        with err_console.status("Verifying connection…"):
            deadline = time.time() + max_wait
            while time.time() < deadline:
                try:
                    status = _poll_once()
                    if status is not None:
                        return status, False
                except Exception:
                    pass
                time.sleep(poll_interval)
        return None, False

    # Interactive: poll with skip option (Enter to skip)
    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        with err_console.status(
            "Verifying connection… [dim]press Enter to skip[/dim]"
        ):
            deadline = time.time() + max_wait
            last_poll = 0.0
            while time.time() < deadline:
                # Non-blocking keypress check (200ms timeout)
                if select.select([sys.stdin], [], [], 0.2)[0]:
                    ch = sys.stdin.read(1)
                    if ch in ("\r", "\n"):
                        return None, True
                    if ch == "\x03":
                        raise KeyboardInterrupt

                now = time.time()
                if now - last_poll >= poll_interval:
                    last_poll = now
                    try:
                        status = _poll_once()
                        if status is not None:
                            return status, False
                    except Exception:
                        pass  # retry on next interval

        return None, False  # timeout
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# Pinned fingerprint for production. Updated on key rotation.
PINNED_KEY_FINGERPRINT: str | None = None  # Set when production key is known


def _verify_fingerprint(fingerprint: str) -> None:
    """Verify server key fingerprint against pinned value."""
    if PINNED_KEY_FINGERPRINT is None:
        return  # No pin configured yet
    if fingerprint != PINNED_KEY_FINGERPRINT:
        from datafrey.exceptions import FingerprintMismatchError
        from datafrey.ui.display import show_security_warning

        show_security_warning(PINNED_KEY_FINGERPRINT, fingerprint)
        raise FingerprintMismatchError(PINNED_KEY_FINGERPRINT, fingerprint)
