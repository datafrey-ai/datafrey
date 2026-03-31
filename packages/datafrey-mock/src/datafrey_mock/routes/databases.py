"""GET/POST/DELETE /databases endpoints."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from datafrey_api import (
    DatabaseCreate,
    DatabaseCreated,
    DatabaseRecord,
    DatabaseStatus,
    Provider,
    PublicKeyResponse,
)

from datafrey_mock.auth import MockUser, get_current_user
from datafrey_mock.state import MockState

router = APIRouter()

# Dummy RSA public key for the mock (not a real secret)
_MOCK_PUBLIC_KEY = """\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAncnkywtVkoGXu+XqFcF7
0ah1UuZeUtphzBnsH4Azh9eq6hshL78lse7D3yd6DaNHnCj/iiltTwPsw0Q0tC8n
5g4ecSKuFNOmCT6VAxH2+V09rL13CiLO/Pe9M/IVbXdOCgBeUtsyXl6hrmdQBEKY
J2CydI7IQ4IqO+GPV7S/7ayyqb4oDKpMG6LHtJkwDlGwDGUT7RFyOZKEx0oMhfgs
PkmTaFRjl91eVlb9kA86ufQEbsE6UpV7j9A+sWfkeLgPf9lirKtLs0VBClqXKs/y
J338ET/8zynh7Tv49gsK/yk58S9T6OGIT+a8Rm6m+ZnamfJPOo9LgI2dGrwBe6A2
mwIDAQAB
-----END PUBLIC KEY-----"""

_MOCK_FINGERPRINT = "SHA256:+qJQxWm8kEOVwYlaiW9uryFhqQRk6z1giKCjph3pOv0"


def _make_host(provider: Provider, db_id: str) -> str:
    if provider == Provider.snowflake:
        return f"{db_id}.us-east-1.snowflakecomputing.com"
    return f"{db_id}.db.example.com"


def _get_state(request: Request) -> MockState:
    return request.app.state.mock_state


@router.get("/databases")
def list_databases(
    user: MockUser = Depends(get_current_user),
    state: MockState = Depends(_get_state),
) -> dict:
    state.resolve_pending(user.sub)
    dbs = state.databases_for(user.sub)
    return {"databases": [r.model_dump(mode="json") for r in dbs.values()]}


@router.post("/databases", status_code=201)
def create_database(
    body: DatabaseCreate,
    user: MockUser = Depends(get_current_user),
    state: MockState = Depends(_get_state),
) -> dict:
    dbs = state.databases_for(user.sub)
    if len(dbs) >= 1:
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "message": "Database limit reached. You can only connect 1 database. Remove it first with `datafrey db drop`.",
                "status_code": 422,
            },
        )
    db_id = f"db_{body.provider.value}_{secrets.token_hex(6)}"
    now = datetime.now(timezone.utc)
    host = _make_host(body.provider, db_id)

    record = DatabaseRecord(
        id=db_id,
        provider=body.provider,
        name=body.name,
        host=host,
        status=DatabaseStatus.loading,
        created_at=now,
    )
    state.databases_for(user.sub)[db_id] = record
    state.mark_pending(db_id)

    created = DatabaseCreated(
        id=db_id,
        provider=body.provider,
        name=body.name,
        host=host,
        status=DatabaseStatus.loading,
        created_at=now,
    )
    return created.model_dump(mode="json")


@router.get("/databases/public-key")
def get_public_key(
    user: MockUser = Depends(get_current_user),
) -> dict:
    resp = PublicKeyResponse(
        public_key=_MOCK_PUBLIC_KEY,
        fingerprint=_MOCK_FINGERPRINT,
        algorithm="RSA-OAEP-SHA256",
    )
    return resp.model_dump(mode="json")


@router.delete("/databases/{database_id}", status_code=204)
def delete_database(
    database_id: str,
    user: MockUser = Depends(get_current_user),
    state: MockState = Depends(_get_state),
) -> None:
    dbs = state.databases_for(user.sub)
    if database_id not in dbs:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "not_found",
                "message": f"Database {database_id} not found.",
                "status_code": 404,
            },
        )
    del dbs[database_id]
