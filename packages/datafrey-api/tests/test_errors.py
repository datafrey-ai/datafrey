import pytest
from pydantic import ValidationError

from datafrey_api import ApiError, ErrorCode


class TestErrorCode:
    def test_all_codes(self):
        expected = {
            "not_found",
            "unauthorized",
            "validation_error",
            "rate_limited",
            "internal_error",
            "plan_failed",
            "run_failed",
        }
        assert {e.value for e in ErrorCode} == expected


class TestApiError:
    def test_valid(self):
        err = ApiError(error="not_found", message="DB not found", status_code=404)
        assert err.error == "not_found"
        assert err.message == "DB not found"
        assert err.status_code == 404

    def test_frozen(self):
        err = ApiError(error="unauthorized", message="bad token", status_code=401)
        with pytest.raises(ValidationError):
            err.error = "other"

    def test_unknown_error_code_accepted(self):
        """error is str, not ErrorCode — forward-compatible."""
        err = ApiError(error="some_future_code", message="new error", status_code=500)
        assert err.error == "some_future_code"

    def test_from_json(self):
        data = {"error": "rate_limited", "message": "slow down", "status_code": 429}
        err = ApiError.model_validate(data)
        assert err.status_code == 429
