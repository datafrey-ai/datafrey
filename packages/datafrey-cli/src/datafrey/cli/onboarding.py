"""Database connection onboarding workflow helpers."""

from __future__ import annotations

import os

from datafrey.ui.console import err_console
from datafrey.ui.display import (
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
    if is_mock_server(api_url):
        print_success(
            f"Server key fingerprint  {pubkey_resp.fingerprint}  [dim](mock)[/]"
        )
    else:
        # For any real (non-mock) API URL the pin list must be non-empty and
        # the server key must match. _verify_fingerprint raises on mismatch;
        # here we also fail closed when no pin is configured, so a release
        # that accidentally ships with PINNED_KEY_FINGERPRINTS=[] cannot
        # silently downgrade MITM protection.
        if not _verify_fingerprint(pubkey_resp.fingerprint):
            from datafrey.exceptions import FingerprintMismatchError

            raise FingerprintMismatchError("(no pinned fingerprint)", pubkey_resp.fingerprint)
        print_success(f"Server key verified  {pubkey_resp.fingerprint}")

    # Validate credentials against provider schema before encrypting
    from datafrey_api import Provider, validate_credentials

    sensitive = {k: v for k, v in credentials.items() if k not in ("name",)}
    validate_credentials(Provider(provider_name), sensitive)

    # Derive AAD from authenticated user's sub claim.
    # The server must pass the same sub as AAD during decryption,
    # preventing replay of encrypted credentials under a different account.
    # Fail closed: if we can't derive a sub, we won't submit without AAD.
    access_token = os.environ.get("DATAFREY_TOKEN") or token_store.get_access_token()
    try:
        payload = pyjwt.decode(access_token, options={"verify_signature": False})
        user_sub = payload.get("sub") or ""
    except Exception:
        user_sub = ""
    if not user_sub:
        raise RuntimeError(
            "Could not derive tenant binding (sub claim) from access token. "
            "Re-run `datafrey login` and try again."
        )
    aad = user_sub.encode("utf-8")

    encrypted = encrypt_credentials(sensitive, pubkey_resp.public_key, aad=aad)

    print_success("Credentials encrypted (AES-256-GCM + RSA-OAEP) before transmission")

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


# Accepted production server key fingerprints.
#
# Rotation: add the new fingerprint BEFORE the backend starts serving it,
# ship a CLI release, wait for users to upgrade, flip the backend, then
# ship a release that drops the old fingerprint.
#
# Override for self-hosting / staging via DATAFREY_PINNED_KEY_FINGERPRINT
# (comma-separated list). If both the constant and the env are empty,
# pinning is skipped and the fingerprint is shown as "(unpinned)".
PINNED_KEY_FINGERPRINTS: list[str] = [
    "SHA256:4FSWuSx0mcbXNH/yJf4kvS7xxE7IxQyR6WqahHTqU4s=",
]


def _accepted_fingerprints() -> list[str]:
    """Return the pin list plus any additional pins from env.

    The env override EXTENDS the built-in list; it cannot remove pins.
    This prevents a malicious env var from silently disabling the pin check
    by pointing it at an attacker-controlled fingerprint only.
    """
    env = os.environ.get("DATAFREY_PINNED_KEY_FINGERPRINT", "").strip()
    extra = [p.strip() for p in env.split(",") if p.strip()] if env else []
    return [*PINNED_KEY_FINGERPRINTS, *extra]


def _verify_fingerprint(fingerprint: str) -> bool:
    """Check fingerprint against pinned list (constant-time comparison).

    Returns True if a pin is active and fingerprint matches.
    Returns False if no pin is configured.
    Raises FingerprintMismatchError if a pin is active but doesn't match.
    """
    import hmac

    allowed = _accepted_fingerprints()
    if not allowed:
        return False
    for pin in allowed:
        if hmac.compare_digest(pin, fingerprint):
            return True

    from datafrey.exceptions import FingerprintMismatchError
    from datafrey.ui.display import show_security_warning

    expected = " | ".join(allowed)
    show_security_warning(expected, fingerprint)
    raise FingerprintMismatchError(expected, fingerprint)
