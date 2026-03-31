"""POST /auth/token — mock token endpoint (part of manage router)."""

from __future__ import annotations

from datetime import datetime, timezone

import jwt
from fastapi import APIRouter

router = APIRouter()

# Symmetric key for mock JWTs — not a real secret
_MOCK_JWT_SECRET = "mock-secret-key"


@router.post("/auth/token")
def create_mock_token() -> dict:
    """Generate a dummy JWT. No auth required."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "mock-user-id",
        "email": "user@example.com",
        "name": "Mock User",
        "iat": now,
        "exp": datetime(2099, 12, 31, tzinfo=timezone.utc),
    }
    token = jwt.encode(payload, _MOCK_JWT_SECRET, algorithm="HS256")
    return {"token": token}
