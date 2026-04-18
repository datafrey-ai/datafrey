"""HTTP API client wrapping httpx."""

from __future__ import annotations

import time

import httpx
from datafrey_api import (
    DatabaseCreate,
    DatabaseCreated,
    DatabaseRecord,
    IndexStatus,
    PublicKeyResponse,
    StatusResponse,
)

from datafrey.api.errors import raise_for_status
from datafrey.exceptions import NetworkError

_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
_MAX_RETRIES = 2
_RETRY_BACKOFF = 1.0  # seconds, doubled each retry


class HttpApiClient:
    """Thin wrapper around httpx for the Datafrey management API."""

    _show_spinner: bool = True

    def __init__(self, base_url: str, token: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=_TIMEOUT,
            follow_redirects=False,
        )

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        if self._show_spinner:
            from datafrey.ui.console import err_console

            with err_console.status(""):
                return self._do_request(method, path, **kwargs)
        return self._do_request(method, path, **kwargs)

    def _do_request(self, method: str, path: str, **kwargs) -> httpx.Response:
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = self._client.request(method, path, **kwargs)
            except (httpx.ConnectError, httpx.TimeoutException):
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_BACKOFF * (2**attempt))
                    continue
                # Drop the chain: the underlying httpx exception holds the
                # outbound Request (with its Authorization header).
                raise NetworkError(self._base_url) from None
            raise_for_status(resp)
            return resp
        raise NetworkError(self._base_url) from None  # unreachable, keeps mypy happy

    # ── Management endpoints ──

    def get_status(self) -> StatusResponse:
        resp = self._request("GET", "/status")
        return StatusResponse.model_validate(resp.json())

    def list_databases(self) -> list[DatabaseRecord]:
        resp = self._request("GET", "/databases")
        return [DatabaseRecord.model_validate(d) for d in resp.json()]

    def create_database(self, data: DatabaseCreate) -> DatabaseCreated:
        resp = self._request("POST", "/databases", json=data.model_dump())
        return DatabaseCreated.model_validate(resp.json())

    def delete_database(self, db_id: str) -> None:
        self._request("DELETE", f"/databases/{db_id}")

    def reindex_database(self, db_id: str) -> None:
        self._request("POST", f"/databases/{db_id}/reindex")

    def drop_index(self, db_id: str) -> None:
        self._request("DELETE", f"/databases/{db_id}/index")

    def get_index_status(self, db_id: str) -> IndexStatus:
        resp = self._request("GET", f"/databases/{db_id}/index-status")
        return IndexStatus.model_validate(resp.json())

    def get_public_key(self) -> PublicKeyResponse:
        resp = self._request("GET", "/databases/public-key")
        return PublicKeyResponse.model_validate(resp.json())

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HttpApiClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
