"""Anonymous + WorkOS identity for PostHog distinct_id."""

from __future__ import annotations

import secrets

from datafrey.config import load_config, save_config


def get_or_create_anon_id() -> str:
    """Return persisted anon ID, generating one on first call."""
    config = load_config()
    anon = config.get("telemetry_anon_id")
    if anon:
        return anon
    anon = secrets.token_hex(16)
    config["telemetry_anon_id"] = anon
    save_config(config)
    return anon


def get_workos_user_id() -> str | None:
    return load_config().get("workos_user_id")


def set_workos_user_id(user_id: str) -> None:
    config = load_config()
    config["workos_user_id"] = user_id
    save_config(config)


def get_distinct_id() -> str:
    """WorkOS sub if logged in, else persisted anon ID."""
    return get_workos_user_id() or get_or_create_anon_id()


def extract_workos_sub(access_token: str) -> str | None:
    """Decode the JWT and return the `sub` claim, or None on failure."""
    try:
        import jwt as pyjwt

        payload = pyjwt.decode(access_token, options={"verify_signature": False})
        sub = payload.get("sub")
        return sub if isinstance(sub, str) else None
    except Exception:
        return None


def identify_user(workos_sub: str) -> None:
    """Alias anon→workos_sub on PostHog.

    Sends only the pseudonymous WorkOS `sub`. Email/name stay in WorkOS;
    resolve via GET /user_management/users/{sub} when actually needed,
    so a PostHog compromise can't leak user identities.

    Full no-op when telemetry is disabled — no local state, no network.
    """
    from datafrey.telemetry.client import _client_or_none, is_disabled

    if is_disabled():
        return
    try:
        anon = get_or_create_anon_id()
        client = _client_or_none()
        if client is None:
            return
        client.alias(previous_id=anon, distinct_id=workos_sub)
        set_workos_user_id(workos_sub)
    except Exception:
        pass
