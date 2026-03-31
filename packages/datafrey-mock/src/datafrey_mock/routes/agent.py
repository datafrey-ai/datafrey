"""POST /plan and /run — stub Agent API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from datafrey_api import PlanRequest, PlanResponse, RunRequest, RunResponse

from datafrey_mock.auth import MockUser, get_current_user

router = APIRouter()


@router.post("/plan")
def plan(
    body: PlanRequest,
    user: MockUser = Depends(get_current_user),
) -> dict:
    response = PlanResponse(
        plan=(
            f"Query plan for: {body.prompt}\n"
            "1. Connect to your database\n"
            "2. SELECT * FROM sample_table LIMIT 10"
        ),
    )
    return response.model_dump(mode="json")


@router.post("/run")
def run(
    body: RunRequest,
    user: MockUser = Depends(get_current_user),
) -> dict:
    response = RunResponse(
        output=(
            "| id | name       | value |\n"
            "|----|------------|-------|\n"
            "| 1  | Alice      | 100   |\n"
            "| 2  | Bob        | 200   |\n"
            "| 3  | Charlie    | 300   |\n"
            "\n3 rows returned"
        ),
    )
    return response.model_dump(mode="json")
