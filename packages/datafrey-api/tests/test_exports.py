"""Verify the public surface matches the spec."""

import datafrey_api

EXPECTED_SYMBOLS = {
    "Provider",
    "DatabaseStatus",
    "DatabaseRecord",
    "DatabaseCreated",
    "DatabaseCreate",
    "EncryptedCredentials",
    "PublicKeyResponse",
    "SnowflakeCredentials",
    "SnowflakeKeyPairCredentials",
    "SnowflakePATCredentials",
    "UserInfo",
    "StatusResponse",
    "PlanRequest",
    "PlanResponse",
    "RunRequest",
    "RunResponse",
    "ErrorCode",
    "ApiError",
    "validate_credentials",
}


def test_all_exports_present():
    assert set(datafrey_api.__all__) == EXPECTED_SYMBOLS


def test_star_import_resolves():
    for name in EXPECTED_SYMBOLS:
        assert hasattr(datafrey_api, name), f"{name} not importable from datafrey_api"


def test_subpackage_imports():
    from datafrey_api.manage import DatabaseRecord
    from datafrey_api.agent import PlanRequest

    assert DatabaseRecord is datafrey_api.DatabaseRecord
    assert PlanRequest is datafrey_api.PlanRequest
