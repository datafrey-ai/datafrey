from enum import Enum

from pydantic import BaseModel, ConfigDict


class ErrorCode(str, Enum):
    not_found = "not_found"
    unauthorized = "unauthorized"
    validation_error = "validation_error"
    rate_limited = "rate_limited"
    internal_error = "internal_error"
    plan_failed = "plan_failed"
    run_failed = "run_failed"


class ApiError(BaseModel):
    model_config = ConfigDict(frozen=True)

    error: str  # raw string, not ErrorCode — forward-compatible with unknown codes
    message: str
    status_code: int
