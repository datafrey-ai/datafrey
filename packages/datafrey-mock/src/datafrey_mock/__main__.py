"""Entry point: python -m datafrey_mock / datafrey-mock CLI."""

from __future__ import annotations

import argparse

import uvicorn

from datafrey_mock.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="datafrey mock API server")
    parser.add_argument("--port", type=int, default=12767, help="Server port")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address")
    parser.add_argument(
        "--seed",
        default="default",
        choices=["default", "empty"],
        help="Seed data mode",
    )
    args = parser.parse_args()

    app = create_app(seed=args.seed)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
