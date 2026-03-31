"""Auth middleware: get_authenticated_client() — DATAFREY_TOKEN or keyring."""

from __future__ import annotations

import os
import time

from datafrey.api.client import HttpApiClient
from datafrey.auth import token_store
from datafrey.config import get_api_url
from datafrey.exceptions import NotAuthenticatedError, SessionExpiredError


def get_authenticated_client() -> HttpApiClient:
    """Return an API client with a valid token.

    Checks DATAFREY_TOKEN env var first, then keyring.
    Refreshes token if expiring soon.
    """
    env_token = os.environ.get("DATAFREY_TOKEN")
    if env_token:
        return HttpApiClient(base_url=get_api_url(), token=env_token)

    access_token = token_store.get_access_token()
    if not access_token:
        raise NotAuthenticatedError("Not authenticated.")

    # Check if token needs refresh (expires in <60s)
    try:
        import jwt

        payload = jwt.decode(access_token, options={"verify_signature": False})
        exp = payload.get("exp", 0)
        if exp and (exp - time.time()) < 60:
            access_token = _refresh_or_fail()
    except Exception:
        pass  # If decode fails, try using the token as-is

    return HttpApiClient(base_url=get_api_url(), token=access_token)


def _refresh_or_fail() -> str:
    """Attempt token refresh. Clears keyring and raises on failure."""
    from datafrey.auth.device_flow import refresh_access_token

    refresh_token = token_store.get_refresh_token()
    if not refresh_token:
        token_store.clear_tokens()
        raise SessionExpiredError("Session expired.")

    result = refresh_access_token(refresh_token)
    if not result:
        token_store.clear_tokens()
        raise SessionExpiredError("Session expired.")

    token_store.store_tokens(result["access_token"], result["refresh_token"])
    return result["access_token"]
