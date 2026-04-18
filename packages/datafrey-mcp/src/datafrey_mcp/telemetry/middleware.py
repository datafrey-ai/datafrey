"""FastMCP middleware that emits PostHog telemetry for sessions + tool calls.

Captures only metadata: tool name, duration, outcome, MCP client name, user
agent. Never tool arguments, prompt content, SQL, or response payloads.
"""

from __future__ import annotations

import time
from typing import Any

from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext

from datafrey_mcp.telemetry.client import track
from datafrey_mcp.telemetry.events import (
    MCP_SESSION_STARTED,
    MCP_TOOL_COMPLETED,
    MCP_TOOL_INVOKED,
)
from datafrey_mcp.telemetry.identity import get_distinct_id


def _http_props() -> dict[str, Any]:
    """Best-effort User-Agent capture, truncated. Empty dict outside HTTP."""
    try:
        from fastmcp.server.dependencies import get_http_headers

        headers = get_http_headers()
        ua = (headers.get("user-agent") or "").strip()[:200]
        return {"user_agent": ua} if ua else {}
    except Exception:
        return {}


def _extract_client_info(context: MiddlewareContext) -> tuple[str | None, str | None]:
    """Pull (name, version) from the initialize message's clientInfo block."""
    try:
        params = getattr(context.message, "params", None)
        if params is None:
            return None, None
        if isinstance(params, dict):
            client_info = params.get("clientInfo") or {}
        else:
            client_info = getattr(params, "clientInfo", None) or {}
        if isinstance(client_info, dict):
            name = client_info.get("name")
            version = client_info.get("version")
        else:
            name = getattr(client_info, "name", None)
            version = getattr(client_info, "version", None)
        name = (name or "").strip()[:100] or None
        version = (version or "").strip()[:50] or None
        return name, version
    except Exception:
        return None, None


class TelemetryMiddleware(Middleware):
    """Emits session/tool events. Never raises into the request flow."""

    async def on_initialize(
        self, context: MiddlewareContext, call_next: CallNext
    ) -> Any:
        result = await call_next(context)
        try:
            distinct_id = get_distinct_id()
            if not distinct_id:
                return result
            name, version = _extract_client_info(context)
            track(
                MCP_SESSION_STARTED,
                distinct_id=distinct_id,
                mcp_client_name=name,
                mcp_client_version=version,
                **_http_props(),
            )
        except Exception:
            pass
        return result

    async def on_call_tool(
        self, context: MiddlewareContext, call_next: CallNext
    ) -> Any:
        raw_tool = getattr(context.message, "name", None)
        tool = (raw_tool or "").strip()[:100] if isinstance(raw_tool, str) else None
        distinct_id = get_distinct_id()
        http_props = _http_props()

        if distinct_id and tool:
            try:
                track(
                    MCP_TOOL_INVOKED,
                    distinct_id=distinct_id,
                    tool=tool,
                    **http_props,
                )
            except Exception:
                pass

        start = time.monotonic()
        outcome = "ok"
        error_class: str | None = None
        try:
            return await call_next(context)
        except BaseException as e:
            outcome = "error"
            error_class = type(e).__name__[:100]
            raise
        finally:
            if distinct_id and tool:
                try:
                    track(
                        MCP_TOOL_COMPLETED,
                        distinct_id=distinct_id,
                        tool=tool,
                        duration_ms=int((time.monotonic() - start) * 1000),
                        outcome=outcome,
                        error_class=error_class,
                        **http_props,
                    )
                except Exception:
                    pass
