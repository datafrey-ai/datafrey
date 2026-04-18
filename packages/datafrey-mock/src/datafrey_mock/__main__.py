"""Entry point: python -m datafrey_mock / datafrey-mock CLI."""

from __future__ import annotations

import argparse
import ipaddress
import sys

import uvicorn

from datafrey_mock.app import create_app


def _is_loopback(host: str) -> bool:
    if host in ("localhost",):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="datafrey mock API server")
    parser.add_argument("--port", type=int, default=12767, help="Server port")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (loopback only)")
    parser.add_argument(
        "--seed",
        default="default",
        choices=["default", "empty"],
        help="Seed data mode",
    )
    args = parser.parse_args()

    if not _is_loopback(args.host):
        sys.stderr.write(
            f"error: datafrey-mock refuses non-loopback bind ({args.host!r}). "
            "It accepts any Bearer token and must never be reachable from the "
            "public internet.\n"
        )
        sys.exit(2)

    app = create_app(seed=args.seed)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
