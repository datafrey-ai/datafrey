"""FastAPI app with lifespan, router mounting, and admin endpoints."""

from __future__ import annotations

from fastapi import APIRouter, FastAPI

from datafrey_mock.routes import agent, auth, databases, status
from datafrey_mock.state import MockState


def create_app(seed: str = "default") -> FastAPI:
    mock_state = MockState(seed=seed)

    app = FastAPI(title="datafrey-mock")
    app.state.mock_state = mock_state

    # Management API under /manage/v1/
    manage_router = APIRouter()
    manage_router.include_router(databases.router)
    manage_router.include_router(status.router)
    manage_router.include_router(auth.router)
    app.include_router(manage_router, prefix="/manage/v1")

    # Agent API under /agent/v1/
    agent_router = APIRouter()
    agent_router.include_router(agent.router)
    app.include_router(agent_router, prefix="/agent/v1")

    # Admin endpoints under /mock/
    @app.post("/mock/reset")
    def reset_state() -> dict:
        app.state.mock_state.reset()
        return {"status": "reset"}

    @app.post("/mock/token")
    def mock_token() -> dict:
        return auth.create_mock_token()

    @app.get("/mock/health")
    def health() -> dict:
        return {"status": "ok"}

    return app
