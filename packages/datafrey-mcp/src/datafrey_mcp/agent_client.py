"""Async HTTP client for the datafrey Agent API."""

from __future__ import annotations

import httpx
from datafrey_api import PlanRequest, PlanResponse, RunRequest, RunResponse


class AgentApiError(Exception):
    """Agent API returned a non-2xx. Never carries the outbound request."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"Agent API {status_code}: {message}")


class AgentApiClient:
    """Forwards MCP tool calls to /agent/v1/ endpoints."""

    def __init__(self, base_url: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            # plan can run several minutes, run can take ~1 min; read budget
            # must cover the worst case or the tool errors mid-query.
            timeout=httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0),
            follow_redirects=False,
            limits=httpx.Limits(max_connections=32, max_keepalive_connections=8),
        )

    async def _post(self, path: str, token: str, body: dict) -> dict:
        try:
            resp = await self._client.post(
                path,
                json=body,
                headers={"Authorization": f"Bearer {token}"},
            )
        except httpx.HTTPError as e:
            # Drop the exception chain — the original request carries the bearer.
            raise AgentApiError(0, f"network: {type(e).__name__}") from None
        if resp.status_code >= 400:
            # Cap body to avoid unbounded propagation into MCP error responses.
            safe_body = (resp.text or "")[:256]
            raise AgentApiError(resp.status_code, safe_body)
        return resp.json()

    async def plan(self, token: str, request: PlanRequest) -> PlanResponse:
        data = await self._post("/plan", token, request.model_dump(exclude_none=True))
        return PlanResponse.model_validate(data)

    async def run(self, token: str, request: RunRequest) -> RunResponse:
        data = await self._post("/run", token, request.model_dump())
        return RunResponse.model_validate(data)

    async def close(self) -> None:
        await self._client.aclose()
