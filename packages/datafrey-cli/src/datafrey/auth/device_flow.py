"""WorkOS device authorization flow (RFC 8628)."""

from __future__ import annotations

import time
import webbrowser

import httpx

from datafrey.config import WORKOS_CLIENT_ID
from datafrey.exceptions import DatafreyError
from datafrey.ui.clipboard import copy_to_clipboard as _copy_to_clipboard
from datafrey.ui.console import err_console
from datafrey.ui.display import show_device_code_panel

WORKOS_BASE_URL = "https://api.workos.com"
AUTHORIZE_URL = f"{WORKOS_BASE_URL}/user_management/authorize/device"
TOKEN_URL = f"{WORKOS_BASE_URL}/user_management/authenticate"


class DeviceFlowError(DatafreyError):
    pass


def start_device_flow(no_browser: bool = False) -> dict:
    """Run the full device authorization flow. Returns {access_token, refresh_token, user}."""
    # Step 1: Request device code
    resp = httpx.post(
        AUTHORIZE_URL,
        json={"client_id": WORKOS_CLIENT_ID},
        timeout=10.0,
    )
    if not resp.is_success:
        raise DeviceFlowError(
            "Failed to start device authorization.",
            hint="Check your network and try again.",
        )

    data = resp.json()
    device_code = data["device_code"]
    user_code = data["user_code"]
    verification_uri = data["verification_uri"]
    interval = data.get("interval", 5)
    expires_in = data.get("expires_in", 900)

    # Step 2: Copy code + show panel + open browser
    copied = _copy_to_clipboard(user_code)
    show_device_code_panel(user_code, verification_uri, copied=copied)

    if not no_browser:
        try:
            webbrowser.open(verification_uri)
        except Exception:
            err_console.print(
                "[dim]Could not open browser. Visit the URL above manually.[/]"
            )

    # Step 3: Poll for completion
    deadline = time.time() + expires_in
    retries = 0

    with err_console.status("Waiting for browser authentication...") as _:
        while time.time() < deadline:
            time.sleep(interval)

            try:
                poll_resp = httpx.post(
                    TOKEN_URL,
                    json={
                        "client_id": WORKOS_CLIENT_ID,
                        "device_code": device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    },
                    timeout=10.0,
                )
                retries = 0 # Reset on success
            except (httpx.ConnectError, httpx.TimeoutException):
                retries += 1
                if retries >= 3:
                    raise DeviceFlowError(
                        "Network error during authentication.",
                        hint="Check your internet connection and try again.",
                    )
                continue

            if poll_resp.status_code == 200:
                result = poll_resp.json()
                return {
                    "access_token": result["access_token"],
                    "refresh_token": result["refresh_token"],
                    "user": result.get("user", {}),
                }

            # Handle pending/error states
            try:
                error_data = poll_resp.json()
                error_code = error_data.get("error", "")
            except Exception:
                error_code = ""

            if error_code == "authorization_pending":
                continue
            elif error_code == "slow_down":
                interval += 5
            elif error_code == "expired_token":
                raise DeviceFlowError(
                    "Authorization expired.", hint="Run 'datafrey login' to try again."
                )
            elif error_code == "access_denied":
                raise DeviceFlowError(
                    "Authorization denied.", hint="Run 'datafrey login' to try again."
                )

    raise DeviceFlowError(
        "Authorization timed out.", hint="Run 'datafrey login' to try again."
    )


def refresh_access_token(refresh_token: str) -> dict:
    """Exchange a refresh token for new tokens. Returns {access_token, refresh_token}."""
    resp = httpx.post(
        TOKEN_URL,
        json={
            "client_id": WORKOS_CLIENT_ID,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=10.0,
    )
    if not resp.is_success:
        return {}
    data = resp.json()
    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }


def check_recent_auth(access_token: str) -> bool:
    """True if the JWT was issued within the last 5 minutes."""
    import jwt

    MAX_AUTH_AGE_SECONDS = 300
    try:
        payload = jwt.decode(access_token, options={"verify_signature": False})
        return (time.time() - payload.get("iat", 0)) <= MAX_AUTH_AGE_SECONDS
    except Exception:
        return False
