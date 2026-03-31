"""FastMCP server with plan/run tools bridging to the datafrey Agent API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastmcp import Context, FastMCP
from fastmcp.server.auth.providers.workos import AuthKitProvider
from fastmcp.server.dependencies import get_access_token
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from datafrey_api import PlanRequest, PlanResponse, RunRequest, RunResponse

from datafrey_mcp.agent_client import AgentApiClient
from datafrey_mcp.config import (
    AGENT_API_URL,
    MCP_BASE_URL,
    WORKOS_AUTHKIT_DOMAIN,
    WORKOS_CLIENT_ID,
)


def create_server(
    *, host: str = "0.0.0.0", port: int = 8080
) -> FastMCP:
    """Create the FastMCP server with auth and tools configured."""

    base_url = MCP_BASE_URL or f"http://localhost:{port}"
    auth = AuthKitProvider(
        authkit_domain=f"https://{WORKOS_AUTHKIT_DOMAIN}",
        base_url=base_url,
        client_id=WORKOS_CLIENT_ID,
    )

    agent_client: AgentApiClient | None = None

    @asynccontextmanager
    async def lifespan(server: FastMCP) -> AsyncIterator[dict]:
        nonlocal agent_client
        agent_client = AgentApiClient(AGENT_API_URL)
        try:
            yield {"agent_client": agent_client}
        finally:
            await agent_client.close()

    mcp = FastMCP(
        name="datafrey",
        instructions=(
            "Datafrey — query your connected databases using natural language. "
            "Use 'plan' to generate a query plan, then 'run' to execute it."
        ),
        auth=auth,
        lifespan=lifespan,
    )

    @mcp.custom_route("/health", methods=["GET"])
    async def health(request: Request) -> PlainTextResponse:
        return PlainTextResponse("ok")

    @mcp.tool()
    async def plan(
        prompt: str,
        ctx: Context = None,
    ) -> str:
        """Generate a query plan for a database question.

        Args:
            prompt: Natural language question about your data (e.g. "show me top 10 customers by revenue")
        """
        access_token = get_access_token()
        request = PlanRequest(prompt=prompt)
        response = await agent_client.plan(access_token.token, request)
        return response.plan

    @mcp.tool()
    async def run(
        code: str,
        ctx: Context = None,
    ) -> str:
        """Execute a query against your connected database.

        Args:
            code: SQL or code to execute (from a query plan)
        """
        access_token = get_access_token()
        request = RunRequest(code=code)
        response = await agent_client.run(access_token.token, request)
        return response.output

    return mcp
