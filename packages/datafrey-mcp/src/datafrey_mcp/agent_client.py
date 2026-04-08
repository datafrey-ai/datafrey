"""Async HTTP client for the datafrey Agent API."""

from __future__ import annotations
import httpx
from datafrey_api import PlanRequest, PlanResponse, RunRequest, RunResponse


class AgentApiClient:
    """Forwards MCP tool calls to /agent/v1/ endpoints."""

    def __init__(self, base_url: str) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=120.0)

    async def _post(self, path: str, token: str, body: dict) -> dict:
        resp = await self._client.post(
            path,
            json=body,
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()

    async def plan(self, token: str, request: PlanRequest) -> PlanResponse:
        data = await self._post("/plan", token, request.model_dump(exclude_none=True))
        return PlanResponse.model_validate(data)

    async def run(self, token: str, request: RunRequest) -> RunResponse:
        data = await self._post("/run", token, request.model_dump())
        return RunResponse.model_validate(data)

    async def close(self) -> None:
        await self._client.aclose()
