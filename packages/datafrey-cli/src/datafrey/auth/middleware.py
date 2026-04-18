"""Auth middleware: get_authenticated_client() — DATAFREY_TOKEN or keyring."""

from __future__ import annotations

import os
import time

import httpx

from datafrey.api.client import HttpApiClient
from datafrey.auth import token_store
from datafrey.config import get_api_url
from datafrey.exceptions import NotAuthenticatedError, SessionExpiredError


def get_authenticated_client() -> HttpApiClient:
    """Return an API client with a valid token.

    Checks DATAFREY_TOKEN env var first, then keyring.
    Refreshes token if expiring soon. Transient failures fall back to the
    existing token (which may still have seconds of validity); only an
    explicit 400/401 from the IdP clears the keyring.
    """
    env_token = os.environ.get("DATAFREY_TOKEN")
    if env_token:
        return HttpApiClient(base_url=get_api_url(), token=env_token)

    access_token = token_store.get_access_token()
    if not access_token:
        raise NotAuthenticatedError("Not authenticated.")

    try:
        import jwt

        payload = jwt.decode(access_token, options={"verify_signature": False})
        exp = payload.get("exp", 0)
    except Exception:
        exp = 0

    if exp and (exp - time.time()) < 60:
        refreshed = _refresh_or_none()
        if refreshed is not None:
            access_token = refreshed

    return HttpApiClient(base_url=get_api_url(), token=access_token)


def _refresh_or_none() -> str | None:
    """Attempt token refresh.

    Returns new access token on success.
    Returns None on transient errors (network, 5xx) — the caller keeps the
    existing token instead of logging the user out because the IdP blinked.
    Raises SessionExpiredError on explicit auth rejection (400/401) after
    clearing stored tokens.
    """
    from datafrey.auth.device_flow import refresh_access_token

    refresh_token = token_store.get_refresh_token()
    if not refresh_token:
        token_store.clear_tokens()
        raise SessionExpiredError("Session expired.")

    try:
        result = refresh_access_token(refresh_token)
    except httpx.HTTPError:
        return None

    if not result:
        token_store.clear_tokens()
        raise SessionExpiredError("Session expired.")

    token_store.store_tokens(result["access_token"], result["refresh_token"])
    return result["access_token"]
