"""Entry point: python -m datafrey_mcp / datafrey-mcp CLI."""

from __future__ import annotations

import argparse
import sys

from datafrey_mcp.config import MCP_BASE_URL, MCP_HOST, MCP_PORT
from datafrey_mcp.server import create_server

# Hosts that never leave the local machine — safe to run without TLS.
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})


def _tls_preflight(host: str, base_url: str) -> None:
    """Warn when the server is reachable off-box without advertised TLS.

    Bearer tokens transit the streamable-HTTP transport in plaintext. If the
    bind address is public and the deployer hasn't declared an https base URL
    (so an ingress would rewrite to it), every request can be wiretapped.
    We can't confirm the ingress does TLS — only that the operator said so.
    """
    if host in _LOOPBACK_HOSTS:
        return
    if base_url.startswith("https://"):
        return
    print(
        "\n"
        "⚠  SECURITY: MCP bound to "
        f"{host!r} without an https DATAFREY_MCP_BASE_URL.\n"
        "   Bearer tokens will be sent in plaintext unless an ingress in front\n"
        "   of this process terminates TLS. Set DATAFREY_MCP_BASE_URL=https://…\n"
        "   to acknowledge, or bind to 127.0.0.1 for local-only use.\n",
        file=sys.stderr,
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="datafrey MCP server")
    parser.add_argument("--port", type=int, default=MCP_PORT, help="Server port")
    parser.add_argument("--host", default=MCP_HOST, help="Bind address")
    args = parser.parse_args()

    _tls_preflight(args.host, MCP_BASE_URL)

    mcp = create_server(host=args.host, port=args.port)
    mcp.run(
        transport="streamable-http",
        host=args.host,
        port=args.port,
        stateless_http=True,
    )


if __name__ == "__main__":
    main()
