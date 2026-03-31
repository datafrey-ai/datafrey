"""GET /status endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from datafrey_api import StatusResponse, UserInfo

from datafrey_mock.auth import MockUser, get_current_user
from datafrey_mock.state import MockState

router = APIRouter()


def _get_state(request: Request) -> MockState:
    return request.app.state.mock_state


@router.get("/status")
def get_status(
    user: MockUser = Depends(get_current_user),
    state: MockState = Depends(_get_state),
) -> dict:
    dbs = state.databases_for(user.sub)
    resp = StatusResponse(
        user=UserInfo(email=user.email, name=user.name),
        databases_count=len(dbs),
        mcp_enabled=True,
    )
    return resp.model_dump(mode="json")
