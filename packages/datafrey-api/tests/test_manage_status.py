import pytest
from pydantic import ValidationError

from datafrey_api import StatusResponse, UserInfo


class TestUserInfo:
    def test_valid(self):
        user = UserInfo(email="alice@example.com", name="Alice")
        assert user.email == "alice@example.com"

    def test_frozen(self):
        user = UserInfo(email="alice@example.com", name="Alice")
        with pytest.raises(ValidationError):
            user.name = "Bob"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            UserInfo(email="not-an-email", name="Alice")


class TestStatusResponse:
    def test_valid(self):
        resp = StatusResponse(
            user=UserInfo(email="a@b.com", name="A"),
            databases_count=3,
            mcp_enabled=True,
        )
        assert resp.databases_count == 3
        assert resp.mcp_enabled is True

    def test_frozen(self):
        resp = StatusResponse(
            user=UserInfo(email="a@b.com", name="A"),
            databases_count=0,
            mcp_enabled=False,
        )
        with pytest.raises(ValidationError):
            resp.databases_count = 5

    def test_negative_count_rejected(self):
        with pytest.raises(ValidationError):
            StatusResponse(
                user=UserInfo(email="a@b.com", name="A"),
                databases_count=-1,
                mcp_enabled=False,
            )

    def test_from_json(self):
        data = {
            "user": {"email": "x@y.com", "name": "X"},
            "databases_count": 0,
            "mcp_enabled": False,
        }
        resp = StatusResponse.model_validate(data)
        assert resp.user.email == "x@y.com"
