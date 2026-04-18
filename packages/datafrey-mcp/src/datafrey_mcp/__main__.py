"""Entry point: python -m datafrey_mcp / datafrey-mcp CLI."""

from __future__ import annotations

import argparse

from datafrey_mcp.observability import init_sentry

init_sentry()

from datafrey_mcp.config import MCP_HOST, MCP_PORT
from datafrey_mcp.server import create_server


def main() -> None:
    parser = argparse.ArgumentParser(description="datafrey MCP server")
    parser.add_argument("--port", type=int, default=MCP_PORT, help="Server port")
    parser.add_argument("--host", default=MCP_HOST, help="Bind address")
    args = parser.parse_args()

    mcp = create_server(host=args.host, port=args.port)
    mcp.run(
        transport="streamable-http",
        host=args.host,
        port=args.port,
        stateless_http=True,
    )


if __name__ == "__main__":
    main()
