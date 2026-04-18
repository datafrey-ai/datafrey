"""POST /auth/token — mock token endpoint (part of manage router)."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter

router = APIRouter()

# Per-process random symmetric key. Regenerated on every start so a token
# issued by one mock instance can never be replayed against another, even
# if the OSS source is public.
_MOCK_JWT_SECRET = secrets.token_urlsafe(32)


@router.post("/auth/token")
def create_mock_token() -> dict:
    """Generate a dummy JWT. No auth required."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "mock-user-id",
        "email": "user@example.com",
        "name": "Mock User",
        "iat": now,
        # Short-lived: mock is a dev tool, not a long-running session.
        "exp": now + timedelta(hours=24),
    }
    token = jwt.encode(payload, _MOCK_JWT_SECRET, algorithm="HS256")
    return {"token": token}
