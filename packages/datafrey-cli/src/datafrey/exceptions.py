"""DatafreyError hierarchy — every exception carries what happened + what to do."""

from __future__ import annotations


class DatafreyError(Exception):
    """Base for all CLI errors. Subclasses provide hint text."""

    hint: str = ""

    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        if hint:
            self.hint = hint


class NotAuthenticatedError(DatafreyError):
    hint = "Run 'datafrey login' to sign in."


class SessionExpiredError(DatafreyError):
    hint = "Run 'datafrey login' to re-authenticate."


class InsecureKeyringError(DatafreyError):
    def __init__(self, backend_name: str) -> None:
        super().__init__(
            f"Keyring backend '{backend_name}' is not on the allow-list.",
            hint=(
                "Datafrey requires an OS-native keyring:\n"
                "  macOS:   Keychain (built-in)\n"
                "  Windows: Credential Locker (built-in)\n"
                "  Linux:   GNOME Keyring, KWallet, or libsecret\n\n"
                "On Linux, install and unlock your keyring service, then retry.\n"
                "See: https://docs.datafrey.ai"
            ),
        )


class UntrustedURLError(DatafreyError):
    def __init__(self, url: str) -> None:
        super().__init__(
            f"Untrusted API URL: {url}",
            hint=(
                "Allowed patterns:\n"
                "  https://*.datafrey.ai\n"
                "  http://localhost:*\n"
                "  http://127.0.0.1:*"
            ),
        )


class ApiRequestError(DatafreyError):
    """HTTP-level error from the backend."""

    def __init__(self, status_code: int, error: str, message: str) -> None:
        self.status_code = status_code
        self.error_code = error
        super().__init__(message)


class ReauthRequiredError(DatafreyError):
    hint = ""  # Handled inline by db connect


class FingerprintMismatchError(DatafreyError):
    def __init__(self, expected: str, got: str) -> None:
        super().__init__(
            "Server key fingerprint mismatch.",
            hint=(
                f"Expected: {expected}\n"
                f"Got:      {got}\n\n"
                "Most likely the server key was rotated and your CLI is out of date.\n"
                "Upgrade and retry:\n"
                "  pip install -U datafrey\n"
                "  # or:\n"
                "  uv tool upgrade datafrey\n\n"
                "If upgrading doesn't resolve it, this could indicate a MITM attack.\n"
                "Do NOT proceed. Email slava+security@datafrey.ai."
            ),
        )


class NetworkError(DatafreyError):
    def __init__(self, host: str) -> None:
        super().__init__(
            f"Could not connect to {host} (network timeout).",
            hint=(
                "Check your internet connection and try again.\n"
                "Status: https://status.datafrey.ai"
            ),
        )
