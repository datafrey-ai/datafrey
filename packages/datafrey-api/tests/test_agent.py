import pytest
from pydantic import ValidationError

from datafrey_api import PlanRequest, PlanResponse, RunRequest, RunResponse


class TestPlanRequest:
    def test_valid(self):
        req = PlanRequest(prompt="Show all tables")
        assert req.prompt == "Show all tables"

    def test_empty_prompt_rejected(self):
        with pytest.raises(ValidationError):
            PlanRequest(prompt="")

    def test_prompt_too_long_rejected(self):
        with pytest.raises(ValidationError):
            PlanRequest(prompt="x" * 4097)

    def test_mutable(self):
        req = PlanRequest(prompt="original")
        req.prompt = "updated"
        assert req.prompt == "updated"


class TestPlanResponse:
    def test_valid(self):
        resp = PlanResponse(plan="SELECT * FROM ...")
        assert resp.plan == "SELECT * FROM ..."

    def test_frozen(self):
        resp = PlanResponse(plan="plan")
        with pytest.raises(ValidationError):
            resp.plan = "other"


class TestRunRequest:
    def test_valid(self):
        req = RunRequest(code="SELECT 1")
        assert req.code == "SELECT 1"

    def test_empty_code_rejected(self):
        with pytest.raises(ValidationError):
            RunRequest(code="")

    def test_code_too_long_rejected(self):
        with pytest.raises(ValidationError):
            RunRequest(code="x" * 16385)

    def test_mutable(self):
        req = RunRequest(code="SELECT 1")
        req.code = "SELECT 2"
        assert req.code == "SELECT 2"


class TestRunResponse:
    def test_valid(self):
        resp = RunResponse(output="1 row returned")
        assert resp.output == "1 row returned"

    def test_frozen(self):
        resp = RunResponse(output="ok")
        with pytest.raises(ValidationError):
            resp.output = "other"
