"""Auth dependency: accept any Bearer token.

DEVELOPMENT ONLY. The mock server accepts any Bearer token as valid so the
CLI can be exercised without a live WorkOS environment. This module must
never run in a context reachable from the public internet.
"""

from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import Header, HTTPException


@dataclass(frozen=True)
class MockUser:
    sub: str
    email: str
    name: str


def get_current_user(authorization: str | None = Header(default=None)) -> MockUser:
    """Extract user from Bearer token. Any value accepted.

    Valid JWT → extract sub/email/name claims.
    Invalid JWT → stub user.
    Missing header → 401.
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "unauthorized",
                "message": "Missing Authorization header.",
                "status_code": 401,
            },
        )

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(
            status_code=401,
            detail={
                "error": "unauthorized",
                "message": "Invalid Authorization header format.",
                "status_code": 401,
            },
        )

    token = parts[1]

    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return MockUser(
            sub=payload.get("sub", "mock-user-id"),
            email=payload.get("email", "user@example.com"),
            name=payload.get("name", "Mock User"),
        )
    except jwt.DecodeError:
        return MockUser(sub="mock-user-id", email="user@example.com", name="Mock User")
